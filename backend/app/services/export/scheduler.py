"""
后台导出调度器：轮询 pending 的 ExportTask，生成文档并保存到本地。

架构与 generation scheduler 一致：asyncio 轮询 + 认领。
超过 30 分钟仍在 processing 的任务会被自动取消。
"""

import asyncio
import io
import logging
import zipfile
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.export_task import ExportTask
from app.models.application import Application
from app.models.generation import GenerationTask, GenerationSection
from app.services.document_export import (
    export_application_form_to_txt,
    export_manual_to_word,
    export_manual_to_pdf,
    export_source_code_to_word,
    export_source_code_to_pdf,
)
from app.services.storage import save_file

logger = logging.getLogger(__name__)

TASK_TIMEOUT_MINUTES = 30

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.SCHEDULER_MAX_CONCURRENT_EXPORT)
    return _semaphore


# ── 任务认领 ──

async def _claim_pending() -> int | None:
    async with async_session() as db:
        result = await db.execute(
            select(ExportTask)
            .where(ExportTask.status == "pending")
            .order_by(ExportTask.created_at)
            .limit(1)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None
        task.status = "processing"
        task.started_at = datetime.now(timezone.utc)
        await db.commit()
        return task.id


# ── 启动恢复 ──

async def _recover_interrupted_tasks() -> None:
    """系统启动时恢复被中断的导出任务：将所有 processing 状态的任务重置为 pending。"""
    async with async_session() as db:
        result = await db.execute(
            select(ExportTask).where(ExportTask.status == "processing")
        )
        interrupted = list(result.scalars().all())
        for task in interrupted:
            logger.warning(
                "Recovering interrupted export task %d (was processing, started_at=%s)",
                task.id, task.started_at
            )
            task.status = "pending"
            task.started_at = None

        if interrupted:
            await db.commit()
            logger.info("Recovery complete: reset %d export tasks to pending", len(interrupted))


# ── 超时检查 ──

async def _cancel_stale_tasks(running_tasks: dict[int, asyncio.Task]) -> None:
    """检查并取消处理超过 30 分钟的任务。"""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=TASK_TIMEOUT_MINUTES)
    async with async_session() as db:
        result = await db.execute(
            select(ExportTask)
            .where(
                ExportTask.status == "processing",
                ExportTask.started_at <= cutoff,
            )
        )
        stale = list(result.scalars().all())
        for task in stale:
            logger.warning("Export: task %d timed out (started_at=%s)", task.id, task.started_at)
            task.status = "failed"
            task.error_message = f"导出超时：处理时间超过 {TASK_TIMEOUT_MINUTES} 分钟，已自动取消"
            task.completed_at = datetime.now(timezone.utc)
            # 取消正在执行的 asyncio task
            atask = running_tasks.pop(task.id, None)
            if atask and not atask.done():
                atask.cancel()
                logger.info("Export: cancelled asyncio task for export %d", task.id)
        if stale:
            await db.commit()


# ── 导出逻辑 ──

def _build_file_path(task_id: int, fmt: str) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ext_map = {
        "application-form-txt": "txt",
        "manual-word": "docx",
        "manual-pdf": "pdf",
        "source-code-word": "docx",
        "source-code-pdf": "pdf",
        "all": "zip",
    }
    return f"{date_str}/{task_id}_{fmt}.{ext_map.get(fmt, 'bin')}"


def _build_file_name(software_name: str, fmt: str) -> str:
    name = software_name or "export"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    name_map = {
        "application-form-txt": f"{name}-申请表信息-{ts}.txt",
        "manual-word": f"{name}-文档鉴别材料-{ts}.docx",
        "manual-pdf": f"{name}-文档鉴别材料-{ts}.pdf",
        "source-code-word": f"{name}-源程序鉴别材料-{ts}.docx",
        "source-code-pdf": f"{name}-源程序鉴别材料-{ts}.pdf",
        "all": f"{name}-全部材料-{ts}.zip",
    }
    return name_map.get(fmt, f"{name}-export-{ts}.bin")


_EXPORT_FUNCS = {
    "application-form-txt": export_application_form_to_txt,
    "manual-word": export_manual_to_word,
    "manual-pdf": export_manual_to_pdf,
    "source-code-word": export_source_code_to_word,
    "source-code-pdf": export_source_code_to_pdf,
}


