"""ユーザーリポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.common.types import UserId
from src.platform.domain.users.models.user import User


class UserRepository(ABC):
    """プラットフォームユーザーの永続化インターフェース。"""

    @abstractmethod
    async def get(self, user_id: UserId) -> User:
        """ユーザー ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def get_by_email(self, email: str) -> User:
        """メールアドレスで取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def create(self, entity: User) -> User:
        """新規作成する。ID 重複時は ConflictError。"""

    @abstractmethod
    async def update(self, entity: User) -> User:
        """既存を更新する。"""

    @abstractmethod
    async def delete(self, user_id: UserId) -> None:
        """削除する。存在しない場合は NotFoundError。"""
