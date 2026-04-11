"""ワークフロー実行ステップの Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import StepStatus, StepType
from src.platform.domain.common.types import ExecutionId, SpecId, StepId
from src.platform.domain.execution.models.workflow_step import (
    StepError,
    WorkflowExecutionStep,
)
from src.platform.domain.execution.repositories.step_repository import (
    WorkflowExecutionStepRepository,
)
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "workflow_execution_steps"
ENTITY_TYPE = "WorkflowExecutionStep"


class CosmosWorkflowExecutionStepRepository(WorkflowExecutionStepRepository):
    """workflow_execution_steps コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, step_execution_id: StepId, execution_id: ExecutionId) -> WorkflowExecutionStep:
        async with cosmos_error_handler(ENTITY_TYPE, step_execution_id):
            doc = await self._container.read_item(item=step_execution_id, partition_key=execution_id)
        return _from_document(doc)

    async def list_by_execution(
        self,
        execution_id: ExecutionId,
        *,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[WorkflowExecutionStep], str | None]:
        docs, next_token = await paginate(
            self._container,
            "SELECT * FROM c WHERE c.workflowExecutionId = @execId ORDER BY c.createdAt ASC",
            [{"name": "@execId", "value": execution_id}],
            partition_key=execution_id,
            max_items=max_items,
            continuation_token=continuation_token,
        )
        return [_from_document(d) for d in docs], next_token

    async def create(self, entity: WorkflowExecutionStep) -> WorkflowExecutionStep:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.step_execution_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(
        self,
        entity: WorkflowExecutionStep,
        *,
        etag: str | None = None,
    ) -> WorkflowExecutionStep:
        doc = _to_document(entity)
        kwargs: dict[str, Any] = {
            "item": entity.step_execution_id,
            "body": doc,
        }
        if etag is not None:
            kwargs["if_match"] = etag
        async with cosmos_error_handler(ENTITY_TYPE, entity.step_execution_id):
            replaced = await self._container.replace_item(**kwargs)
        return _from_document(replaced)


def _to_document(entity: WorkflowExecutionStep) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": entity.step_execution_id,
        "workflowExecutionId": entity.workflow_execution_id,
        "stepId": entity.step_id,
        "stepName": entity.step_name,
        "stepType": entity.step_type.value,
        "status": entity.status.value,
        "attemptCount": entity.attempt_count,
        "schemaVersion": entity.schema_version,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }
    if entity.executor_details is not None:
        doc["executorDetails"] = entity.executor_details
    if entity.agent_id is not None:
        doc["agentId"] = entity.agent_id
    if entity.assigned_to is not None:
        doc["assignedTo"] = entity.assigned_to
    if entity.requested_by is not None:
        doc["requestedBy"] = entity.requested_by
    if entity.started_at is not None:
        doc["startedAt"] = entity.started_at.isoformat()
    if entity.completed_at is not None:
        doc["completedAt"] = entity.completed_at.isoformat()
    if entity.duration_ms is not None:
        doc["durationMs"] = entity.duration_ms
    if entity.error is not None:
        err: dict[str, Any] = {
            "code": entity.error.code,
            "message": entity.error.message,
        }
        if entity.error.detail is not None:
            err["detail"] = entity.error.detail
        if entity.error.occurred_at is not None:
            err["occurredAt"] = entity.error.occurred_at.isoformat()
        doc["error"] = err
    return doc


def _from_document(doc: dict[str, Any]) -> WorkflowExecutionStep:
    error_doc = doc.get("error")
    error = None
    if error_doc:
        occurred = error_doc.get("occurredAt")
        error = StepError(
            code=error_doc["code"],
            message=error_doc["message"],
            detail=error_doc.get("detail"),
            occurred_at=(datetime.fromisoformat(occurred) if occurred else None),
        )

    started = doc.get("startedAt")
    completed = doc.get("completedAt")
    agent_id = doc.get("agentId")

    return WorkflowExecutionStep(
        step_execution_id=StepId(doc["id"]),
        workflow_execution_id=ExecutionId(doc["workflowExecutionId"]),
        step_id=doc["stepId"],
        step_name=doc["stepName"],
        step_type=StepType(doc["stepType"]),
        status=StepStatus(doc["status"]),
        attempt_count=doc["attemptCount"],
        schema_version=doc["schemaVersion"],
        created_at=datetime.fromisoformat(doc["createdAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        executor_details=doc.get("executorDetails"),
        agent_id=SpecId(agent_id) if agent_id else None,
        assigned_to=doc.get("assignedTo"),
        requested_by=doc.get("requestedBy"),
        started_at=datetime.fromisoformat(started) if started else None,
        completed_at=datetime.fromisoformat(completed) if completed else None,
        duration_ms=doc.get("durationMs"),
        error=error,
    )
