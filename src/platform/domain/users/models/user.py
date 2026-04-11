"""プラットフォームユーザーのドメインモデル。"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.platform.domain.common.enums import UserRole, UserStatus
from src.platform.domain.common.types import UserId


@dataclass(frozen=True)
class User:
    """プラットフォームユーザー。"""

    user_id: UserId
    display_name: str
    role: UserRole
    status: UserStatus
    schema_version: int
    created_at: datetime
    updated_at: datetime
    email: str | None = None
    preferences: dict[str, Any] | None = None
    last_login_at: datetime | None = None

    def with_status(self, status: UserStatus, updated_at: datetime) -> User:
        """ステータスを変更した新しいインスタンスを返す。"""
        return dataclasses.replace(self, status=status, updated_at=updated_at)
