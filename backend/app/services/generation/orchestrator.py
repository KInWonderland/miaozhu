import asyncio
import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.application import Application
from app.models.generation import GenerationTask, GenerationSection
from app.services.llm.base import BaseLLMProvider
from app.services.prompts.base import PromptBuilder
from app.services.generation.sections import SECTION_MAP

logger = logging.getLogger(__name__)

# 申请表中可自动填充的字段
AUTOFILL_FIELDS = [
    "software_version", "software_category", "completion_date",
    "development_method", "code_line_count", "dev_hardware",
    "dev_os", "dev_tools", "runtime_platform", "runtime_hardware",
    "runtime_software", "development_language", "development_purpose",
    "target_industry", "technical_features", "work_type",
    "rights_acquisition", "rights_scope", "publish_status",
]


def _clean_content(content: str) -> str:
    """清理 LLM 输出中的前缀寒暄和后缀说明文字"""
    if not content:
        return content

    lines = content.split("\n")

    # ── 去除开头的寒暄/角色说明 ──
    # 匹配常见 AI 开头模式，直到第一个 markdown 标题或正文
    preamble_patterns = [
        re.compile(r"^(好的|当然|没问题|嗯|以下|下面)[，,].*"),
        re.compile(r"^作为.*专家.*"),
        re.compile(r"^我将(根据|为您|按照).*"),
        re.compile(r"^根据您(提供|的).*我.*"),
        re.compile(r"^(非常感谢|感谢).*"),
    ]
    while lines:
        stripped = lines[0].strip()
        if not stripped:
            lines.pop(0)
            continue
        if any(p.match(stripped) for p in preamble_patterns):
            lines.pop(0)
            continue
        break

    # ── 去除结尾的总结性说明 ──
    postscript_patterns = [
        re.compile(r"^\*{0,2}[（(（].*章节(结束|完毕|完成).*[)）]\*{0,2}$"),
        re.compile(r"^\*{0,2}撰写说明[：:]?\*{0,2}"),
        re.compile(r"^(本章节|本文档|以上内容)(已严格|已按照|已根据|已完整).*"),
        re.compile(r"^(如需|如有|如果需要|希望以上|如您还需).*"),
        re.compile(r"^-{3,}$"),
    ]
    while lines:
        stripped = lines[-1].strip()
        if not stripped:
            lines.pop()
            continue
        if any(p.match(stripped) for p in postscript_patterns):
            lines.pop()
            continue
        break

    return "\n".join(lines).strip()


