"""ツール仕様の Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import SpecStatus, ToolType
from src.platform.domain.common.types import SpecId, UserId
from src.platform.domain.repository.tool_spec_repository import (
    ToolSpecRepository,
)
from src.platform.domain.specs.tool_spec import ToolSpec
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "tool_specs"
ENTITY_TYPE = "ToolSpec"


class CosmosToolSpecRepository(ToolSpecRepository):
    """tool_specs コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, spec_id: SpecId) -> ToolSpec:
        async with cosmos_error_handler(ENTITY_TYPE, spec_id):
            doc = await self._container.read_item(item=spec_id, partition_key=spec_id)
        return _from_document(doc)

    async def list_specs(
        self,
        *,
        status: SpecStatus | None = None,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[ToolSpec], str | None]:
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

    async def create(self, entity: ToolSpec) -> ToolSpec:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.spec_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: ToolSpec, *, etag: str | None = None) -> ToolSpec:
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


def _to_document(entity: ToolSpec) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": entity.spec_id,
        "name": entity.name,
        "version": entity.version,
        "description": entity.description,
        "toolType": entity.tool_type.value,
        "implementation": entity.implementation,
        "status": entity.status.value,
        "createdBy": entity.created_by,
        "schemaVersion": entity.schema_version,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }
    if entity.parameters is not None:
        doc["parameters"] = entity.parameters
    return doc


def _from_document(doc: dict[str, Any]) -> ToolSpec:
    return ToolSpec(
        spec_id=SpecId(doc["id"]),
        name=doc["name"],
        version=doc["version"],
        description=doc["description"],
        tool_type=ToolType(doc["toolType"]),
        implementation=doc["implementation"],
        status=SpecStatus(doc["status"]),
        created_by=UserId(doc["createdBy"]),
        schema_version=doc["schemaVersion"],
        created_at=datetime.fromisoformat(doc["createdAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        parameters=doc.get("parameters"),
    )
