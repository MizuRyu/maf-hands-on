"""ワークフロー実行ステップのドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import StepStatus, StepType
from src.platform.domain.common.types import ExecutionId, SpecId, StepId


@dataclass(frozen=True)
class StepError:
    """ステップ実行時のエラー情報。"""

    code: str
    message: str
    detail: str | None = None
    occurred_at: datetime | None = None


@dataclass(frozen=True)
class WorkflowExecutionStep:
    """ワークフロー実行ステップ。各ステップの実行状態・結果を記録する。"""

    step_execution_id: StepId
    workflow_execution_id: ExecutionId
    step_id: str
    step_name: str
    step_type: StepType
    status: StepStatus
    attempt_count: int
    schema_version: int
    created_at: datetime
    updated_at: datetime
    executor_details: dict[str, Any] | None = None
    agent_id: SpecId | None = None
    assigned_to: str | None = None
    requested_by: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error: StepError | None = None

    def with_status(self, status: StepStatus, updated_at: datetime) -> WorkflowExecutionStep:
        """ステータスを変更した新しいインスタンスを返す。"""
        return dataclasses.replace(self, status=status, updated_at=updated_at)
