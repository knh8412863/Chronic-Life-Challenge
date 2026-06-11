from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response
from fastapi.responses import StreamingResponse

from app.dependencies.security import get_request_user
from app.dtos.data_exports import (
    DataExportCreateRequest,
    DataExportListResponse,
    DataExportResponse,
    DataExportStatus,
)
from app.dtos.predictions import DataResponse
from app.models.users import User
from app.services.data_exports import DataExportService

data_export_router = APIRouter(tags=["data-exports"])


@data_export_router.post(
    "/data-exports",
    response_model=DataResponse[DataExportResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_data_export(
    request: DataExportCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DataExportService, Depends(DataExportService)],
) -> Response:
    result = await service.create_export(user, request)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_202_ACCEPTED)


@data_export_router.get(
    "/data-exports",
    response_model=DataResponse[DataExportListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_data_exports(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DataExportService, Depends(DataExportService)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    export_status: DataExportStatus | None = None,
) -> Response:
    result = await service.get_exports(user, limit=limit, offset=offset, export_status=export_status)
    return Response({"data": result.model_dump(mode="json")}, status_code=status.HTTP_200_OK)


@data_export_router.get("/data-exports/{export_id}/download", status_code=status.HTTP_200_OK)
async def download_data_export(
    export_id: str,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DataExportService, Depends(DataExportService)],
) -> StreamingResponse:
    filename, content_type, content = await service.build_download(user, export_id)
    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
