"""ツール仕様のドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import SpecStatus, ToolType
from src.platform.domain.common.types import SpecId, UserId


@dataclass(frozen=True)
class ToolSpec:
    """ツール仕様。MAF Tool の設定を保持する。"""

    spec_id: SpecId
    name: str
    version: int
    description: str
    tool_type: ToolType
    implementation: dict[str, Any]
    status: SpecStatus
    created_by: UserId
    schema_version: int
    created_at: datetime
    updated_at: datetime
    parameters: dict[str, Any] | None = None

    def with_status(self, status: SpecStatus, updated_at: datetime) -> ToolSpec:
        """ステータスを変更した新しいインスタンスを返す。"""
        return dataclasses.replace(self, status=status, updated_at=updated_at)
