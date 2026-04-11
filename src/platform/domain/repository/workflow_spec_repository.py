"""ワークフロー仕様リポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.common.types import SpecId
from src.platform.domain.specs.workflow_spec import WorkflowSpec


class WorkflowSpecRepository(ABC):
    """ワークフロー定義の永続化インターフェース。"""

    @abstractmethod
    async def get(self, spec_id: SpecId) -> WorkflowSpec:
        """仕様 ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def list_specs(
        self,
        *,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[WorkflowSpec], str | None]:
        """仕様一覧を取得する。continuation_token でページネーション。"""

    @abstractmethod
    async def create(self, entity: WorkflowSpec) -> WorkflowSpec:
        """新規作成する。ID 重複時は ConflictError。"""

    @abstractmethod
    async def update(self, entity: WorkflowSpec) -> WorkflowSpec:
        """既存を更新する。"""

    @abstractmethod
    async def delete(self, spec_id: SpecId) -> None:
        """削除する。存在しない場合は NotFoundError。"""
