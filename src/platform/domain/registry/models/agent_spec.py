"""エージェント仕様のドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import FoundryDeploymentType, SpecStatus
from src.platform.domain.common.types import SpecId, UserId


@dataclass(frozen=True)
class AgentSpec:
    """エージェント仕様。MAF ChatAgent 構築に必要な設定を保持する。"""

    spec_id: SpecId
    name: str
    version: int
    model_id: str
    instructions: str
    status: SpecStatus
    created_by: UserId
    schema_version: int
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    tool_ids: list[str] = field(default_factory=list)
    middleware_config: list[dict[str, Any]] = field(default_factory=list)
    context_provider_config: list[dict[str, Any]] = field(default_factory=list)
    response_format: dict[str, Any] | None = None
    foundry_agent_name: str | None = None
    foundry_agent_version: str | None = None
    foundry_deployment_type: FoundryDeploymentType | None = None
    foundry_synced_at: datetime | None = None

    def with_status(self, status: SpecStatus, updated_at: datetime) -> AgentSpec:
        """ステータスを変更した新しいインスタンスを返す。"""
        return dataclasses.replace(self, status=status, updated_at=updated_at)
