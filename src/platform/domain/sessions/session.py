"""チャットセッションのドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import SessionStatus
from src.platform.domain.common.types import ExecutionId, SessionId, UserId


@dataclass(frozen=True)
class Session:
    """チャットセッション。ユーザーとの会話セッションを管理する。"""

    session_id: SessionId
    user_id: UserId
    status: SessionStatus
    schema_version: int
    created_at: datetime
    updated_at: datetime
    service_session_id: str | None = None
    state: dict[str, Any] | None = None
    title: str | None = None
    workflow_execution_id: ExecutionId | None = None
    ttl: int | None = None

    def with_status(self, status: SessionStatus, updated_at: datetime) -> Session:
        """ステータスを変更した新しいインスタンスを返す。"""
        return dataclasses.replace(self, status=status, updated_at=updated_at)
