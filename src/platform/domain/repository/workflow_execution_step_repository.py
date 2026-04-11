"""ワークフロー実行ステップリポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.common.types import ExecutionId, StepId
from src.platform.domain.runs.workflow_execution_step import WorkflowExecutionStep


class WorkflowExecutionStepRepository(ABC):
    """ワークフロー実行ステップの永続化インターフェース。"""

    @abstractmethod
    async def get(self, step_execution_id: StepId, execution_id: ExecutionId) -> WorkflowExecutionStep:
        """ステップ実行 ID と実行 ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def list_by_execution(
        self,
        execution_id: ExecutionId,
        *,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[WorkflowExecutionStep], str | None]:
        """指定実行 ID のステップ一覧を取得する。"""

    @abstractmethod
    async def create(self, entity: WorkflowExecutionStep) -> WorkflowExecutionStep:
        """新規作成する。ID 重複時は ConflictError。"""

    @abstractmethod
    async def update(
        self,
        entity: WorkflowExecutionStep,
        *,
        etag: str | None = None,
    ) -> WorkflowExecutionStep:
        """既存を更新する。ETag 不一致時は ConcurrencyError。"""
