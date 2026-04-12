"""Foundry Agent Sync アダプター。

ローカル環境ではモック実装を提供する。
Azure Foundry 環境が利用可能な場合は、実際の API 呼び出しに差し替える。
"""

from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.platform.domain.registry.models.agent_spec import AgentSpec

logger = logging.getLogger(__name__)


class SyncStatus(StrEnum):
    """同期結果のステータス。"""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class FoundrySyncResult:
    """Foundry 同期の結果。"""

    status: SyncStatus
    foundry_agent_name: str | None = None
    foundry_agent_version: str | None = None
    synced_at: datetime | None = None
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class FoundryAgentSyncAdapter:
    """Foundry Agent Service への同期アダプター (モック実装)。"""

    def __init__(self, *, dry_run: bool = True) -> None:
        self._dry_run = dry_run

    async def sync_agent_to_foundry(self, spec: AgentSpec) -> FoundrySyncResult:
        """AgentSpec を Foundry Agent Service に同期する。"""
        logger.info(
            "Foundry sync: agent=%s, version=%d, dry_run=%s",
            spec.name,
            spec.version,
            self._dry_run,
        )

        if self._dry_run:
            return FoundrySyncResult(
                status=SyncStatus.SUCCESS,
                foundry_agent_name=f"foundry-{spec.name}",
                foundry_agent_version=f"v{spec.version}",
                synced_at=datetime.now(UTC),
                details={"mode": "dry_run"},
            )

        # 実際の Foundry API 呼び出しはここに実装
        return FoundrySyncResult(
            status=SyncStatus.SKIPPED,
            error="Foundry API not configured",
        )

    async def get_foundry_agent_status(self, foundry_agent_name: str) -> dict[str, Any]:
        """Foundry 上の Agent ステータスを取得する。"""
        logger.info("Foundry status check: %s", foundry_agent_name)
        if self._dry_run:
            return {
                "name": foundry_agent_name,
                "status": "deployed",
                "mode": "dry_run",
            }
        return {"name": foundry_agent_name, "status": "unknown"}

    async def delete_foundry_agent(self, foundry_agent_name: str) -> FoundrySyncResult:
        """Foundry 上の Agent を削除する。"""
        logger.info("Foundry delete: %s", foundry_agent_name)
        if self._dry_run:
            return FoundrySyncResult(
                status=SyncStatus.SUCCESS,
                foundry_agent_name=foundry_agent_name,
                synced_at=datetime.now(UTC),
                details={"action": "delete", "mode": "dry_run"},
            )
        return FoundrySyncResult(
            status=SyncStatus.SKIPPED,
            error="Foundry API not configured",
        )


def apply_sync_result(spec: AgentSpec, result: FoundrySyncResult) -> AgentSpec:
    """同期結果を AgentSpec に反映する。"""
    if result.status != SyncStatus.SUCCESS:
        return spec
    return dataclasses.replace(
        spec,
        foundry_agent_name=result.foundry_agent_name,
        foundry_agent_version=result.foundry_agent_version,
        foundry_synced_at=result.synced_at,
    )
