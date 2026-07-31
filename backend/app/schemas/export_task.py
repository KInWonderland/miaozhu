from datetime import datetime

from pydantic import BaseModel


class CreateExportTaskRequest(BaseModel):
    format: str  # application-form-txt / manual-* / source-code-* / all


class ExportTaskResponse(BaseModel):
    id: int
    application_id: int
    format: str
    status: str
    file_name: str | None = None
    file_size: int | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
