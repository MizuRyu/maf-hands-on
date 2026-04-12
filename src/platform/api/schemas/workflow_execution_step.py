"""WorkflowExecutionStep 関連の API スキーマ。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.platform.domain.common.enums import StepStatus, StepType


class WorkflowExecutionStepResponseData(BaseModel):
    """WorkflowExecutionStep レスポンスデータ。"""

    step_execution_id: str
    step_id: str
    step_name: str
    step_type: StepType
    status: StepStatus
    attempt_count: int
    agent_id: str | None = None
    assigned_to: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error: dict[str, Any] | None = None


class WorkflowExecutionHitlRequest(BaseModel):
    """HITL 応答リクエスト。"""

    step_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    comment: str | None = None
