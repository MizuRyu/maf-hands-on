"""ToolSpec ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.platform.api.deps.services import get_tool_spec_repo, get_tool_spec_service
from src.platform.api.schemas.common import API_PREFIX, BaseResponse
from src.platform.api.schemas.tool import (
    ToolSpecCreateRequest,
    ToolSpecResponseData,
    ToolSpecUpdateRequest,
)
from src.platform.application.spec_management.tool_spec_service import ToolSpecService
from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.types import SpecId
from src.platform.domain.registry.repositories.tool_spec_repository import (
    ToolSpecRepository,
)

router = APIRouter(prefix=API_PREFIX, tags=["tools"])


class ToolSpecResponse(BaseResponse[ToolSpecResponseData]):
    pass


class ToolSpecListResponse(BaseResponse[list[ToolSpecResponseData]]):
    pass


def _to_data(spec) -> ToolSpecResponseData:
    return ToolSpecResponseData(
        spec_id=spec.spec_id,
        name=spec.name,
        version=spec.version,
        description=spec.description,
        tool_type=spec.tool_type,
        implementation=spec.implementation,
        status=spec.status,
        created_by=spec.created_by,
        schema_version=spec.schema_version,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
        parameters=spec.parameters,
    )


@router.get("/tools/{spec_id}", response_model=ToolSpecResponse)
async def get_tool(
    spec_id: str,
    repo: Annotated[ToolSpecRepository, Depends(get_tool_spec_repo)],
) -> ToolSpecResponse:
    spec = await repo.get(SpecId(spec_id))
    return ToolSpecResponse(data=_to_data(spec))


@router.get("/tools", response_model=ToolSpecListResponse)
async def list_tools(
    repo: Annotated[ToolSpecRepository, Depends(get_tool_spec_repo)],
    status: SpecStatus | None = None,
    max_items: int = 50,
) -> ToolSpecListResponse:
    specs, _ = await repo.list(status=status, max_items=max_items)
    return ToolSpecListResponse(data=[_to_data(s) for s in specs])


@router.post("/tools", status_code=201, response_model=ToolSpecResponse)
async def create_tool(
    body: ToolSpecCreateRequest,
    service: Annotated[ToolSpecService, Depends(get_tool_spec_service)],
) -> ToolSpecResponse:
    spec = await service.register(
        name=body.name,
        version=body.version,
        description=body.description,
        tool_type=body.tool_type.value,
        implementation=body.implementation,
        parameters=body.parameters,
    )
    return ToolSpecResponse(data=_to_data(spec))


@router.patch("/tools/{spec_id}", response_model=ToolSpecResponse)
async def update_tool(
    spec_id: str,
    body: ToolSpecUpdateRequest,
    service: Annotated[ToolSpecService, Depends(get_tool_spec_service)],
) -> ToolSpecResponse:
    spec = await service.update(
        spec_id,
        name=body.name,
        description=body.description,
        implementation=body.implementation,
        parameters=body.parameters,
    )
    return ToolSpecResponse(data=_to_data(spec))


@router.post("/tools/{spec_id}/archive", response_model=ToolSpecResponse)
async def archive_tool(
    spec_id: str,
    service: Annotated[ToolSpecService, Depends(get_tool_spec_service)],
) -> ToolSpecResponse:
    spec = await service.archive(spec_id)
    return ToolSpecResponse(data=_to_data(spec))
