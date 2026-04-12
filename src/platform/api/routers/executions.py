"""WorkflowExecution 管理ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.platform.api.deps.services import (
    get_workflow_execution_repo,
    get_workflow_execution_service,
)
from src.platform.api.schemas.common import API_PREFIX, BaseResponse
from src.platform.api.schemas.execution import (
    ExecutionResponseData,
    ExecutionResumeRequest,
    ExecutionStartRequest,
)
from src.platform.application.run_management.workflow_execution_service import (
    WorkflowExecutionService,
)
from src.platform.domain.common.enums import RunStatus
from src.platform.domain.common.types import ExecutionId, SpecId
from src.platform.domain.execution.repositories.execution_repository import (
    WorkflowExecutionRepository,
)

router = APIRouter(prefix=API_PREFIX, tags=["executions"])


class ExecutionResponse(BaseResponse[ExecutionResponseData]):
    pass


class ExecutionListResponse(BaseResponse[list[ExecutionResponseData]]):
    pass


def _to_data(execution) -> ExecutionResponseData:
    return ExecutionResponseData(
        execution_id=execution.execution_id,
        workflow_id=execution.workflow_id,
        workflow_name=execution.workflow_name,
        workflow_version=execution.workflow_version,
        status=execution.status,
        schema_version=execution.schema_version,
        started_at=execution.started_at,
        updated_at=execution.updated_at,
        session_id=execution.session_id,
        variables=execution.variables,
        current_step_id=execution.current_step_id,
        latest_checkpoint_id=execution.latest_checkpoint_id,
        created_by=execution.created_by,
        updated_by=execution.updated_by,
        result_summary=execution.result_summary,
        completed_at=execution.completed_at,
    )


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    repo: Annotated[WorkflowExecutionRepository, Depends(get_workflow_execution_repo)],
) -> ExecutionResponse:
    execution = await repo.get(ExecutionId(execution_id))
    return ExecutionResponse(data=_to_data(execution))


@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    repo: Annotated[WorkflowExecutionRepository, Depends(get_workflow_execution_repo)],
    workflow_id: str | None = None,
    status: RunStatus | None = None,
    max_items: int = 50,
) -> ExecutionListResponse:
    executions, _ = await repo.list(
        workflow_id=SpecId(workflow_id) if workflow_id else None,
        status=status,
        max_items=max_items,
    )
    return ExecutionListResponse(data=[_to_data(e) for e in executions])


@router.post("/executions", status_code=201, response_model=ExecutionResponse)
async def start_execution(
    body: ExecutionStartRequest,
    service: Annotated[WorkflowExecutionService, Depends(get_workflow_execution_service)],
) -> ExecutionResponse:
    execution = await service.start(
        workflow_id=body.workflow_id,
        variables=body.variables,
        created_by=body.created_by,
    )
    return ExecutionResponse(data=_to_data(execution))


@router.post("/executions/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    execution_id: str,
    service: Annotated[WorkflowExecutionService, Depends(get_workflow_execution_service)],
) -> ExecutionResponse:
    execution = await service.cancel(execution_id)
    return ExecutionResponse(data=_to_data(execution))


@router.post("/executions/{execution_id}/resume", response_model=ExecutionResponse)
async def resume_execution(
    execution_id: str,
    body: ExecutionResumeRequest,
    service: Annotated[WorkflowExecutionService, Depends(get_workflow_execution_service)],
) -> ExecutionResponse:
    execution = await service.resume(execution_id, response=body.response)
    return ExecutionResponse(data=_to_data(execution))
