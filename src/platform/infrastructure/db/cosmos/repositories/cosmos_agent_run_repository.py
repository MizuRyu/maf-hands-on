"""Agent 実行の Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.agent_runs.models.agent_run import (
    AgentRun,
    PendingApproval,
    ToolCall,
)
from src.platform.domain.agent_runs.repositories.agent_run_repository import (
    AgentRunRepository,
)
from src.platform.domain.common.enums import AgentRunStatus
from src.platform.domain.common.types import RunId, SessionId, SpecId, UserId
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "agent_runs"
ENTITY_TYPE = "AgentRun"


class CosmosAgentRunRepository(AgentRunRepository):
    """agent_runs コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, run_id: RunId) -> AgentRun:
        async with cosmos_error_handler(ENTITY_TYPE, run_id):
            doc = await self._container.read_item(item=run_id, partition_key=run_id)
        return _from_document(doc)

    async def list_by_agent(
        self,
        agent_id: SpecId,
        *,
        max_items: int = 50,
    ) -> list[AgentRun]:
        docs, _ = await paginate(
            self._container,
            "SELECT * FROM c WHERE c.agentId = @agentId ORDER BY c.startedAt DESC",
            [{"name": "@agentId", "value": agent_id}],
            max_items=max_items,
        )
        return [_from_document(d) for d in docs]

    async def create(self, entity: AgentRun) -> AgentRun:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.run_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: AgentRun) -> AgentRun:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.run_id):
            replaced = await self._container.replace_item(item=entity.run_id, body=doc)
        return _from_document(replaced)


def _to_document(entity: AgentRun) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": entity.run_id,
        "agentId": entity.agent_id,
        "status": entity.status.value,
        "input": entity.input,
        "schemaVersion": entity.schema_version,
        "startedAt": entity.started_at.isoformat(),
    }
    if entity.session_id is not None:
        doc["sessionId"] = entity.session_id
    if entity.output is not None:
        doc["output"] = entity.output
    if entity.tool_calls:
        doc["toolCalls"] = [
            {
                "toolName": tc.tool_name,
                "arguments": tc.arguments,
                "result": tc.result,
                "status": tc.status,
            }
            for tc in entity.tool_calls
        ]
    if entity.pending_approval is not None:
        doc["pendingApproval"] = {
            "toolName": entity.pending_approval.tool_name,
            "arguments": entity.pending_approval.arguments,
        }
    if entity.trace_id is not None:
        doc["traceId"] = entity.trace_id
    if entity.created_by is not None:
        doc["createdBy"] = entity.created_by
    if entity.completed_at is not None:
        doc["completedAt"] = entity.completed_at.isoformat()
    return doc


def _from_document(doc: dict[str, Any]) -> AgentRun:
    tool_calls = [
        ToolCall(
            tool_name=tc["toolName"],
            arguments=tc["arguments"],
            result=tc.get("result"),
            status=tc.get("status", "completed"),
        )
        for tc in doc.get("toolCalls", [])
    ]
    pa_doc = doc.get("pendingApproval")
    pending = PendingApproval(tool_name=pa_doc["toolName"], arguments=pa_doc["arguments"]) if pa_doc else None
    completed = doc.get("completedAt")
    session = doc.get("sessionId")
    return AgentRun(
        run_id=RunId(doc["id"]),
        agent_id=SpecId(doc["agentId"]),
        status=AgentRunStatus(doc["status"]),
        input=doc["input"],
        schema_version=doc["schemaVersion"],
        started_at=datetime.fromisoformat(doc["startedAt"]),
        session_id=SessionId(session) if session else None,
        output=doc.get("output"),
        tool_calls=tool_calls,
        pending_approval=pending,
        trace_id=doc.get("traceId"),
        created_by=UserId(cb) if (cb := doc.get("createdBy")) else None,
        completed_at=datetime.fromisoformat(completed) if completed else None,
    )
