"""ワークフロー実行インスタンスのドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import RunStatus
from src.platform.domain.common.types import (
    CheckpointId,
    ExecutionId,
    SessionId,
    SpecId,
)


@dataclass(frozen=True)
class WorkflowExecution:
    """ワークフロー実行インスタンス。実行状態を管理する。"""

    execution_id: ExecutionId
    workflow_id: SpecId
    workflow_name: str
    workflow_version: int
    status: RunStatus
    schema_version: int
    started_at: datetime
    updated_at: datetime
    session_id: SessionId | None = None
    variables: dict[str, Any] | None = None
    current_step_id: str | None = None
    latest_checkpoint_id: CheckpointId | None = None
    result_summary: dict[str, Any] | None = None
    completed_at: datetime | None = None

    def with_status(self, status: RunStatus, updated_at: datetime) -> WorkflowExecution:
        """ステータスを変更した新しいインスタンスを返す。"""
        return dataclasses.replace(self, status=status, updated_at=updated_at)
