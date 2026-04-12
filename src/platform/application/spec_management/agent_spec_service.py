"""AgentSpec のユースケース。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.types import SpecId, UserId

# Query (get/list) は Repository 直読み。このサービスは Command のみ。
from src.platform.domain.registry.models.agent_spec import AgentSpec
from src.platform.domain.registry.repositories.agent_spec_repository import (
    AgentSpecRepository,
)

SCHEMA_VERSION = 1


class AgentSpecService:
    """AgentSpec の CRUD ユースケースを提供する。"""

    def __init__(self, repository: AgentSpecRepository) -> None:
        self._repo = repository

    async def register(
        self,
        *,
        name: str,
        version: int,
        model_id: str,
        instructions: str,
        created_by: str = "system",
        description: str | None = None,
        tool_ids: list[str] | None = None,
        middleware_config: list[dict] | None = None,
        context_provider_config: list[dict] | None = None,
        response_format: dict | None = None,
        foundry_deployment_type: str | None = None,
    ) -> AgentSpec:
        """新規 AgentSpec を登録する。"""
        from src.platform.domain.common.enums import FoundryDeploymentType

        now = datetime.now(UTC)
        spec = AgentSpec(
            spec_id=SpecId(str(uuid.uuid4())),
            name=name,
            version=version,
            model_id=model_id,
            instructions=instructions,
            status=SpecStatus.DRAFT,
            created_by=UserId(created_by),
            schema_version=SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
            description=description,
            tool_ids=tool_ids or [],
            middleware_config=middleware_config or [],
            context_provider_config=context_provider_config or [],
            response_format=response_format,
            foundry_deployment_type=(
                FoundryDeploymentType(foundry_deployment_type) if foundry_deployment_type else None
            ),
        )
        return await self._repo.create(spec)

    async def update(
        self,
        spec_id: str,
        *,
        name: str | None = None,
        model_id: str | None = None,
        instructions: str | None = None,
        description: str | None = None,
        tool_ids: list[str] | None = None,
        middleware_config: list[dict] | None = None,
        context_provider_config: list[dict] | None = None,
        response_format: dict | None = None,
    ) -> AgentSpec:
        """AgentSpec を更新する。"""
        import dataclasses

        existing = await self._repo.get(SpecId(spec_id))
        updates: dict = {"updated_at": datetime.now(UTC)}
        if name is not None:
            updates["name"] = name
        if model_id is not None:
            updates["model_id"] = model_id
        if instructions is not None:
            updates["instructions"] = instructions
        if description is not None:
            updates["description"] = description
        if tool_ids is not None:
            updates["tool_ids"] = tool_ids
        if middleware_config is not None:
            updates["middleware_config"] = middleware_config
        if context_provider_config is not None:
            updates["context_provider_config"] = context_provider_config
        if response_format is not None:
            updates["response_format"] = response_format

        updated = dataclasses.replace(existing, **updates)
        return await self._repo.update(updated)

    async def activate(self, spec_id: str) -> AgentSpec:
        """AgentSpec を active にする。"""
        existing = await self._repo.get(SpecId(spec_id))
        activated = existing.with_status(SpecStatus.ACTIVE, datetime.now(UTC))
        return await self._repo.update(activated)

    async def archive(self, spec_id: str) -> AgentSpec:
        """AgentSpec をアーカイブする。"""
        existing = await self._repo.get(SpecId(spec_id))
        archived = existing.with_status(SpecStatus.ARCHIVED, datetime.now(UTC))
        return await self._repo.update(archived)
