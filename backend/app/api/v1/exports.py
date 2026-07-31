from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.dependencies import get_db
from app.models.application import Application
from app.models.export_task import ExportTask
from app.schemas.export_task import CreateExportTaskRequest, ExportTaskResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["文档导出"])

VALID_FORMATS = {
    "application-form-txt",
    "manual-word",
    "manual-pdf",
    "source-code-word",
    "source-code-pdf",
    "all",
}

async def _validate_and_fix_task_consistency(tasks: list[ExportTask], db: AsyncSession) -> None:
    """验证导出任务状态与时间戳的一致性，修复不一致的任务

    规则：
    1. pending: started_at 和 completed_at 都应为 NULL
    2. processing: started_at 应有值，completed_at 应为 NULL
    3. completed/failed: started_at 和 completed_at 都应有值

    不一致的任务将被标记为 failed
    """
    now = datetime.now(timezone.utc)
    fixed_count = 0

    for task in tasks:
        error_msg = None

        if task.status == "pending":
            # pending状态：两个时间戳都应该为空
            if task.started_at is not None or task.completed_at is not None:
                error_msg = "状态为pending但存在时间戳，数据不一致"

        elif task.status == "processing":
            # processing状态：started_at应有值，completed_at应为空
            if task.started_at is None:
                error_msg = "状态为processing但started_at为空，数据不一致"
            elif task.completed_at is not None:
                error_msg = "状态为processing但completed_at已有值，数据不一致"

        elif task.status in ("completed", "failed"):
            # completed/failed状态：两个时间戳都应有值
            if task.started_at is None:
                error_msg = f"状态为{task.status}但started_at为空，数据不一致"
            elif task.completed_at is None:
                error_msg = f"状态为{task.status}但completed_at为空，数据不一致"

        if error_msg:
            logger.error(
                "Export task %d consistency check failed: status=%s, started_at=%s, completed_at=%s, error=%s",
                task.id, task.status, task.started_at, task.completed_at, error_msg
            )
            # 修复：标记为失败
            task.status = "failed"
            task.error_message = f"数据一致性检查失败：{error_msg}"
            if task.started_at is None:
                task.started_at = now
            if task.completed_at is None:
                task.completed_at = now
            fixed_count += 1

    if fixed_count > 0:
        await db.commit()
        logger.warning("Fixed %d export tasks with inconsistent state", fixed_count)


@router.post(
    "/applications/{app_id}/export-tasks",
    response_model=ExportTaskResponse,
    status_code=201,
)
async def create_export_task(
    app_id: int,
    data: CreateExportTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    if data.format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {data.format}")

    result = await db.execute(
        select(Application).where(Application.id == app_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="申请不存在")

    software_name = app.software_name or "export"

    # 预填文件名（带软件名），完成时 scheduler 会用最终名覆盖
    fmt_label = {
        "application-form-txt": "申请表信息",
        "manual-word": "文档鉴别材料",
        "manual-pdf": "文档鉴别材料",
        "source-code-word": "源程序鉴别材料",
        "source-code-pdf": "源程序鉴别材料",
        "all": "全部材料",
    }
    ext_map = {
        "application-form-txt": "txt",
        "manual-word": "docx", "manual-pdf": "pdf",
        "source-code-word": "docx", "source-code-pdf": "pdf",
        "all": "zip",
    }
    label = fmt_label.get(data.format, "导出")
    ext = ext_map.get(data.format, "bin")
    pre_file_name = f"{software_name}-{label}.{ext}"

    task = ExportTask(
        application_id=app_id,
        format=data.format,
        file_name=pre_file_name,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/export-tasks")
async def list_export_tasks(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count(ExportTask.id))
    )
    total = total_result.scalar()

    result = await db.execute(
        select(ExportTask)
        .order_by(desc(ExportTask.created_at))
        .offset(offset)
        .limit(page_size)
    )
    items = list(result.scalars().all())

    # 数据一致性检查和修复
    await _validate_and_fix_task_consistency(items, db)

    return {"items": [ExportTaskResponse.model_validate(i) for i in items], "total": total}


@router.get("/export-tasks/{task_id}/download")
async def download_file(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    from app.services.storage import get_full_path

    result = await db.execute(
        select(ExportTask).where(ExportTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    if task.status != "completed" or not task.file_path:
        raise HTTPException(status_code=400, detail="文件尚未准备好")

    full_path = get_full_path(task.file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    from fastapi.responses import FileResponse
    from urllib.parse import quote
    return FileResponse(
        path=str(full_path),
        filename=task.file_name,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(task.file_name or 'download')}"},
    )


@router.get(
    "/applications/{app_id}/export-tasks/latest",
    response_model=list[ExportTaskResponse],
)
async def get_latest_exports(
    app_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExportTask)
        .where(ExportTask.application_id == app_id)
        .order_by(desc(ExportTask.created_at))
        .limit(20)
    )
    items = list(result.scalars().all())

    # 数据一致性检查和修复
    await _validate_and_fix_task_consistency(items, db)

    return items


@router.delete("/export-tasks/{task_id}")
async def delete_export_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除单个导出任务"""
    result = await db.execute(
        select(ExportTask).where(ExportTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="导出任务不存在")

    await db.delete(task)
    await db.commit()
    return {"message": "删除成功"}


@router.delete("/export-tasks/failed/batch")
async def delete_failed_export_tasks(
    db: AsyncSession = Depends(get_db),
):
    """批量删除所有失败的导出任务"""
    result = await db.execute(
        select(ExportTask).where(ExportTask.status == "failed")
    )
    tasks = list(result.scalars().all())

    if not tasks:
        return {"message": "无失败任务", "count": 0}

    for task in tasks:
        await db.delete(task)

    await db.commit()
    logger.info("Deleted %d failed export tasks", len(tasks))
    return {"message": f"已删除 {len(tasks)} 个失败任务", "count": len(tasks)}
