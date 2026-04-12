"""WorkflowExecution のユースケース。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.platform.domain.common.enums import RunStatus
from src.platform.domain.common.types import ExecutionId, SpecId, UserId

# Query (get/list) は Repository 直読み。このサービスは Command のみ。
from src.platform.domain.execution.models.workflow_run import WorkflowExecution
from src.platform.domain.execution.repositories.execution_repository import (
    WorkflowExecutionRepository,
)

SCHEMA_VERSION = 1


class WorkflowExecutionService:
    """WorkflowExecution の管理ユースケースを提供する。"""

    def __init__(self, repository: WorkflowExecutionRepository) -> None:
        self._repo = repository

    async def start(
        self,
        *,
        workflow_id: str,
        workflow_name: str = "",
        workflow_version: int = 1,
        variables: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> WorkflowExecution:
        """新規 Workflow 実行を開始する。"""
        now = datetime.now(UTC)
        execution = WorkflowExecution(
            execution_id=ExecutionId(str(uuid.uuid4())),
            workflow_id=SpecId(workflow_id),
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            status=RunStatus.IDLE,
            schema_version=SCHEMA_VERSION,
            started_at=now,
            updated_at=now,
            variables=variables,
            created_by=UserId(created_by) if created_by else None,
        )
        return await self._repo.create(execution)

    async def cancel(self, execution_id: str) -> WorkflowExecution:
        """Workflow 実行をキャンセルする。"""
        existing = await self._repo.get(ExecutionId(execution_id))
        cancelled = existing.with_status(RunStatus.CANCELLED, datetime.now(UTC))
        return await self._repo.update(cancelled)

    async def resume(self, execution_id: str, *, response: dict[str, Any]) -> WorkflowExecution:
        """HITL 応答で Workflow 実行を再開する。"""
        import dataclasses

        existing = await self._repo.get(ExecutionId(execution_id))
        now = datetime.now(UTC)
        # variables に HITL 応答をマージ
        current_vars = existing.variables or {}
        current_vars["hitl_response"] = response
        resumed = dataclasses.replace(
            existing,
            status=RunStatus.RUNNING,
            updated_at=now,
            variables=current_vars,
        )
        return await self._repo.update(resumed)
