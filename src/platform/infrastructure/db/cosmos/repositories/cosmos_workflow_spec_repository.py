"""ワークフロー仕様の Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import StepType
from src.platform.domain.common.types import SpecId
from src.platform.domain.registry.models.workflow_spec import (
    WorkflowSpec,
    WorkflowStepDefinition,
)
from src.platform.domain.registry.repositories.workflow_spec_repository import (
    WorkflowSpecRepository,
)
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "workflows"
ENTITY_TYPE = "WorkflowSpec"


class CosmosWorkflowSpecRepository(WorkflowSpecRepository):
    """workflows コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, spec_id: SpecId) -> WorkflowSpec:
        async with cosmos_error_handler(ENTITY_TYPE, spec_id):
            doc = await self._container.read_item(item=spec_id, partition_key=spec_id)
        return _from_document(doc)

    async def list(
        self,
        *,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[WorkflowSpec], str | None]:
        docs, next_token = await paginate(
            self._container,
            "SELECT * FROM c",
            max_items=max_items,
            continuation_token=continuation_token,
        )
        return [_from_document(d) for d in docs], next_token

    async def create(self, entity: WorkflowSpec) -> WorkflowSpec:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.spec_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: WorkflowSpec) -> WorkflowSpec:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.spec_id):
            replaced = await self._container.replace_item(item=entity.spec_id, body=doc)
        return _from_document(replaced)

    async def delete(self, spec_id: SpecId) -> None:
        async with cosmos_error_handler(ENTITY_TYPE, spec_id):
            await self._container.delete_item(item=spec_id, partition_key=spec_id)


def _to_document(entity: WorkflowSpec) -> dict[str, Any]:
    steps_dict: dict[str, dict[str, Any]] = {}
    for key, step_def in entity.steps.items():
        steps_dict[key] = {
            "stepId": step_def.step_id,
            "stepName": step_def.step_name,
            "stepType": step_def.step_type.value,
            "order": step_def.order,
        }
    return {
        "id": entity.spec_id,
        "name": entity.name,
        "version": entity.version,
        "description": entity.description,
        "steps": steps_dict,
        "schemaVersion": entity.schema_version,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }


def _from_document(doc: dict[str, Any]) -> WorkflowSpec:
    raw_steps = doc.get("steps", {})
    steps: dict[str, WorkflowStepDefinition] = {}
    for key, val in raw_steps.items():
        steps[key] = WorkflowStepDefinition(
            step_id=val["stepId"],
            step_name=val["stepName"],
            step_type=StepType(val["stepType"]),
            order=val["order"],
        )
    return WorkflowSpec(
        spec_id=SpecId(doc["id"]),
        name=doc["name"],
        version=doc["version"],
        steps=steps,
        schema_version=doc["schemaVersion"],
        created_at=datetime.fromisoformat(doc["createdAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        description=doc.get("description"),
    )
