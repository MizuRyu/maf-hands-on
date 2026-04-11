"""ツール仕様リポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.types import SpecId
from src.platform.domain.specs.tool_spec import ToolSpec


class ToolSpecRepository(ABC):
    """ツール仕様の永続化インターフェース。"""

    @abstractmethod
    async def get(self, spec_id: SpecId) -> ToolSpec:
        """仕様 ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def list_specs(
        self,
        *,
        status: SpecStatus | None = None,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[ToolSpec], str | None]:
        """仕様一覧を取得する。continuation_token でページネーション。"""

    @abstractmethod
    async def create(self, entity: ToolSpec) -> ToolSpec:
        """新規作成する。ID 重複時は ConflictError。"""

    @abstractmethod
    async def update(self, entity: ToolSpec, *, etag: str | None = None) -> ToolSpec:
        """既存を更新する。ETag 不一致時は ConcurrencyError。"""

    @abstractmethod
    async def delete(self, spec_id: SpecId) -> None:
        """削除する。存在しない場合は NotFoundError。"""
