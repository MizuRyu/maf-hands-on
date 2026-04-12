"""WorkflowExecution 関連の API スキーマ。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.platform.domain.common.enums import RunStatus


class ExecutionStartRequest(BaseModel):
    """ワークフロー実行開始リクエスト。"""

    workflow_id: str = Field(min_length=1)
    variables: dict[str, Any] | None = None
    created_by: str | None = None


class ExecutionResumeRequest(BaseModel):
    """HITL 応答によるワークフロー再開リクエスト。"""

    response: dict[str, Any]


class ExecutionResponseData(BaseModel):
    """WorkflowExecution レスポンス。"""

    execution_id: str
    workflow_id: str
    workflow_name: str
    workflow_version: int
    status: RunStatus
    schema_version: int
    started_at: datetime
    updated_at: datetime
    session_id: str | None = None
    variables: dict[str, Any] | None = None
    current_step_id: str | None = None
    latest_checkpoint_id: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    result_summary: dict[str, Any] | None = None
    completed_at: datetime | None = None
