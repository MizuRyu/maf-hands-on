"""ワークフロー実行の Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import RunStatus
from src.platform.domain.common.types import (
    CheckpointId,
    ExecutionId,
    SessionId,
    SpecId,
)
from src.platform.domain.execution.models.workflow_run import WorkflowExecution
from src.platform.domain.execution.repositories.execution_repository import (
    WorkflowExecutionRepository,
)
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "workflow_executions"
ENTITY_TYPE = "WorkflowExecution"


class CosmosWorkflowExecutionRepository(WorkflowExecutionRepository):
    """workflow_executions コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, execution_id: ExecutionId) -> WorkflowExecution:
        async with cosmos_error_handler(ENTITY_TYPE, execution_id):
            doc = await self._container.read_item(item=execution_id, partition_key=execution_id)
        return _from_document(doc)

    async def list_executions(
        self,
        *,
        workflow_id: SpecId | None = None,
        status: RunStatus | None = None,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[WorkflowExecution], str | None]:
        conditions: list[str] = []
        params: list[dict[str, Any]] = []
        if workflow_id is not None:
            conditions.append("c.workflowId = @workflowId")
            params.append({"name": "@workflowId", "value": workflow_id})
        if status is not None:
            conditions.append("c.status = @status")
            params.append({"name": "@status", "value": status.value})

        query = "SELECT * FROM c"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        docs, next_token = await paginate(
            self._container,
            query,
            params or None,
            max_items=max_items,
            continuation_token=continuation_token,
        )
        return [_from_document(d) for d in docs], next_token

    async def create(self, entity: WorkflowExecution) -> WorkflowExecution:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.execution_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: WorkflowExecution, *, etag: str | None = None) -> WorkflowExecution:
        doc = _to_document(entity)
        kwargs: dict[str, Any] = {
            "item": entity.execution_id,
            "body": doc,
        }
        if etag is not None:
            kwargs["if_match"] = etag
        async with cosmos_error_handler(ENTITY_TYPE, entity.execution_id):
            replaced = await self._container.replace_item(**kwargs)
        return _from_document(replaced)

    async def delete(self, execution_id: ExecutionId) -> None:
        async with cosmos_error_handler(ENTITY_TYPE, execution_id):
            await self._container.delete_item(item=execution_id, partition_key=execution_id)


def _to_document(entity: WorkflowExecution) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": entity.execution_id,
        "workflowId": entity.workflow_id,
        "workflowName": entity.workflow_name,
        "workflowVersion": entity.workflow_version,
        "status": entity.status.value,
        "schemaVersion": entity.schema_version,
        "startedAt": entity.started_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }
    if entity.session_id is not None:
        doc["sessionId"] = entity.session_id
    if entity.variables is not None:
        doc["variables"] = entity.variables
    if entity.current_step_id is not None:
        doc["currentStepId"] = entity.current_step_id
    if entity.latest_checkpoint_id is not None:
        doc["latestCheckpointId"] = entity.latest_checkpoint_id
    if entity.result_summary is not None:
        doc["resultSummary"] = entity.result_summary
    if entity.completed_at is not None:
        doc["completedAt"] = entity.completed_at.isoformat()
    return doc


def _from_document(doc: dict[str, Any]) -> WorkflowExecution:
    completed = doc.get("completedAt")
    session = doc.get("sessionId")
    checkpoint = doc.get("latestCheckpointId")
    return WorkflowExecution(
        execution_id=ExecutionId(doc["id"]),
        workflow_id=SpecId(doc["workflowId"]),
        workflow_name=doc["workflowName"],
        workflow_version=doc["workflowVersion"],
        status=RunStatus(doc["status"]),
        schema_version=doc["schemaVersion"],
        started_at=datetime.fromisoformat(doc["startedAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        session_id=SessionId(session) if session else None,
        variables=doc.get("variables"),
        current_step_id=doc.get("currentStepId"),
        latest_checkpoint_id=(CheckpointId(checkpoint) if checkpoint else None),
        result_summary=doc.get("resultSummary"),
        completed_at=(datetime.fromisoformat(completed) if completed else None),
    )
