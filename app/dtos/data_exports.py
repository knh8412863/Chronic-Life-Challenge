from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class DataExportFormat(StrEnum):
    CSV = "CSV"
    PDF = "PDF"
    XLSX = "XLSX"
    JSON = "JSON"


class DataExportStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class DataExportType(StrEnum):
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    BLOOD_GLUCOSE = "BLOOD_GLUCOSE"
    EXERCISE = "EXERCISE"
    DIET = "DIET"
    SLEEP = "SLEEP"
    LIPID_OBESITY = "LIPID_OBESITY"
    RENAL = "RENAL"
    ACTIVITY = "ACTIVITY"


class DataExportCreateRequest(BaseModel):
    format: DataExportFormat
    start_date: date
    end_date: date
    data_types: Annotated[list[DataExportType], Field(min_length=1)]
    send_email: bool = False
    password_protect: bool = False

    @model_validator(mode="after")
    def validate_range_and_format(self) -> "DataExportCreateRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be earlier than or equal to end_date.")
        if self.password_protect and self.format not in {DataExportFormat.PDF, DataExportFormat.XLSX}:
            raise ValueError("password_protect is only available for PDF or XLSX exports.")
        return self


class DataExportResponse(BaseModel):
    export_id: str
    status: DataExportStatus
    format: DataExportFormat
    start_date: date
    end_date: date
    estimated_size_mb: float = 0.1
    estimated_completion_minutes: int = 1
    expires_at: datetime
    created_at: datetime


class DataExportListItemResponse(BaseModel):
    export_id: str
    format: DataExportFormat
    status: DataExportStatus
    start_date: date
    end_date: date
    file_size_mb: float | None = None
    download_count: int
    expires_at: datetime
    created_at: datetime


class DataExportPaginationResponse(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool


class DataExportListResponse(BaseModel):
    items: list[DataExportListItemResponse]
    pagination: DataExportPaginationResponse
