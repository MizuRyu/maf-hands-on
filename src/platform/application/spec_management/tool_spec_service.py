"""ToolSpec のユースケース。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.platform.domain.common.enums import SpecStatus, ToolType
from src.platform.domain.common.types import SpecId, UserId

# Query (get/list) は Repository 直読み。このサービスは Command のみ。
from src.platform.domain.registry.models.tool_spec import ToolSpec
from src.platform.domain.registry.repositories.tool_spec_repository import (
    ToolSpecRepository,
)

SCHEMA_VERSION = 1


class ToolSpecService:
    """ToolSpec の CRUD ユースケースを提供する。"""

    def __init__(self, repository: ToolSpecRepository) -> None:
        self._repo = repository

    async def register(
        self,
        *,
        name: str,
        version: int,
        description: str,
        tool_type: str,
        implementation: dict,
        created_by: str = "system",
        parameters: dict | None = None,
    ) -> ToolSpec:
        """新規 ToolSpec を登録する。"""
        now = datetime.now(UTC)
        spec = ToolSpec(
            spec_id=SpecId(str(uuid.uuid4())),
            name=name,
            version=version,
            description=description,
            tool_type=ToolType(tool_type),
            implementation=implementation,
            status=SpecStatus.DRAFT,
            created_by=UserId(created_by),
            schema_version=SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
            parameters=parameters,
        )
        return await self._repo.create(spec)

    async def update(
        self,
        spec_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        implementation: dict | None = None,
        parameters: dict | None = None,
    ) -> ToolSpec:
        """ToolSpec を更新する。"""
        import dataclasses

        existing = await self._repo.get(SpecId(spec_id))
        updates: dict = {"updated_at": datetime.now(UTC)}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if implementation is not None:
            updates["implementation"] = implementation
        if parameters is not None:
            updates["parameters"] = parameters

        updated = dataclasses.replace(existing, **updates)
        return await self._repo.update(updated)

    async def archive(self, spec_id: str) -> ToolSpec:
        """ToolSpec をアーカイブする。"""
        existing = await self._repo.get(SpecId(spec_id))
        archived = existing.with_status(SpecStatus.ARCHIVED, datetime.now(UTC))
        return await self._repo.update(archived)
