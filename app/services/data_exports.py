import csv
import io
import json
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.dtos.data_exports import (
    DataExportCreateRequest,
    DataExportFormat,
    DataExportListItemResponse,
    DataExportListResponse,
    DataExportPaginationResponse,
    DataExportResponse,
    DataExportStatus,
    DataExportType,
)
from app.models.predictions import ActivityLog, ExerciseLog, LipidObesityRecord, MealLog, RenalRecord, VitalRecord
from app.models.reports import DataExport, DataExportLog
from app.models.users import User


class DataExportService:
    async def create_export(self, user: User, data: DataExportCreateRequest) -> DataExportResponse:
        if not await self._has_any_data(user.id, data.start_date, data.end_date, data.data_types):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="선택한 기간에 데이터가 없습니다.")

        export = await DataExport.create(
            user=user,
            export_id=f"exp_{uuid4().hex}",
            format=data.format.value,
            start_date=data.start_date,
            end_date=data.end_date,
            data_types=[item.value for item in data.data_types],
            status=DataExportStatus.COMPLETED.value,
            send_email=data.send_email,
            password_protected=data.password_protect,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        await DataExportLog.create(export_id=export.export_id, event="COMPLETED")
        return self._to_response(export)

    async def get_exports(
        self,
        user: User,
        limit: int = 20,
        offset: int = 0,
        export_status: DataExportStatus | None = None,
    ) -> DataExportListResponse:
        query = DataExport.filter(user_id=user.id)
        if export_status:
            query = query.filter(status=export_status.value)
        total = await query.count()
        exports = await query.order_by("-created_at").offset(offset).limit(limit)
        return DataExportListResponse(
            items=[self._to_list_item(item) for item in exports],
            pagination=DataExportPaginationResponse(
                total=total,
                limit=limit,
                offset=offset,
                has_more=offset + limit < total,
            ),
        )

    async def build_download(self, user: User, export_id: str) -> tuple[str, str, bytes]:
        export = await DataExport.get_or_none(user_id=user.id, export_id=export_id)
        if export is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="요청한 내보내기 파일을 찾을 수 없습니다.")
        if export.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            export.status = DataExportStatus.EXPIRED.value
            await export.save(update_fields=["status", "updated_at"])
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="파일이 만료되어 삭제되었습니다.")

        rows = await self._collect_rows(user.id, export.start_date, export.end_date, export.data_types)
        content, content_type, ext = self._render(export.format, rows)
        export.download_count += 1
        export.file_size_bytes = len(content)
        await export.save(update_fields=["download_count", "file_size_bytes", "updated_at"])
        filename = f"health_data_{export.start_date}_to_{export.end_date}.{ext}"
        return filename, content_type, content

    @staticmethod
    async def _has_any_data(user_id: int, start: date, end: date, data_types: list[DataExportType]) -> bool:
        rows = await DataExportService._collect_rows(user_id, start, end, [item.value for item in data_types])
        return bool(rows)

    @staticmethod
    async def _collect_rows(user_id: int, start: date, end: date, data_types: list[str]) -> list[dict]:
        rows: list[dict] = []
        if DataExportType.BLOOD_PRESSURE.value in data_types:
            records = await VitalRecord.filter(user_id=user_id, record_date__gte=start, record_date__lte=end, measure_type__startswith="BP_")
            rows.extend({"type": "BLOOD_PRESSURE", "date": str(r.record_date), "measure_type": r.measure_type, "sbp": r.sbp, "dbp": r.dbp, "memo": r.memo} for r in records)
        if DataExportType.BLOOD_GLUCOSE.value in data_types:
            records = await VitalRecord.filter(user_id=user_id, record_date__gte=start, record_date__lte=end, measure_type__startswith="GLUCOSE_")
            rows.extend({"type": "BLOOD_GLUCOSE", "date": str(r.record_date), "measure_type": r.measure_type, "glucose": r.glucose, "memo": r.memo} for r in records)
        if DataExportType.EXERCISE.value in data_types:
            records = await ExerciseLog.filter(user_id=user_id, exercise_date__gte=start, exercise_date__lte=end)
            rows.extend({"type": "EXERCISE", "date": str(r.exercise_date), "exercise_type": r.exercise_type, "duration_minutes": r.duration_minutes, "calories_burned": r.calories_burned, "memo": r.memo} for r in records)
        if DataExportType.DIET.value in data_types:
            records = await MealLog.filter(user_id=user_id, meal_date__gte=start, meal_date__lte=end)
            rows.extend({"type": "DIET", "date": str(r.meal_date), "meal_type": r.meal_type, "food_name": r.food_name, "calories": r.calories, "sodium_mg": float(r.sodium_mg) if r.sodium_mg is not None else None, "memo": r.memo} for r in records)
        if DataExportType.LIPID_OBESITY.value in data_types:
            records = await LipidObesityRecord.filter(user_id=user_id, record_date__gte=start, record_date__lte=end)
            rows.extend({"type": "LIPID_OBESITY", "date": str(r.record_date), "total_cholesterol": r.total_cholesterol, "hdl_cholesterol": r.hdl_cholesterol, "ldl_cholesterol": r.ldl_cholesterol, "triglycerides": r.triglycerides, "bmi": float(r.bmi) if r.bmi is not None else None} for r in records)
        if DataExportType.RENAL.value in data_types:
            records = await RenalRecord.filter(user_id=user_id, record_date__gte=start, record_date__lte=end)
            rows.extend({"type": "RENAL", "date": str(r.record_date), "creatinine": float(r.creatinine) if r.creatinine is not None else None, "egfr": float(r.egfr) if r.egfr is not None else None, "bun": float(r.bun) if r.bun is not None else None, "urine_protein_pos": r.urine_protein_pos} for r in records)
        if DataExportType.ACTIVITY.value in data_types or DataExportType.SLEEP.value in data_types:
            records = await ActivityLog.filter(user_id=user_id, record_date__gte=start, record_date__lte=end)
            rows.extend({"type": "ACTIVITY", "date": str(r.record_date), "sleep_hours": float(r.sleep_hours) if r.sleep_hours is not None else None, "stress_level": r.stress_level, "diet_score": float(r.diet_score) if r.diet_score is not None else None, "memo": r.memo} for r in records)
        return rows

    @staticmethod
    def _render(export_format: str, rows: list[dict]) -> tuple[bytes, str, str]:
        if export_format == DataExportFormat.JSON.value:
            return json.dumps(rows, ensure_ascii=False, default=str).encode(), "application/json", "json"
        if export_format == DataExportFormat.PDF.value:
            text = "Health Data Export\n" + json.dumps(rows, ensure_ascii=False, default=str)
            return text.encode(), "application/pdf", "pdf"
        if export_format == DataExportFormat.XLSX.value:
            return DataExportService._csv_bytes(rows), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
        return DataExportService._csv_bytes(rows), "text/csv; charset=utf-8", "csv"

    @staticmethod
    def _csv_bytes(rows: list[dict]) -> bytes:
        if not rows:
            return b""
        headers = sorted({key for row in rows for key in row})
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue().encode()

    @staticmethod
    def _to_response(export: DataExport) -> DataExportResponse:
        return DataExportResponse(
            export_id=export.export_id,
            status=DataExportStatus(export.status),
            format=DataExportFormat(export.format),
            start_date=export.start_date,
            end_date=export.end_date,
            expires_at=export.expires_at,
            created_at=export.created_at,
        )

    @staticmethod
    def _to_list_item(export: DataExport) -> DataExportListItemResponse:
        return DataExportListItemResponse(
            export_id=export.export_id,
            format=DataExportFormat(export.format),
            status=DataExportStatus(export.status),
            start_date=export.start_date,
            end_date=export.end_date,
            file_size_mb=round(export.file_size_bytes / 1024 / 1024, 2) if export.file_size_bytes else None,
            download_count=export.download_count,
            expires_at=export.expires_at,
            created_at=export.created_at,
        )