async def _get_export_data(app_id: int):
    """获取 Application + 已完成的 GenerationSection"""
    async with async_session() as db:
        result = await db.execute(
            select(Application).where(Application.id == app_id)
        )
        app = result.scalar_one_or_none()
        if not app:
            raise ValueError("申请不存在")

        result = await db.execute(
            select(GenerationTask)
            .where(GenerationTask.application_id == app_id)
            .order_by(GenerationTask.created_at.desc())
            .limit(1)
        )
        gen_task = result.scalar_one_or_none()
        if not gen_task:
            raise ValueError("尚未生成")

        result = await db.execute(
            select(GenerationSection)
            .where(
                GenerationSection.task_id == gen_task.id,
                GenerationSection.status == "completed",
            )
            .order_by(GenerationSection.section_order)
        )
        sections = list(result.scalars().all())
        if not sections:
            raise ValueError("没有已完成的章节可供导出")
        return app, sections


def _generate_single(fmt: str, app, sections) -> bytes:
    buf: io.BytesIO = _EXPORT_FUNCS[fmt](app, sections)
    return buf.getvalue()


def _generate_all_zip(app, sections) -> bytes:
    import time
    name = app.software_name or "export"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fmt, label, ext in [
            ("application-form-txt", "申请表信息", "txt"),
            ("manual-word", "文档鉴别材料", "docx"),
            ("manual-pdf", "文档鉴别材料", "pdf"),
            ("source-code-word", "源程序鉴别材料", "docx"),
            ("source-code-pdf", "源程序鉴别材料", "pdf"),
        ]:
            logger.info("ZIP: starting generation of %s", fmt)
            t0 = time.monotonic()
            try:
                data = _generate_single(fmt, app, sections)
                elapsed = time.monotonic() - t0
                logger.info("ZIP: generated %s (%.1fs, %d bytes)", fmt, elapsed, len(data))
                zf.writestr(f"{name}-{label}-{ts}.{ext}", data)
            except Exception as e:
                elapsed = time.monotonic() - t0
                logger.error("ZIP: failed to generate %s after %.1fs: %s", fmt, elapsed, str(e))
                raise
    zip_buf.seek(0)
    return zip_buf.getvalue()


async def _process_export(task_id: int, running_tasks: dict[int, asyncio.Task]) -> None:
    sem = _get_semaphore()
    async with sem:
        try:
            logger.info("Export: processing task %d", task_id)

            async with async_session() as db:
                et = await db.get(ExportTask, task_id)
                if not et or et.status != "processing":
                    return
                app_id, fmt = et.application_id, et.format

            app, sections = await _get_export_data(app_id)

            if fmt == "all":
                data = await asyncio.to_thread(_generate_all_zip, app, sections)
            else:
                data = await asyncio.to_thread(_generate_single, fmt, app, sections)

            file_rel_path = _build_file_path(task_id, fmt)
            file_size = await asyncio.to_thread(save_file, file_rel_path, data)
            file_name = _build_file_name(app.software_name or "", fmt)

            async with async_session() as db:
                et = await db.get(ExportTask, task_id)
                if et and et.status == "processing":
                    et.status = "completed"
                    et.file_path = file_rel_path
                    et.file_name = file_name
                    et.file_size = file_size
                    et.completed_at = datetime.now(timezone.utc)
                    await db.commit()

            logger.info("Export: task %d completed (%s)", task_id, file_rel_path)

        except asyncio.CancelledError:
            logger.warning("Export: task %d was cancelled", task_id)
        except Exception as exc:
            logger.exception("Export: task %d failed", task_id)
            try:
                async with async_session() as db:
                    et = await db.get(ExportTask, task_id)
                    if et and et.status == "processing":
                        et.status = "failed"
                        et.error_message = str(exc)[:1000]
                        et.completed_at = datetime.now(timezone.utc)
                        await db.commit()
            except Exception:
                logger.exception("Export: failed to mark task %d as failed", task_id)
        finally:
            running_tasks.pop(task_id, None)


# ── 主循环 ──

async def run_export_scheduler() -> None:
    poll = settings.SCHEDULER_POLL_INTERVAL

    logger.info("Export scheduler started (poll=%ds, timeout=%dmin)", poll, TASK_TIMEOUT_MINUTES)

    # 启动时恢复被中断的任务
    await _recover_interrupted_tasks()

    running_tasks: dict[int, asyncio.Task] = {}

    try:
        while True:
            try:
                # 检查超时任务
                await _cancel_stale_tasks(running_tasks)

                if len(running_tasks) < settings.SCHEDULER_MAX_CONCURRENT_EXPORT:
                    task_id = await _claim_pending()
                    if task_id and task_id not in running_tasks:
                        atask = asyncio.create_task(_process_export(task_id, running_tasks))
                        running_tasks[task_id] = atask
            except Exception:
                logger.exception("Export scheduler error")
            await asyncio.sleep(poll)
    finally:
        # 取消所有正在执行的任务
        for tid, atask in running_tasks.items():
            if not atask.done():
                atask.cancel()
                logger.info("Export: cancelling task %d on shutdown", tid)
        logger.info("Export scheduler stopped")
