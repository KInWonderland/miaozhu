"""
后台定时调度器：轮询 pending 任务和待重新生成的 section。

特性：
- asyncio.Semaphore：限制并发 LLM 调用数（由 SCHEDULER_MAX_CONCURRENT_LLM 控制）
- 非阻塞派发：任务/section 以 asyncio.Task 方式后台执行，调度器循环不阻塞
- 超时清理：超过 30 分钟仍在 running 的任务会被自动标记为失败
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.generation import GenerationTask, GenerationSection
from app.services.llm.factory import create_llm_provider
from app.services.prompts.copyright import CopyrightPromptBuilder
from app.services.generation.orchestrator import GenerationOrchestrator

logger = logging.getLogger(__name__)

TASK_TIMEOUT_MINUTES = 30  # 任务超时时间（分钟）

# 进程内全局信号量
_llm_semaphore: asyncio.Semaphore | None = None
_llm_semaphore_limit: int | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _llm_semaphore, _llm_semaphore_limit
    limit = settings.SCHEDULER_MAX_CONCURRENT_LLM
    if _llm_semaphore is None or _llm_semaphore_limit != limit:
        _llm_semaphore = asyncio.Semaphore(limit)
        _llm_semaphore_limit = limit
        logger.info("Generation LLM concurrency set to %d", limit)
    return _llm_semaphore


def _create_orchestrator() -> GenerationOrchestrator:
    return GenerationOrchestrator(
        llm=create_llm_provider(),
        prompt_builder=CopyrightPromptBuilder(),
    )


# ── 任务派发 ───────────────────────────────────────────────

async def _claim_pending_task() -> int | None:
    """获取并标记一个 pending 任务为 running，返回 task_id"""
    async with async_session() as db:
        result = await db.execute(
            select(GenerationTask)
            .where(GenerationTask.status == "pending")
            .order_by(GenerationTask.created_at)
            .limit(1)
        )
        task = result.scalar_one_or_none()
        if not task:
            return None

        task.status = "running"
        await db.commit()
        return task.id


async def _claim_pending_section() -> int | None:
    """获取并标记一个待重新生成的 section 为 running，返回 section_id"""
    async with async_session() as db:
        result = await db.execute(
            select(GenerationSection)
            .join(GenerationTask, GenerationSection.task_id == GenerationTask.id)
            .where(
                GenerationSection.status == "pending",
                GenerationTask.status.in_(["completed", "failed"]),
            )
            .order_by(GenerationSection.updated_at)
            .limit(1)
        )
        section = result.scalar_one_or_none()
        if not section:
            return None

        section.status = "running"
        await db.commit()
        return section.id


# ── 启动恢复 ───────────────────────────────────────────────

async def _recover_interrupted_tasks() -> None:
    """系统启动时恢复被中断的任务：将所有 running 状态的任务和章节重置为 pending，以便重新调度。"""
    async with async_session() as db:
        now = datetime.now(timezone.utc)

        # 恢复被中断的 GenerationTask
        result = await db.execute(
            select(GenerationTask).where(GenerationTask.status == "running")
        )
        interrupted_tasks = list(result.scalars().all())
        for task in interrupted_tasks:
            logger.warning(
                "Recovering interrupted task %d (was running, updated_at=%s)",
                task.id, task.updated_at
            )
            task.status = "pending"
            task.updated_at = now

        # 恢复被中断的 GenerationSection（只处理已完成任务中的 section）
        result = await db.execute(
            select(GenerationSection)
            .join(GenerationTask, GenerationSection.task_id == GenerationTask.id)
            .where(
                GenerationSection.status == "running",
                GenerationTask.status.in_(["completed", "failed"])
            )
        )
        interrupted_sections = list(result.scalars().all())
        for section in interrupted_sections:
            logger.warning(
                "Recovering interrupted section %d (was running, updated_at=%s)",
                section.id, section.updated_at
            )
            section.status = "pending"
            section.updated_at = now

        if interrupted_tasks or interrupted_sections:
            await db.commit()
            logger.info(
                "Recovery complete: reset %d tasks and %d sections to pending",
                len(interrupted_tasks), len(interrupted_sections)
            )


# ── 状态同步 ───────────────────────────────────────────────

async def _sync_task_status() -> None:
    """根据 sections 的实际状态同步 task 状态。

    解决问题：
    - 调度器异常导致 task 状态为 failed，但实际上 sections 都成功了
    - task 状态与 sections 实际状态不一致
    """
    async with async_session() as db:
        # 查询所有非 pending/running 的任务
        result = await db.execute(
            select(GenerationTask)
            .where(GenerationTask.status.in_(["completed", "failed"]))
        )
        tasks = list(result.scalars().all())

        synced_count = 0
        for task in tasks:
            # 获取该任务的所有 sections
            result = await db.execute(
                select(GenerationSection)
                .where(GenerationSection.task_id == task.id)
            )
            sections = list(result.scalars().all())

            if not sections:
                continue

            # 统计各状态的 section 数量
            total = len(sections)
            completed = sum(1 for s in sections if s.status == "completed")
            failed = sum(1 for s in sections if s.status == "failed")
            pending_or_running = sum(1 for s in sections if s.status in ("pending", "running"))

            # 根据 sections 状态计算应该的 task 状态
            expected_status = None
            expected_error = None

            if pending_or_running > 0:
                # 仍有 sections 在处理中，任务应该是 running
                expected_status = "running"
            elif failed == total:
                # 所有 sections 都失败
                expected_status = "failed"
                expected_error = "所有章节生成失败"
            elif failed > 0:
                # 部分失败
                expected_status = "completed"
                expected_error = f"{failed} 个章节生成失败"
            else:
                # 全部成功
                expected_status = "completed"
                expected_error = None

            # 如果状态不一致，更新任务状态
            if task.status != expected_status:
                logger.info(
                    "Syncing task %d status: %s → %s (completed=%d, failed=%d, total=%d)",
                    task.id, task.status, expected_status, completed, failed, total
                )
                task.status = expected_status
                task.error_message = expected_error
                task.completed_sections = completed
                task.updated_at = datetime.now(timezone.utc)
                synced_count += 1

        if synced_count > 0:
            await db.commit()
            logger.info("Task status sync: updated %d tasks", synced_count)


# ── 超时清理 ───────────────────────────────────────────────

async def _cancel_stale_tasks(running_tasks: dict[int, asyncio.Task]) -> None:
    """检查并取消处理超过 30 分钟的生成任务。"""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=TASK_TIMEOUT_MINUTES)
    async with async_session() as db:
        # 清理卡住的 GenerationTask
        result = await db.execute(
            select(GenerationTask)
            .where(
                GenerationTask.status == "running",
                GenerationTask.updated_at <= cutoff,
            )
        )
        stale_tasks = list(result.scalars().all())
        for task in stale_tasks:
            logger.warning("Generation: task %d timed out (updated_at=%s)", task.id, task.updated_at)
            task.status = "failed"
            task.error_message = f"生成超时：处理时间超过 {TASK_TIMEOUT_MINUTES} 分钟，已自动取消"
            task.updated_at = datetime.now(timezone.utc)
            # 取消正在执行的 asyncio task
            atask = running_tasks.pop(task.id, None)
            if atask and not atask.done():
                atask.cancel()
                logger.info("Generation: cancelled asyncio task for generation task %d", task.id)

        # 清理卡住的 GenerationSection
        result = await db.execute(
            select(GenerationSection)
            .where(
                GenerationSection.status == "running",
                GenerationSection.updated_at <= cutoff,
            )
        )
        stale_sections = list(result.scalars().all())
        for section in stale_sections:
            logger.warning("Generation: section %d timed out (updated_at=%s)", section.id, section.updated_at)
            section.status = "failed"
            section.error_message = f"生成超时：处理时间超过 {TASK_TIMEOUT_MINUTES} 分钟，已自动取消"
            section.updated_at = datetime.now(timezone.utc)

        if stale_tasks or stale_sections:
            await db.commit()
            logger.info("Generation: cleaned up %d stale tasks and %d stale sections",
                       len(stale_tasks), len(stale_sections))


async def _run_task(task_id: int, running: dict[int, asyncio.Task]) -> None:
    try:
        logger.info("Scheduler: dispatching task %d", task_id)
        orchestrator = _create_orchestrator()
        await orchestrator.run_full(task_id, llm_semaphore=_get_semaphore())
    except asyncio.CancelledError:
        logger.warning("Scheduler: task %d was cancelled", task_id)
    except Exception:
        logger.exception("Scheduler: task %d failed", task_id)
        # orchestrator 异常退出时，确保 task 不会永久卡在 running
        try:
            async with async_session() as db:
                task = await db.get(GenerationTask, task_id)
                if task and task.status == "running":
                    task.status = "failed"
                    task.error_message = "生成过程异常中断"
                    task.updated_at = datetime.now(timezone.utc)
                    await db.commit()
                    logger.info("Scheduler: marked task %d as failed", task_id)
        except Exception:
            logger.exception("Scheduler: failed to mark task %d as failed", task_id)
    finally:
        running.pop(task_id, None)


async def _run_section(section_id: int, running: dict[int, asyncio.Task]) -> None:
    try:
        logger.info("Scheduler: dispatching section %d", section_id)
        orchestrator = _create_orchestrator()
        await orchestrator.run_single(section_id, llm_semaphore=_get_semaphore())
    except asyncio.CancelledError:
        logger.warning("Scheduler: section %d was cancelled", section_id)
    except Exception:
        logger.exception("Scheduler: section %d failed", section_id)
        # 确保 section 不会永久卡在 running
        try:
            async with async_session() as db:
                section = await db.get(GenerationSection, section_id)
                if section and section.status == "running":
                    section.status = "failed"
                    section.error_message = "生成过程异常中断"
                    section.updated_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception:
            logger.exception("Scheduler: failed to mark section %d as failed", section_id)
    finally:
        running.pop(section_id, None)


# ── 主循环 ─────────────────────────────────────────────────

async def run_scheduler() -> None:
    logger.info(
        "Generation scheduler started (poll=%ds, max_concurrent_llm=%d, timeout=%dmin)",
        settings.SCHEDULER_POLL_INTERVAL,
        settings.SCHEDULER_MAX_CONCURRENT_LLM,
        TASK_TIMEOUT_MINUTES,
    )

    # 启动时恢复被中断的任务
    await _recover_interrupted_tasks()

    running_tasks: dict[int, asyncio.Task] = {}
    running_sections: dict[int, asyncio.Task] = {}

    try:
        while True:
            try:
                # Settings are read in each loop so a changed .env is applied
                # before dispatching the next unit of work.
                max_llm = settings.SCHEDULER_MAX_CONCURRENT_LLM
                # 检查超时任务
                await _cancel_stale_tasks(running_tasks)

                # 同步任务状态（根据 sections 实际状态修正 task 状态）
                await _sync_task_status()

                # 尝试获取待处理的任务（最多同时 2 个全量任务）
                if len(running_tasks) < 2:
                    task_id = await _claim_pending_task()
                    if task_id and task_id not in running_tasks:
                        atask = asyncio.create_task(_run_task(task_id, running_tasks))
                        running_tasks[task_id] = atask

                # 尝试获取待重新生成的 section
                if len(running_sections) < max_llm:
                    section_id = await _claim_pending_section()
                    if section_id and section_id not in running_sections:
                        atask = asyncio.create_task(_run_section(section_id, running_sections))
                        running_sections[section_id] = atask

            except Exception:
                logger.exception("Scheduler error")
            await asyncio.sleep(settings.SCHEDULER_POLL_INTERVAL)
    finally:
        # 取消所有正在执行的任务
        for tid, atask in running_tasks.items():
            if not atask.done():
                atask.cancel()
                logger.info("Generation: cancelling task %d on shutdown", tid)
        for sid, atask in running_sections.items():
            if not atask.done():
                atask.cancel()
                logger.info("Generation: cancelling section %d on shutdown", sid)
        logger.info("Generation scheduler stopped")
