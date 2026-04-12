"""AgentRun のユースケース。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.platform.domain.agent_runs.models.agent_run import AgentRun
from src.platform.domain.agent_runs.repositories.agent_run_repository import (
    AgentRunRepository,
)
from src.platform.domain.common.enums import AgentRunStatus
from src.platform.domain.common.types import RunId, SessionId, SpecId, UserId

# Query (get/list) は Repository 直読み。このサービスは Command のみ。

SCHEMA_VERSION = 1


class AgentRunService:
    """Agent 実行の Command ユースケース。"""

    def __init__(self, repository: AgentRunRepository) -> None:
        self._repo = repository

    async def start(
        self,
        *,
        agent_id: str,
        input_text: str,
        session_id: str | None = None,
        created_by: str | None = None,
    ) -> AgentRun:
        """Agent 実行を開始し、同期的に結果を返す。"""
        now = datetime.now(UTC)
        run_id = RunId(str(uuid.uuid4()))

        # Agent 実行 (現在はモック。MAF Agent 統合後に差し替え)
        output = (
            f"[Mock] 入力を受け取りました: '{input_text}'"
            " — これはモックレスポンスです。実際の LLM は呼び出されていません。"
        )

        run = AgentRun(
            run_id=run_id,
            agent_id=SpecId(agent_id),
            status=AgentRunStatus.COMPLETED,
            input=input_text,
            output=output,
            schema_version=SCHEMA_VERSION,
            started_at=now,
            completed_at=datetime.now(UTC),
            session_id=SessionId(session_id) if session_id else None,
            created_by=UserId(created_by) if created_by else None,
        )
        return await self._repo.create(run)

    async def complete(
        self,
        run_id: str,
        *,
        output: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> AgentRun:
        """Agent 実行を完了する。"""
        import dataclasses

        from src.platform.domain.agent_runs.models.agent_run import ToolCall

        existing = await self._repo.get(RunId(run_id))
        tcs = [
            ToolCall(
                tool_name=tc["tool_name"],
                arguments=tc["arguments"],
                result=tc.get("result"),
                status=tc.get("status", "completed"),
            )
            for tc in (tool_calls or [])
        ]
        completed = dataclasses.replace(
            existing,
            status=AgentRunStatus.COMPLETED,
            output=output,
            tool_calls=tcs,
            completed_at=datetime.now(UTC),
        )
        return await self._repo.update(completed)

    async def submit_approval(
        self,
        run_id: str,
        *,
        action: str,
    ) -> AgentRun:
        """Tool approval に応答する。"""
        import dataclasses

        existing = await self._repo.get(RunId(run_id))
        resumed = dataclasses.replace(
            existing,
            status=AgentRunStatus.RUNNING,
            pending_approval=None,
        )
        return await self._repo.update(resumed)
