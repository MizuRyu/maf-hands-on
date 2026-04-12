"""WorkflowSpec のユースケース。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.platform.domain.common.types import SpecId

# Query (get/list) は Repository 直読み。このサービスは Command のみ。
from src.platform.domain.registry.models.workflow_spec import (
    WorkflowSpec,
    WorkflowStepDefinition,
)
from src.platform.domain.registry.repositories.workflow_spec_repository import (
    WorkflowSpecRepository,
)

SCHEMA_VERSION = 1


class WorkflowSpecService:
    """WorkflowSpec の CRUD ユースケースを提供する。"""

    def __init__(self, repository: WorkflowSpecRepository) -> None:
        self._repo = repository

    async def register(
        self,
        *,
        name: str,
        version: int,
        steps: list[dict],
        description: str | None = None,
    ) -> WorkflowSpec:
        """新規 WorkflowSpec を登録する。"""
        now = datetime.now(UTC)
        step_map = {
            s["step_id"]: WorkflowStepDefinition(
                step_id=s["step_id"],
                step_name=s["step_name"],
                step_type=s["step_type"],
                depends_on=s.get("depends_on", []),
            )
            for s in steps
        }
        spec = WorkflowSpec(
            spec_id=SpecId(str(uuid.uuid4())),
            name=name,
            version=version,
            steps=step_map,
            schema_version=SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
            description=description,
        )
        return await self._repo.create(spec)

    async def update(
        self,
        spec_id: str,
        *,
        name: str | None = None,
        steps: list[dict] | None = None,
        description: str | None = None,
    ) -> WorkflowSpec:
        """WorkflowSpec を更新する。"""
        import dataclasses

        existing = await self._repo.get(SpecId(spec_id))
        updates: dict = {"updated_at": datetime.now(UTC)}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if steps is not None:
            updates["steps"] = {
                s["step_id"]: WorkflowStepDefinition(
                    step_id=s["step_id"],
                    step_name=s["step_name"],
                    step_type=s["step_type"],
                    depends_on=s.get("depends_on", []),
                )
                for s in steps
            }

        updated = dataclasses.replace(existing, **updates)
        return await self._repo.update(updated)

    async def delete(self, spec_id: str) -> None:
        """WorkflowSpec を削除する。"""
        await self._repo.delete(SpecId(spec_id))
