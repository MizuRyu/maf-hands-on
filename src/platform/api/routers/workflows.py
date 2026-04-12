"""WorkflowSpec ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.platform.api.deps.services import get_workflow_spec_repo, get_workflow_spec_service
from src.platform.api.schemas.common import API_PREFIX, BaseResponse
from src.platform.api.schemas.workflow import (
    WorkflowSpecCreateRequest,
    WorkflowSpecResponseData,
    WorkflowSpecUpdateRequest,
    WorkflowStepResponseData,
)
from src.platform.application.spec_management.workflow_spec_service import (
    WorkflowSpecService,
)
from src.platform.domain.common.types import SpecId
from src.platform.domain.registry.repositories.workflow_spec_repository import (
    WorkflowSpecRepository,
)

router = APIRouter(prefix=API_PREFIX, tags=["workflows"])


class WorkflowSpecResponse(BaseResponse[WorkflowSpecResponseData]):
    pass


class WorkflowSpecListResponse(BaseResponse[list[WorkflowSpecResponseData]]):
    pass


def _to_data(spec) -> WorkflowSpecResponseData:
    return WorkflowSpecResponseData(
        spec_id=spec.spec_id,
        name=spec.name,
        version=spec.version,
        steps={
            k: WorkflowStepResponseData(
                step_id=v.step_id,
                step_name=v.step_name,
                step_type=v.step_type,
                order=v.order,
            )
            for k, v in spec.steps.items()
        },
        schema_version=spec.schema_version,
        created_at=spec.created_at,
        updated_at=spec.updated_at,
        description=spec.description,
    )


@router.get("/workflows/{spec_id}", response_model=WorkflowSpecResponse)
async def get_workflow(
    spec_id: str,
    repo: Annotated[WorkflowSpecRepository, Depends(get_workflow_spec_repo)],
) -> WorkflowSpecResponse:
    spec = await repo.get(SpecId(spec_id))
    return WorkflowSpecResponse(data=_to_data(spec))


@router.get("/workflows", response_model=WorkflowSpecListResponse)
async def list_workflows(
    repo: Annotated[WorkflowSpecRepository, Depends(get_workflow_spec_repo)],
    max_items: int = 50,
) -> WorkflowSpecListResponse:
    specs, _ = await repo.list(max_items=max_items)
    return WorkflowSpecListResponse(data=[_to_data(s) for s in specs])


@router.post("/workflows", status_code=201, response_model=WorkflowSpecResponse)
async def create_workflow(
    body: WorkflowSpecCreateRequest,
    service: Annotated[WorkflowSpecService, Depends(get_workflow_spec_service)],
) -> WorkflowSpecResponse:
    spec = await service.register(
        name=body.name,
        version=body.version,
        steps=[s.model_dump() for s in body.steps],
        description=body.description,
    )
    return WorkflowSpecResponse(data=_to_data(spec))


@router.patch("/workflows/{spec_id}", response_model=WorkflowSpecResponse)
async def update_workflow(
    spec_id: str,
    body: WorkflowSpecUpdateRequest,
    service: Annotated[WorkflowSpecService, Depends(get_workflow_spec_service)],
) -> WorkflowSpecResponse:
    spec = await service.update(
        spec_id,
        name=body.name,
        steps=[s.model_dump() for s in body.steps] if body.steps else None,
        description=body.description,
    )
    return WorkflowSpecResponse(data=_to_data(spec))


@router.delete("/workflows/{spec_id}", status_code=204)
async def delete_workflow(
    spec_id: str,
    service: Annotated[WorkflowSpecService, Depends(get_workflow_spec_service)],
) -> None:
    await service.delete(spec_id)
