"""WorkflowExecutionService のユニットテスト。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.platform.application.run_management.workflow_execution_service import (
    WorkflowExecutionService,
)
from src.platform.domain.common.enums import RunStatus


class TestWorkflowExecutionService:
    @pytest.fixture
    def repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, repo: AsyncMock) -> WorkflowExecutionService:
        return WorkflowExecutionService(repo)

    async def test_start_creates_execution(self, service: WorkflowExecutionService, repo: AsyncMock) -> None:
        """start は IDLE ステータスの実行を作成する。"""
        repo.create.return_value = MagicMock()
        await service.start(workflow_id="wf-1")
        repo.create.assert_called_once()
        created = repo.create.call_args[0][0]
        assert created.status == RunStatus.IDLE
        assert created.workflow_id == "wf-1"

    async def test_cancel_changes_status(self, service: WorkflowExecutionService, repo: AsyncMock) -> None:
        """cancel はステータスを CANCELLED に変更する。"""
        from datetime import UTC, datetime

        from src.platform.domain.common.types import ExecutionId, SpecId
        from src.platform.domain.execution.models.workflow_run import WorkflowExecution

        execution = WorkflowExecution(
            execution_id=ExecutionId("exec-1"),
            workflow_id=SpecId("wf-1"),
            workflow_name="test-wf",
            workflow_version=1,
            status=RunStatus.RUNNING,
            schema_version=1,
            started_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.get.return_value = execution
        repo.update.return_value = MagicMock()
        await service.cancel("exec-1")
        cancelled = repo.update.call_args[0][0]
        assert cancelled.status == RunStatus.CANCELLED

    async def test_resume_merges_hitl_response(self, service: WorkflowExecutionService, repo: AsyncMock) -> None:
        """resume は HITL 応答を variables にマージする。"""
        from datetime import UTC, datetime

        from src.platform.domain.common.types import ExecutionId, SpecId
        from src.platform.domain.execution.models.workflow_run import WorkflowExecution

        execution = WorkflowExecution(
            execution_id=ExecutionId("exec-1"),
            workflow_id=SpecId("wf-1"),
            workflow_name="test-wf",
            workflow_version=1,
            status=RunStatus.WAITING,
            schema_version=1,
            started_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            variables={"key": "value"},
        )
        repo.get.return_value = execution
        repo.update.return_value = MagicMock()
        await service.resume("exec-1", response={"approved": True})
        resumed = repo.update.call_args[0][0]
        assert resumed.status == RunStatus.RUNNING
        assert resumed.variables["hitl_response"] == {"approved": True}
        assert resumed.variables["key"] == "value"
