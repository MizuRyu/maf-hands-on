"""Agent 実行のドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import AgentRunStatus
from src.platform.domain.common.types import RunId, SessionId, SpecId, UserId


@dataclass(frozen=True)
class ToolCall:
    """Agent 実行中の Tool 呼び出し記録。"""

    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    status: str = "completed"


@dataclass(frozen=True)
class PendingApproval:
    """Tool approval の待機情報。"""

    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class AgentRun:
    """Agent 単体実行の記録。"""

    run_id: RunId
    agent_id: SpecId
    status: AgentRunStatus
    input: str
    schema_version: int
    started_at: datetime
    session_id: SessionId | None = None
    output: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    pending_approval: PendingApproval | None = None
    trace_id: str | None = None
    created_by: UserId | None = None
    completed_at: datetime | None = None

    def with_status(self, status: AgentRunStatus) -> AgentRun:
        return dataclasses.replace(self, status=status)
