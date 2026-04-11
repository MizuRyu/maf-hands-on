"""セッションリポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.common.types import SessionId, UserId
from src.platform.domain.sessions.session import Session


class SessionRepository(ABC):
    """チャットセッションの永続化インターフェース。"""

    @abstractmethod
    async def get(self, session_id: SessionId) -> Session:
        """セッション ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UserId,
        *,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[Session], str | None]:
        """ユーザー ID でセッション一覧を取得する。"""

    @abstractmethod
    async def create(self, entity: Session) -> Session:
        """新規作成する。ID 重複時は ConflictError。"""

    @abstractmethod
    async def update(self, entity: Session, *, etag: str | None = None) -> Session:
        """既存を更新する。ETag 不一致時は ConcurrencyError。"""

    @abstractmethod
    async def delete(self, session_id: SessionId) -> None:
        """削除する。存在しない場合は NotFoundError。"""