class GenerationOrchestrator:
    """生成流程编排"""

    def __init__(self, llm: BaseLLMProvider, prompt_builder: PromptBuilder):
        self.llm = llm
        self.prompt_builder = prompt_builder

    # ── 全量生成 ───────────────────────────────────────────

    async def run_full(
        self,
        task_id: int,
        llm_semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        """后台任务：并发生成所有 section（受 semaphore 限流）"""

        # 1. 加载任务和应用数据
        async with async_session() as db:
            task = await db.get(GenerationTask, task_id)
            if not task:
                logger.error("Task %d not found", task_id)
                return

            # 调度器已经将 status 设为 running，这里只需确认
            if task.status != "running":
                task.status = "running"
                task.updated_at = datetime.now(timezone.utc)
                await db.commit()

            app = await db.get(Application, task.application_id)
            if not app:
                task.status = "failed"
                task.error_message = "Application not found"
                task.updated_at = datetime.now(timezone.utc)
                await db.commit()
                return

            result = await db.execute(
                select(GenerationSection)
                .where(GenerationSection.task_id == task_id)
                .order_by(GenerationSection.section_order)
            )
            sections = list(result.scalars().all())

            app_id = app.id
            extra_prompt = task.extra_prompt

        # 2. 并发处理所有 section（每个 section 独立 DB session）
        sem = llm_semaphore or asyncio.Semaphore(3)

        await asyncio.gather(
            *[
                self._generate_section(
                    section_id=s.id,
                    section_key=s.section_key,
                    app_id=app_id,
                    extra_prompt=extra_prompt,
                    semaphore=sem,
                )
                for s in sections
            ],
            return_exceptions=True,
        )

        # 3. 汇总结果并更新任务状态
        async with async_session() as db:
            task = await db.get(GenerationTask, task_id)
            result = await db.execute(
                select(GenerationSection)
                .where(GenerationSection.task_id == task_id)
            )
            sections = list(result.scalars().all())

            # 清理卡在 pending/running 的 section（gather 已结束说明这些 section 异常中断了）
            now = datetime.now(timezone.utc)
            for s in sections:
                if s.status in ("pending", "running"):
                    s.status = "failed"
                    s.error_message = s.error_message or "生成超时或异常中断"
                    s.updated_at = now

            completed = sum(1 for s in sections if s.status == "completed")
            failed = sum(1 for s in sections if s.status == "failed")

            task.completed_sections = completed
            task.total_prompt_tokens = sum(s.prompt_tokens or 0 for s in sections)
            task.total_completion_tokens = sum(s.completion_tokens or 0 for s in sections)
            task.total_tokens = sum(s.total_tokens or 0 for s in sections)

            # 处理 form_autofill
            autofill = next(
                (s for s in sections if s.section_key == "form_autofill" and s.status == "completed"),
                None,
            )
            if autofill and autofill.content:
                app = await db.get(Application, app_id)
                if app:
                    await self._apply_autofill(db, app, autofill.content)

            if failed == len(sections):
                task.status = "failed"
                task.error_message = "所有章节生成失败"
            elif failed > 0:
                task.status = "completed"
                task.error_message = f"{failed} 个章节生成失败"
            else:
                task.status = "completed"

            task.updated_at = datetime.now(timezone.utc)

            # 更新 Application 状态
            app = await db.get(Application, app_id)
            if app:
                if task.status == "completed":
                    # 生成成功，状态转换为 generated（等待用户审核）
                    app.status = "generated"
                elif task.status == "failed":
                    # 生成失败，回退到 draft
                    app.status = "draft"

            await db.commit()
            logger.info(
                "Task %d finished, status=%s, total_tokens=%d, app_status=%s",
                task_id, task.status, task.total_tokens, app.status if app else None,
            )

    async def _generate_section(
        self,
        section_id: int,
        section_key: str,
        app_id: int,
        extra_prompt: str | None,
        semaphore: asyncio.Semaphore,
    ) -> None:
        """生成单个 section（独立 DB session + semaphore 限流）"""
        async with async_session() as db:
            section = await db.get(GenerationSection, section_id)
            app = await db.get(Application, app_id)

            section.status = "running"
            section.updated_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                section_def = SECTION_MAP.get(section_key)
                if not section_def:
                    raise ValueError(f"Unknown section: {section_key}")

                system_prompt, user_prompt = self.prompt_builder.build(
                    app, section_key, extra_prompt
                )

                # 在 semaphore 保护下调用 LLM
                async with semaphore:
                    chat_result = await self.llm.chat(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=section_def.max_tokens,
                    )

                # 清理 AI 生成的前缀/后缀杂文（跳过 form_autofill 和源代码）
                cleaned = chat_result.content
                if section_key not in ("form_autofill", "source_code_front", "source_code_back"):
                    cleaned = _clean_content(cleaned)
                section.content = cleaned
                section.status = "completed"
                section.prompt_tokens = chat_result.prompt_tokens
                section.completion_tokens = chat_result.completion_tokens
                section.total_tokens = chat_result.total_tokens
                section.updated_at = datetime.now(timezone.utc)

                # 实时更新任务的完成章节数（用于SSE进度推送）
                task = await db.get(GenerationTask, section.task_id)
                if task:
                    from sqlalchemy import func
                    result = await db.execute(
                        select(func.count(GenerationSection.id))
                        .where(
                            GenerationSection.task_id == section.task_id,
                            GenerationSection.status == "completed",
                        )
                    )
                    completed_count = result.scalar()
                    task.completed_sections = completed_count
                    task.updated_at = datetime.now(timezone.utc)

                await db.commit()

                logger.info(
                    "Section '%s' completed, tokens=%d, task progress: %d sections",
                    section_key, chat_result.total_tokens, task.completed_sections if task else 0,
                )

            except Exception as e:
                logger.exception("Failed to generate section '%s'", section_key)
                section.status = "failed"
                section.error_message = str(e)
                section.updated_at = datetime.now(timezone.utc)

                # 失败时也更新任务的 updated_at，触发SSE推送
                task = await db.get(GenerationTask, section.task_id)
                if task:
                    task.updated_at = datetime.now(timezone.utc)

                await db.commit()

    # ── 单 section 重新生成 ────────────────────────────────

    async def run_single(
        self,
        section_id: int,
        llm_semaphore: asyncio.Semaphore | None = None,
    ) -> None:
        """重新生成单个 section（extra_prompt 从 section 模型读取）"""
        sem = llm_semaphore or asyncio.Semaphore(3)

        async with async_session() as db:
            section = await db.get(GenerationSection, section_id)
            if not section:
                logger.error("Section %d not found", section_id)
                return

            task = await db.get(GenerationTask, section.task_id)
            if not task:
                logger.error("Task %d not found", section.task_id)
                return

            app = await db.get(Application, task.application_id)
            if not app:
                logger.error("Application %d not found", task.application_id)
                return

            # 扣除旧的 token 用量
            old_prompt_tokens = section.prompt_tokens
            old_completion_tokens = section.completion_tokens
            old_total_tokens = section.total_tokens

            # 调度器已将 section status 设为 running
            if section.status != "running":
                section.status = "running"
                section.error_message = None
                section.updated_at = datetime.now(timezone.utc)
                await db.commit()

            try:
                section_def = SECTION_MAP.get(section.section_key)
                if not section_def:
                    raise ValueError(f"Unknown section: {section.section_key}")

                extra = section.extra_prompt
                if task.extra_prompt and extra:
                    combined_prompt = f"{task.extra_prompt}\n\n{extra}"
                elif task.extra_prompt:
                    combined_prompt = task.extra_prompt
                else:
                    combined_prompt = extra

                system_prompt, user_prompt = self.prompt_builder.build(
                    app, section.section_key, combined_prompt
                )

                async with sem:
                    chat_result = await self.llm.chat(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=section_def.max_tokens,
                    )

                # 清理 AI 生成的前缀/后缀杂文（跳过 form_autofill 和源代码）
                cleaned = chat_result.content
                if section.section_key not in ("form_autofill", "source_code_front", "source_code_back"):
                    cleaned = _clean_content(cleaned)
                section.content = cleaned
                section.status = "completed"
                section.prompt_tokens = chat_result.prompt_tokens
                section.completion_tokens = chat_result.completion_tokens
                section.total_tokens = chat_result.total_tokens
                section.updated_at = datetime.now(timezone.utc)

                # 更新 task 汇总：减去旧的，加上新的
                task.total_prompt_tokens += chat_result.prompt_tokens - old_prompt_tokens
                task.total_completion_tokens += chat_result.completion_tokens - old_completion_tokens
                task.total_tokens += chat_result.total_tokens - old_total_tokens
                task.updated_at = datetime.now(timezone.utc)
                await db.commit()

                if section.section_key == "form_autofill":
                    await self._apply_autofill(db, app, chat_result.content)

            except Exception as e:
                logger.exception("Failed to regenerate section %d", section_id)
                section.status = "failed"
                section.error_message = str(e)
                section.updated_at = datetime.now(timezone.utc)
                await db.commit()

    # ── 自动填充 ──────────────────────────────────────────

    async def _apply_autofill(self, db: AsyncSession, app: Application, content: str) -> None:
        """解析 form_autofill JSON 并回填 Application 空字段"""
        try:
            # 提取 JSON（可能被 markdown 代码块包裹）
            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)

            data = json.loads(text)
            if not isinstance(data, dict):
                return

            for field in AUTOFILL_FIELDS:
                if field in data and data[field]:
                    current = getattr(app, field, None)
                    if not current:
                        setattr(app, field, str(data[field]))

            app.updated_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info("Autofill applied for application %d", app.id)

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse autofill JSON: %s", e)
