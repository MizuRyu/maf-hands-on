"""Foundry 同期サービス。

AgentSpec の変更を Foundry Agent Service に同期する
Application 層のサービス。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.platform.domain.common.types import SpecId
from src.platform.infrastructure.foundry.agent_sync import (
    SyncStatus,
    apply_sync_result,
)

if TYPE_CHECKING:
    from src.platform.domain.registry.models.agent_spec import AgentSpec
    from src.platform.domain.registry.repositories.agent_spec_repository import (
        AgentSpecRepository,
    )
    from src.platform.infrastructure.foundry.agent_sync import (
        FoundryAgentSyncAdapter,
        FoundrySyncResult,
    )

logger = logging.getLogger(__name__)


class FoundrySyncService:
    """AgentSpec を Foundry に同期するサービス。"""

    def __init__(
        self,
        agent_spec_repo: AgentSpecRepository,
        foundry_adapter: FoundryAgentSyncAdapter,
    ) -> None:
        self._agent_spec_repo = agent_spec_repo
        self._foundry_adapter = foundry_adapter

    async def sync_agent(self, spec_id: str) -> FoundrySyncResult:
        """AgentSpec を Foundry に同期する。"""
        from src.platform.domain.common.exceptions import NotFoundError

        try:
            spec = await self._agent_spec_repo.get(SpecId(spec_id))
        except NotFoundError:
            raise

        result = await self._foundry_adapter.sync_agent_to_foundry(spec)

        if result.status == SyncStatus.SUCCESS:
            updated_spec = apply_sync_result(spec, result)
            await self._agent_spec_repo.update(updated_spec)
            logger.info(
                "Agent synced to Foundry: %s -> %s",
                spec.name,
                result.foundry_agent_name,
            )
        else:
            logger.warning(
                "Foundry sync failed for %s: %s",
                spec.name,
                result.error,
            )
        return result

    async def get_sync_status(self, spec: AgentSpec) -> dict[str, object]:
        """Foundry 同期ステータスを取得する。"""
        if not spec.foundry_agent_name:
            return {"synced": False}

        status = await self._foundry_adapter.get_foundry_agent_status(
            spec.foundry_agent_name,
        )
        return {
            "synced": True,
            "foundry_agent_name": spec.foundry_agent_name,
            "foundry_agent_version": spec.foundry_agent_version,
            "foundry_synced_at": (spec.foundry_synced_at.isoformat() if spec.foundry_synced_at else None),
            "foundry_status": status.get("status"),
        }

    async def delete_synced_agent(self, spec: AgentSpec) -> FoundrySyncResult:
        """Foundry 上の同期済み Agent を削除する。"""
        if not spec.foundry_agent_name:
            from src.platform.infrastructure.foundry.agent_sync import (
                FoundrySyncResult,
                SyncStatus,
            )

            return FoundrySyncResult(
                status=SyncStatus.SKIPPED,
                error="Agent not synced to Foundry",
            )

        return await self._foundry_adapter.delete_foundry_agent(
            spec.foundry_agent_name,
        )
