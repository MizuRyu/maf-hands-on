"""ワークフロー実行リポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.common.enums import RunStatus
from src.platform.domain.common.types import ExecutionId, SpecId
from src.platform.domain.execution.models.workflow_run import WorkflowExecution


class WorkflowExecutionRepository(ABC):
    """ワークフロー実行インスタンスの永続化インターフェース。"""

    @abstractmethod
    async def get(self, execution_id: ExecutionId) -> WorkflowExecution:
        """実行 ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def list(
        self,
        *,
        workflow_id: SpecId | None = None,
        status: RunStatus | None = None,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[WorkflowExecution], str | None]:
        """実行一覧を取得する。continuation_token でページネーション。"""

    @abstractmethod
    async def create(self, entity: WorkflowExecution) -> WorkflowExecution:
        """新規作成する。ID 重複時は ConflictError。"""

    @abstractmethod
    async def update(self, entity: WorkflowExecution, *, etag: str | None = None) -> WorkflowExecution:
        """既存を更新する。ETag 不一致時は ConcurrencyError。"""

    @abstractmethod
    async def delete(self, execution_id: ExecutionId) -> None:
        """削除する。存在しない場合は NotFoundError。"""
