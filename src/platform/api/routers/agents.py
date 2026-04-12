"""AgentSpec + AgentRun ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.platform.api.deps.services import (
    get_agent_run_repo,
    get_agent_run_service,
    get_agent_spec_repo,
    get_agent_spec_service,
)
from src.platform.api.schemas.agent import (
    AgentSpecCreateRequest,
    AgentSpecResponseData,
    AgentSpecUpdateRequest,
)
from src.platform.api.schemas.agent_run import (
    AgentRunResponseData,
    AgentRunStartRequest,
    ApprovalInputRequest,
    PendingApprovalResponseData,
    ToolCallResponseData,
)
from src.platform.api.schemas.common import API_PREFIX, BaseResponse
from src.platform.application.run_management.agent_run_service import AgentRunService
from src.platform.application.spec_management.agent_spec_service import (
    AgentSpecService,
)
from src.platform.domain.agent_runs.repositories.agent_run_repository import (
    AgentRunRepository,
)
from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.types import RunId, SpecId
from src.platform.domain.registry.repositories.agent_spec_repository import (
    AgentSpecRepository,
)

router = APIRouter(prefix=API_PREFIX, tags=["agents"])


class AgentSpecResponse(BaseResponse[AgentSpecResponseData]):
    pass


class AgentSpecListResponse(BaseResponse[list[AgentSpecResponseData]]):
    pass


class AgentRunResponse(BaseResponse[AgentRunResponseData]):
    pass


class AgentRunListResponse(BaseResponse[list[AgentRunResponseData]]):
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


def _run_to_data(run) -> AgentRunResponseData:
    tool_calls = [
        ToolCallResponseData(
            tool_name=tc.tool_name,
            arguments=tc.arguments,
            result=tc.result,
            status=tc.status,
        )
        for tc in run.tool_calls
    ]
    pending = None
    if run.pending_approval:
        pending = PendingApprovalResponseData(
            tool_name=run.pending_approval.tool_name,
            arguments=run.pending_approval.arguments,
        )
    return AgentRunResponseData(
        run_id=run.run_id,
        agent_id=run.agent_id,
        status=run.status.value,
        input=run.input,
        started_at=run.started_at,
        session_id=run.session_id,
        output=run.output,
        tool_calls=tool_calls,
        pending_approval=pending,
        trace_id=run.trace_id,
        created_by=run.created_by,
        completed_at=run.completed_at,
    )


# --- Agent Spec Query ---


@router.get("/agents/{agent_id}", response_model=AgentSpecResponse)
async def get_agent(
    agent_id: str,
    repo: Annotated[AgentSpecRepository, Depends(get_agent_spec_repo)],
) -> AgentSpecResponse:
    spec = await repo.get(SpecId(agent_id))
    return AgentSpecResponse(data=_to_data(spec))


@router.get("/agents", response_model=AgentSpecListResponse)
async def list_agents(
    repo: Annotated[AgentSpecRepository, Depends(get_agent_spec_repo)],
    status: SpecStatus | None = None,
    max_items: int = 50,
) -> AgentSpecListResponse:
    specs, _ = await repo.list(status=status, max_items=max_items)
    return AgentSpecListResponse(data=[_to_data(s) for s in specs])


# --- Agent Spec Command ---


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


@router.patch("/agents/{agent_id}", response_model=AgentSpecResponse)
async def update_agent(
    agent_id: str,
    body: AgentSpecUpdateRequest,
    service: Annotated[AgentSpecService, Depends(get_agent_spec_service)],
) -> AgentSpecResponse:
    spec = await service.update(
        agent_id,
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


@router.post("/agents/{agent_id}/activate", response_model=AgentSpecResponse)
async def activate_agent(
    agent_id: str,
    service: Annotated[AgentSpecService, Depends(get_agent_spec_service)],
) -> AgentSpecResponse:
    spec = await service.activate(agent_id)
    return AgentSpecResponse(data=_to_data(spec))


@router.post("/agents/{agent_id}/archive", response_model=AgentSpecResponse)
async def archive_agent(
    agent_id: str,
    service: Annotated[AgentSpecService, Depends(get_agent_spec_service)],
) -> AgentSpecResponse:
    spec = await service.archive(agent_id)
    return AgentSpecResponse(data=_to_data(spec))


# --- Agent Run Query ---


@router.get("/agents/{agent_id}/runs", response_model=AgentRunListResponse)
async def list_agent_runs(
    agent_id: str,
    repo: Annotated[AgentRunRepository, Depends(get_agent_run_repo)],
    max_items: int = 50,
) -> AgentRunListResponse:
    runs = await repo.list_by_agent(SpecId(agent_id), max_items=max_items)
    return AgentRunListResponse(data=[_run_to_data(r) for r in runs])


@router.get("/agents/{agent_id}/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    agent_id: str,
    run_id: str,
    repo: Annotated[AgentRunRepository, Depends(get_agent_run_repo)],
) -> AgentRunResponse:
    run = await repo.get(RunId(run_id))
    return AgentRunResponse(data=_run_to_data(run))


# --- Agent Run Command ---


@router.post("/agents/{agent_id}/runs", response_model=AgentRunResponse)
async def start_agent_run(
    agent_id: str,
    body: AgentRunStartRequest,
    service: Annotated[AgentRunService, Depends(get_agent_run_service)],
) -> AgentRunResponse:
    run = await service.start(
        agent_id=agent_id,
        input_text=body.input,
        session_id=body.session_id,
    )
    return AgentRunResponse(data=_run_to_data(run))


@router.post("/agents/{agent_id}/runs/{run_id}/input-response", response_model=AgentRunResponse)
async def submit_agent_approval(
    agent_id: str,
    run_id: str,
    body: ApprovalInputRequest,
    service: Annotated[AgentRunService, Depends(get_agent_run_service)],
) -> AgentRunResponse:
    run = await service.submit_approval(run_id, action=body.action)
    return AgentRunResponse(data=_run_to_data(run))
