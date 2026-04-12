"""AgentSpec ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.platform.api.deps.services import get_agent_spec_repo, get_agent_spec_service
from src.platform.api.schemas.agent import (
    AgentSpecCreateRequest,
    AgentSpecResponseData,
    AgentSpecUpdateRequest,
)
from src.platform.api.schemas.common import API_PREFIX, BaseResponse
from src.platform.application.spec_management.agent_spec_service import (
    AgentSpecService,
)
from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.types import SpecId
from src.platform.domain.registry.repositories.agent_spec_repository import (
    AgentSpecRepository,
)

router = APIRouter(prefix=API_PREFIX, tags=["agents"])


class AgentSpecResponse(BaseResponse[AgentSpecResponseData]):
    pass


class AgentSpecListResponse(BaseResponse[list[AgentSpecResponseData]]):
    pass


def _to_data(spec) -> AgentSpecResponseData:
    return AgentSpecResponseData(
        spec_id=spec.spec_id,
        name=spec.name,
        version=spec.version,
        model_id=spec.model_id,
        instructions=spec.instructions,
        status=spec.status,
        created_by=spec.created_by,
        schema_version=spec.schema_version,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
        description=spec.description,
        tool_ids=spec.tool_ids,
        middleware_config=spec.middleware_config,
        context_provider_config=spec.context_provider_config,
        response_format=spec.response_format,
        foundry_agent_name=spec.foundry_agent_name,
        foundry_agent_version=spec.foundry_agent_version,
        foundry_deployment_type=spec.foundry_deployment_type,
        foundry_synced_at=spec.foundry_synced_at,
    )


@router.get("/agents/{spec_id}", response_model=AgentSpecResponse)
async def get_agent(
    spec_id: str,
    repo: Annotated[AgentSpecRepository, Depends(get_agent_spec_repo)],
) -> AgentSpecResponse:
    spec = await repo.get(SpecId(spec_id))
    return AgentSpecResponse(data=_to_data(spec))


@router.get("/agents", response_model=AgentSpecListResponse)
async def list_agents(
    repo: Annotated[AgentSpecRepository, Depends(get_agent_spec_repo)],
    status: SpecStatus | None = None,
    max_items: int = 50,
) -> AgentSpecListResponse:
    specs, _ = await repo.list(status=status, max_items=max_items)
    return AgentSpecListResponse(data=[_to_data(s) for s in specs])


@router.post("/agents", status_code=201, response_model=AgentSpecResponse)
async def create_agent(
    body: AgentSpecCreateRequest,
    service: Annotated[AgentSpecService, Depends(get_agent_spec_service)],
) -> AgentSpecResponse:
    spec = await service.register(
        name=body.name,
        version=body.version,
        model_id=body.model_id,
        instructions=body.instructions,
        description=body.description,
        tool_ids=body.tool_ids,
        middleware_config=body.middleware_config,
        context_provider_config=body.context_provider_config,
        response_format=body.response_format,
        foundry_deployment_type=(body.foundry_deployment_type.value if body.foundry_deployment_type else None),
    )
    return AgentSpecResponse(data=_to_data(spec))


@router.patch("/agents/{spec_id}", response_model=AgentSpecResponse)
async def update_agent(
    spec_id: str,
    body: AgentSpecUpdateRequest,
    service: Annotated[AgentSpecService, Depends(get_agent_spec_service)],
) -> AgentSpecResponse:
    spec = await service.update(
        spec_id,
        name=body.name,
        model_id=body.model_id,
        instructions=body.instructions,
        description=body.description,
        tool_ids=body.tool_ids,
        middleware_config=body.middleware_config,
        context_provider_config=body.context_provider_config,
        response_format=body.response_format,
    )
    return AgentSpecResponse(data=_to_data(spec))


@router.post("/agents/{spec_id}/archive", response_model=AgentSpecResponse)
async def archive_agent(
    spec_id: str,
    service: Annotated[AgentSpecService, Depends(get_agent_spec_service)],
) -> AgentSpecResponse:
    spec = await service.archive(spec_id)
    return AgentSpecResponse(data=_to_data(spec))
