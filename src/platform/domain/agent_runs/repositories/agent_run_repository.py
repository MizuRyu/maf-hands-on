"""Agent 実行リポジトリの ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.platform.domain.agent_runs.models.agent_run import AgentRun
from src.platform.domain.common.types import RunId, SpecId


class AgentRunRepository(ABC):
    """Agent 実行の永続化インターフェース。"""

    @abstractmethod
    async def get(self, run_id: RunId) -> AgentRun:
        """実行 ID で取得する。存在しない場合は NotFoundError。"""

    @abstractmethod
    async def list_by_agent(
        self,
        agent_id: SpecId,
        *,
        max_items: int = 50,
    ) -> list[AgentRun]:
        """Agent ID に紐づく実行一覧を取得する。"""

    @abstractmethod
    async def create(self, entity: AgentRun) -> AgentRun:
        """新規作成する。"""

    @abstractmethod
    async def update(self, entity: AgentRun) -> AgentRun:
        """更新する。"""
