"""Agent Run 関連の API スキーマ。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentRunStartRequest(BaseModel):
    """Agent 実行開始リクエスト。"""

    input: str = Field(min_length=1)
    session_id: str | None = None
    approval_mode: str = "auto"


class ApprovalInputRequest(BaseModel):
    """Tool approval 応答リクエスト。"""

    action: str = Field(min_length=1)


class ToolCallResponseData(BaseModel):
    """Tool 呼び出し記録。"""

    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    status: str = "completed"


class PendingApprovalResponseData(BaseModel):
    """Tool approval 待機情報。"""

    tool_name: str
    arguments: dict[str, Any]


class AgentRunResponseData(BaseModel):
    """Agent 実行レスポンスデータ。"""

    run_id: str
    agent_id: str
    status: str
    input: str
    started_at: datetime
    session_id: str | None = None
    output: str | None = None
    tool_calls: list[ToolCallResponseData] = Field(default_factory=list)
    pending_approval: PendingApprovalResponseData | None = None
    trace_id: str | None = None
    created_by: str | None = None
    completed_at: datetime | None = None
