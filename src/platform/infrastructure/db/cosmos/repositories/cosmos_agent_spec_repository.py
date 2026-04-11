"""エージェント仕様の Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import FoundryDeploymentType, SpecStatus
from src.platform.domain.common.types import SpecId, UserId
from src.platform.domain.repository.agent_spec_repository import (
    AgentSpecRepository,
)
from src.platform.domain.specs.agent_spec import AgentSpec
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "agent_specs"
ENTITY_TYPE = "AgentSpec"


class CosmosAgentSpecRepository(AgentSpecRepository):
    """agent_specs コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, spec_id: SpecId) -> AgentSpec:
        async with cosmos_error_handler(ENTITY_TYPE, spec_id):
            doc = await self._container.read_item(item=spec_id, partition_key=spec_id)
        return _from_document(doc)

    async def list_specs(
        self,
        *,
        status: SpecStatus | None = None,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[AgentSpec], str | None]:
        query = "SELECT * FROM c"
        params: list[dict[str, Any]] = []
        if status is not None:
            query += " WHERE c.status = @status"
            params.append({"name": "@status", "value": status.value})

        docs, next_token = await paginate(
            self._container,
            query,
            params or None,
            max_items=max_items,
            continuation_token=continuation_token,
        )
        return [_from_document(d) for d in docs], next_token

    async def create(self, entity: AgentSpec) -> AgentSpec:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.spec_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: AgentSpec, *, etag: str | None = None) -> AgentSpec:
        doc = _to_document(entity)
        kwargs: dict[str, Any] = {
            "item": entity.spec_id,
            "body": doc,
        }
        if etag is not None:
            kwargs["if_match"] = etag
        async with cosmos_error_handler(ENTITY_TYPE, entity.spec_id):
            replaced = await self._container.replace_item(**kwargs)
        return _from_document(replaced)

    async def delete(self, spec_id: SpecId) -> None:
        async with cosmos_error_handler(ENTITY_TYPE, spec_id):
            await self._container.delete_item(item=spec_id, partition_key=spec_id)


def _to_document(entity: AgentSpec) -> dict[str, Any]:
    """ドメインモデルを Cosmos DB ドキュメントに変換する。"""
    doc: dict[str, Any] = {
        "id": entity.spec_id,
        "name": entity.name,
        "version": entity.version,
        "modelId": entity.model_id,
        "instructions": entity.instructions,
        "status": entity.status.value,
        "createdBy": entity.created_by,
        "schemaVersion": entity.schema_version,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }
    if entity.description is not None:
        doc["description"] = entity.description
    if entity.tool_ids:
        doc["toolIds"] = entity.tool_ids
    if entity.middleware_config:
        doc["middlewareConfig"] = entity.middleware_config
    if entity.context_provider_config:
        doc["contextProviderConfig"] = entity.context_provider_config
    if entity.response_format is not None:
        doc["responseFormat"] = entity.response_format
    if entity.foundry_agent_name is not None:
        doc["foundryAgentName"] = entity.foundry_agent_name
    if entity.foundry_agent_version is not None:
        doc["foundryAgentVersion"] = entity.foundry_agent_version
    if entity.foundry_deployment_type is not None:
        doc["foundryDeploymentType"] = entity.foundry_deployment_type.value
    if entity.foundry_synced_at is not None:
        doc["foundrySyncedAt"] = entity.foundry_synced_at.isoformat()
    return doc


def _from_document(doc: dict[str, Any]) -> AgentSpec:
    """Cosmos DB ドキュメントからドメインモデルを復元する。"""
    foundry_dt = doc.get("foundryDeploymentType")
    foundry_synced = doc.get("foundrySyncedAt")
    return AgentSpec(
        spec_id=SpecId(doc["id"]),
        name=doc["name"],
        version=doc["version"],
        model_id=doc["modelId"],
        instructions=doc["instructions"],
        status=SpecStatus(doc["status"]),
        created_by=UserId(doc["createdBy"]),
        schema_version=doc["schemaVersion"],
        created_at=datetime.fromisoformat(doc["createdAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        description=doc.get("description"),
        tool_ids=doc.get("toolIds", []),
        middleware_config=doc.get("middlewareConfig", []),
        context_provider_config=doc.get("contextProviderConfig", []),
        response_format=doc.get("responseFormat"),
        foundry_agent_name=doc.get("foundryAgentName"),
        foundry_agent_version=doc.get("foundryAgentVersion"),
        foundry_deployment_type=(FoundryDeploymentType(foundry_dt) if foundry_dt else None),
        foundry_synced_at=(datetime.fromisoformat(foundry_synced) if foundry_synced else None),
    )
