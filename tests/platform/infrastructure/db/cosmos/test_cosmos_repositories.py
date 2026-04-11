"""Cosmos DB リポジトリのテスト。

ContainerProxy をモックし、シリアライズ/デシリアライズと
エラーハンドリングを検証する。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.cosmos.exceptions import CosmosHttpResponseError

from src.platform.domain.common.enums import (
    FoundryDeploymentType,
    RunStatus,
    SessionStatus,
    SpecStatus,
    StepStatus,
    StepType,
    ToolType,
    UserRole,
    UserStatus,
)
from src.platform.domain.common.exceptions import (
    ConcurrencyError,
    ConflictError,
    NotFoundError,
)
from src.platform.domain.common.types import (
    ExecutionId,
    SessionId,
    SpecId,
    StepId,
    UserId,
)
from src.platform.domain.runs.workflow_execution import WorkflowExecution
from src.platform.domain.runs.workflow_execution_step import (
    WorkflowExecutionStep,
)
from src.platform.domain.sessions.session import Session
from src.platform.domain.specs.agent_spec import AgentSpec
from src.platform.domain.specs.tool_spec import ToolSpec
from src.platform.domain.specs.workflow_spec import WorkflowSpec
from src.platform.domain.users.user import User
from src.platform.infrastructure.db.cosmos.repositories.cosmos_agent_spec_repository import (
    CosmosAgentSpecRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_session_repository import (
    CosmosSessionRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_tool_spec_repository import (
    CosmosToolSpecRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_user_repository import (
    CosmosUserRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_execution_repository import (
    CosmosWorkflowExecutionRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_execution_step_repository import (
    CosmosWorkflowExecutionStepRepository,
)
from src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_spec_repository import (
    CosmosWorkflowSpecRepository,
)

NOW = datetime(2024, 1, 1, tzinfo=UTC)
NOW_ISO = NOW.isoformat()


def _make_cosmos_error(status_code: int) -> CosmosHttpResponseError:
    """テスト用の CosmosHttpResponseError を作成する。"""
    error = CosmosHttpResponseError(status_code=status_code, message="test error")
    return error


def _mock_container() -> MagicMock:
    """ContainerProxy のモック。各メソッドを AsyncMock にする。"""
    container = MagicMock()
    container.read_item = AsyncMock()
    container.create_item = AsyncMock()
    container.replace_item = AsyncMock()
    container.delete_item = AsyncMock()
    container.query_items = MagicMock()
    container.upsert_item = AsyncMock()
    return container


# ── AgentSpec ──


class TestCosmosAgentSpecRepository:
    def _agent_doc(self) -> dict[str, Any]:
        return {
            "id": "a1",
            "name": "test-agent",
            "version": "1.0.0",
            "modelId": "gpt-4o",
            "instructions": "Be helpful.",
            "status": "draft",
            "createdBy": "u1",
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get_returns_agent_spec(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._agent_doc()
        repo = CosmosAgentSpecRepository(container)

        result = await repo.get(SpecId("a1"))

        assert isinstance(result, AgentSpec)
        assert result.spec_id == "a1"
        assert result.status == SpecStatus.DRAFT
        container.read_item.assert_awaited_once_with(item="a1", partition_key="a1")

    async def test_get_not_found_raises(self) -> None:
        container = _mock_container()
        container.read_item.side_effect = _make_cosmos_error(404)
        repo = CosmosAgentSpecRepository(container)

        with pytest.raises(NotFoundError):
            await repo.get(SpecId("missing"))

    async def test_create_returns_created(self) -> None:
        container = _mock_container()
        doc = self._agent_doc()
        container.create_item.return_value = doc
        repo = CosmosAgentSpecRepository(container)

        spec = AgentSpec(
            spec_id=SpecId("a1"),
            name="test-agent",
            version=1,
            model_id="gpt-4o",
            instructions="Be helpful.",
            status=SpecStatus.DRAFT,
            created_by=UserId("u1"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(spec)

        assert result.spec_id == "a1"
        container.create_item.assert_awaited_once()

    async def test_create_conflict_raises(self) -> None:
        container = _mock_container()
        container.create_item.side_effect = _make_cosmos_error(409)
        repo = CosmosAgentSpecRepository(container)

        spec = AgentSpec(
            spec_id=SpecId("a1"),
            name="test-agent",
            version=1,
            model_id="gpt-4o",
            instructions="Be helpful.",
            status=SpecStatus.DRAFT,
            created_by=UserId("u1"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        with pytest.raises(ConflictError):
            await repo.create(spec)

    async def test_update_with_etag(self) -> None:
        container = _mock_container()
        doc = self._agent_doc()
        container.replace_item.return_value = doc
        repo = CosmosAgentSpecRepository(container)

        spec = AgentSpec(
            spec_id=SpecId("a1"),
            name="test-agent",
            version=1,
            model_id="gpt-4o",
            instructions="Be helpful.",
            status=SpecStatus.ACTIVE,
            created_by=UserId("u1"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        await repo.update(spec, etag="etag-abc")

        call_kwargs = container.replace_item.call_args
        assert call_kwargs.kwargs.get("if_match") == "etag-abc"

    async def test_update_etag_conflict_raises(self) -> None:
        container = _mock_container()
        container.replace_item.side_effect = _make_cosmos_error(412)
        repo = CosmosAgentSpecRepository(container)

        spec = AgentSpec(
            spec_id=SpecId("a1"),
            name="test-agent",
            version=1,
            model_id="gpt-4o",
            instructions="Be helpful.",
            status=SpecStatus.ACTIVE,
            created_by=UserId("u1"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        with pytest.raises(ConcurrencyError):
            await repo.update(spec, etag="stale-etag")

    async def test_delete(self) -> None:
        container = _mock_container()
        repo = CosmosAgentSpecRepository(container)
        await repo.delete(SpecId("a1"))
        container.delete_item.assert_awaited_once_with(item="a1", partition_key="a1")

    async def test_list_without_filter(self) -> None:
        container = _mock_container()
        repo = CosmosAgentSpecRepository(container)
        doc = self._agent_doc()

        with patch(
            "src.platform.infrastructure.db.cosmos.repositories.cosmos_agent_spec_repository.paginate",
            return_value=([doc], "next-token"),
        ):
            results, token = await repo.list_specs()

        assert len(results) == 1
        assert results[0].spec_id == "a1"
        assert token == "next-token"

    async def test_list_with_status_filter(self) -> None:
        container = _mock_container()
        repo = CosmosAgentSpecRepository(container)

        with patch(
            "src.platform.infrastructure.db.cosmos.repositories.cosmos_agent_spec_repository.paginate",
            return_value=([], None),
        ) as mock_paginate:
            await repo.list_specs(status=SpecStatus.ACTIVE)

        call_args = mock_paginate.call_args
        query = call_args[0][1]
        assert "WHERE" in query
        assert "@status" in query

    async def test_update_without_etag(self) -> None:
        container = _mock_container()
        doc = self._agent_doc()
        container.replace_item.return_value = doc
        repo = CosmosAgentSpecRepository(container)

        spec = AgentSpec(
            spec_id=SpecId("a1"),
            name="test-agent",
            version=1,
            model_id="gpt-4o",
            instructions="Be helpful.",
            status=SpecStatus.ACTIVE,
            created_by=UserId("u1"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        await repo.update(spec)

        call_kwargs = container.replace_item.call_args
        assert "if_match" not in call_kwargs.kwargs

    async def test_get_with_optional_fields_roundtrip(self) -> None:
        """Optional フィールドを含むドキュメントのデシリアライズ。"""
        container = _mock_container()
        doc = self._agent_doc()
        doc["description"] = "Agent description"
        doc["toolIds"] = ["t1", "t2"]
        doc["foundryAgentName"] = "my-foundry-agent"
        doc["foundryDeploymentType"] = "hosted"
        doc["foundrySyncedAt"] = NOW_ISO
        container.read_item.return_value = doc
        repo = CosmosAgentSpecRepository(container)

        result = await repo.get(SpecId("a1"))

        assert result.description == "Agent description"
        assert result.tool_ids == ["t1", "t2"]
        assert result.foundry_agent_name == "my-foundry-agent"
        assert result.foundry_deployment_type == FoundryDeploymentType.HOSTED


# ── ToolSpec ──


class TestCosmosToolSpecRepository:
    def _tool_doc(self) -> dict[str, Any]:
        return {
            "id": "t1",
            "name": "my-tool",
            "version": "1.0.0",
            "description": "A tool",
            "toolType": "function",
            "implementation": {"module": "tools.my"},
            "status": "active",
            "createdBy": "u1",
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._tool_doc()
        repo = CosmosToolSpecRepository(container)

        result = await repo.get(SpecId("t1"))
        assert isinstance(result, ToolSpec)
        assert result.tool_type == ToolType.FUNCTION

    async def test_create(self) -> None:
        container = _mock_container()
        container.create_item.return_value = self._tool_doc()
        repo = CosmosToolSpecRepository(container)

        tool = ToolSpec(
            spec_id=SpecId("t1"),
            name="my-tool",
            version=1,
            description="A tool",
            tool_type=ToolType.FUNCTION,
            implementation={"module": "tools.my"},
            status=SpecStatus.ACTIVE,
            created_by=UserId("u1"),
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(tool)
        assert result.spec_id == "t1"


# ── WorkflowSpec ──


class TestCosmosWorkflowSpecRepository:
    def _wf_doc(self) -> dict[str, Any]:
        return {
            "id": "w1",
            "name": "test-wf",
            "version": "1.0.0",
            "description": None,
            "steps": {
                "step1": {
                    "stepId": "s1",
                    "stepName": "Step 1",
                    "stepType": "agent",
                    "order": 0,
                }
            },
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._wf_doc()
        repo = CosmosWorkflowSpecRepository(container)

        result = await repo.get(SpecId("w1"))
        assert isinstance(result, WorkflowSpec)
        assert "step1" in result.steps


# ── WorkflowExecution ──


class TestCosmosWorkflowExecutionRepository:
    def _exec_doc(self) -> dict[str, Any]:
        return {
            "id": "e1",
            "workflowId": "w1",
            "workflowName": "test-wf",
            "workflowVersion": "1.0.0",
            "status": "idle",
            "schemaVersion": 1,
            "startedAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._exec_doc()
        repo = CosmosWorkflowExecutionRepository(container)

        result = await repo.get(ExecutionId("e1"))
        assert isinstance(result, WorkflowExecution)
        assert result.status == RunStatus.IDLE

    async def test_update_with_etag(self) -> None:
        container = _mock_container()
        container.replace_item.return_value = self._exec_doc()
        repo = CosmosWorkflowExecutionRepository(container)

        exe = WorkflowExecution(
            execution_id=ExecutionId("e1"),
            workflow_id=SpecId("w1"),
            workflow_name="test-wf",
            workflow_version=1,
            status=RunStatus.RUNNING,
            schema_version=1,
            started_at=NOW,
            updated_at=NOW,
        )
        await repo.update(exe, etag="etag-xyz")
        call_kwargs = container.replace_item.call_args
        assert call_kwargs.kwargs.get("if_match") == "etag-xyz"


# ── WorkflowExecutionStep ──


class TestCosmosWorkflowExecutionStepRepository:
    def _step_doc(self) -> dict[str, Any]:
        return {
            "id": "se1",
            "workflowExecutionId": "e1",
            "stepId": "s1",
            "stepName": "Step 1",
            "stepType": "agent",
            "status": "idle",
            "attemptCount": 0,
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._step_doc()
        repo = CosmosWorkflowExecutionStepRepository(container)

        result = await repo.get(StepId("se1"), ExecutionId("e1"))
        assert isinstance(result, WorkflowExecutionStep)
        container.read_item.assert_awaited_once_with(item="se1", partition_key="e1")

    async def test_step_with_error_roundtrip(self) -> None:
        """エラー情報を含むステップのシリアライズ・デシリアライズ。"""
        container = _mock_container()
        doc = self._step_doc()
        doc["error"] = {
            "code": "E001",
            "message": "Something failed",
            "detail": "stack trace here",
            "occurredAt": NOW_ISO,
        }
        doc["status"] = "failed"
        container.read_item.return_value = doc
        repo = CosmosWorkflowExecutionStepRepository(container)

        result = await repo.get(StepId("se1"), ExecutionId("e1"))
        assert result.error is not None
        assert result.error.code == "E001"
        assert result.error.detail == "stack trace here"


# ── Session ──


class TestCosmosSessionRepository:
    def _session_doc(self) -> dict[str, Any]:
        return {
            "id": "sess1",
            "sessionId": "sess1",
            "userId": "u1",
            "status": "active",
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._session_doc()
        repo = CosmosSessionRepository(container)

        result = await repo.get(SessionId("sess1"))
        assert isinstance(result, Session)
        assert result.status == SessionStatus.ACTIVE

    async def test_update_with_etag(self) -> None:
        container = _mock_container()
        container.replace_item.return_value = self._session_doc()
        repo = CosmosSessionRepository(container)

        session = Session(
            session_id=SessionId("sess1"),
            user_id=UserId("u1"),
            status=SessionStatus.ACTIVE,
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        await repo.update(session, etag="etag-sess")
        call_kwargs = container.replace_item.call_args
        assert call_kwargs.kwargs.get("if_match") == "etag-sess"


# ── User ──


class TestCosmosUserRepository:
    def _user_doc(self) -> dict[str, Any]:
        return {
            "id": "u1",
            "displayName": "Test User",
            "role": "operator",
            "status": "active",
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_get(self) -> None:
        container = _mock_container()
        container.read_item.return_value = self._user_doc()
        repo = CosmosUserRepository(container)

        result = await repo.get(UserId("u1"))
        assert isinstance(result, User)
        assert result.display_name == "Test User"

    async def test_get_by_email_not_found(self) -> None:
        """メール検索で見つからない場合 NotFoundError。"""
        container = _mock_container()
        repo = CosmosUserRepository(container)

        # paginate をモックして空リストを返す
        with patch(
            "src.platform.infrastructure.db.cosmos.repositories.cosmos_user_repository.paginate",
            return_value=([], None),
        ):
            with pytest.raises(NotFoundError):
                await repo.get_by_email("missing@example.com")

    async def test_delete(self) -> None:
        container = _mock_container()
        repo = CosmosUserRepository(container)
        await repo.delete(UserId("u1"))
        container.delete_item.assert_awaited_once_with(item="u1", partition_key="u1")


# ── CosmosHelpers ──


class TestCosmosHelpers:
    async def test_cosmos_error_handler_404(self) -> None:
        from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
            cosmos_error_handler,
        )

        with pytest.raises(NotFoundError):
            async with cosmos_error_handler("Test", "id1"):
                raise _make_cosmos_error(404)

    async def test_cosmos_error_handler_409(self) -> None:
        from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
            cosmos_error_handler,
        )

        with pytest.raises(ConflictError):
            async with cosmos_error_handler("Test", "id1"):
                raise _make_cosmos_error(409)

    async def test_cosmos_error_handler_412(self) -> None:
        from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
            cosmos_error_handler,
        )

        with pytest.raises(ConcurrencyError):
            async with cosmos_error_handler("Test", "id1"):
                raise _make_cosmos_error(412)

    async def test_cosmos_error_handler_other_reraises(self) -> None:
        from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
            cosmos_error_handler,
        )

        with pytest.raises(CosmosHttpResponseError):
            async with cosmos_error_handler("Test", "id1"):
                raise _make_cosmos_error(500)

    async def test_cosmos_error_handler_no_error(self) -> None:
        """エラーなしの場合は正常に通過する。"""
        from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
            cosmos_error_handler,
        )

        async with cosmos_error_handler("Test", "id1"):
            pass  # 例外なし — 正常通過


# ── 追加: create / delete / list テスト ──


class TestCosmosWorkflowSpecRepositoryExtended:
    def _wf_doc(self) -> dict[str, Any]:
        return {
            "id": "w1",
            "name": "test-wf",
            "version": "1.0.0",
            "description": None,
            "steps": {
                "step1": {
                    "stepId": "s1",
                    "stepName": "Step 1",
                    "stepType": "agent",
                    "order": 0,
                }
            },
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_create(self) -> None:
        container = _mock_container()
        container.create_item.return_value = self._wf_doc()
        repo = CosmosWorkflowSpecRepository(container)

        from src.platform.domain.specs.workflow_spec import WorkflowStepDefinition

        spec = WorkflowSpec(
            spec_id=SpecId("w1"),
            name="test-wf",
            version=1,
            steps={
                "step1": WorkflowStepDefinition(step_id="s1", step_name="Step 1", step_type=StepType.AGENT, order=0)
            },
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(spec)
        assert result.spec_id == "w1"
        container.create_item.assert_awaited_once()

    async def test_delete(self) -> None:
        container = _mock_container()
        repo = CosmosWorkflowSpecRepository(container)
        await repo.delete(SpecId("w1"))
        container.delete_item.assert_awaited_once()


class TestCosmosWorkflowExecutionRepositoryExtended:
    def _exec_doc(self) -> dict[str, Any]:
        return {
            "id": "e1",
            "workflowId": "w1",
            "workflowName": "test-wf",
            "workflowVersion": "1.0.0",
            "status": "idle",
            "schemaVersion": 1,
            "startedAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_create(self) -> None:
        container = _mock_container()
        container.create_item.return_value = self._exec_doc()
        repo = CosmosWorkflowExecutionRepository(container)

        exe = WorkflowExecution(
            execution_id=ExecutionId("e1"),
            workflow_id=SpecId("w1"),
            workflow_name="test-wf",
            workflow_version=1,
            status=RunStatus.IDLE,
            schema_version=1,
            started_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(exe)
        assert result.execution_id == "e1"

    async def test_delete(self) -> None:
        container = _mock_container()
        repo = CosmosWorkflowExecutionRepository(container)
        await repo.delete(ExecutionId("e1"))
        container.delete_item.assert_awaited_once()

    async def test_list_with_filters(self) -> None:
        container = _mock_container()
        repo = CosmosWorkflowExecutionRepository(container)

        with patch(
            "src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_execution_repository.paginate",
            return_value=([self._exec_doc()], None),
        ) as mock_paginate:
            results, _token = await repo.list_executions(workflow_id=SpecId("w1"), status=RunStatus.IDLE)

        assert len(results) == 1
        query = mock_paginate.call_args[0][1]
        assert "workflowId" in query
        assert "status" in query

    async def test_get_with_optional_fields(self) -> None:
        container = _mock_container()
        doc = self._exec_doc()
        doc["sessionId"] = "sess-1"
        doc["variables"] = {"key": "val"}
        doc["completedAt"] = NOW_ISO
        container.read_item.return_value = doc
        repo = CosmosWorkflowExecutionRepository(container)

        result = await repo.get(ExecutionId("e1"))
        assert result.session_id == "sess-1"
        assert result.variables == {"key": "val"}
        assert result.completed_at is not None


class TestCosmosWorkflowExecutionStepRepositoryExtended:
    def _step_doc(self) -> dict[str, Any]:
        return {
            "id": "se1",
            "workflowExecutionId": "e1",
            "stepId": "s1",
            "stepName": "Step 1",
            "stepType": "agent",
            "status": "idle",
            "attemptCount": 0,
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_create(self) -> None:
        container = _mock_container()
        container.create_item.return_value = self._step_doc()
        repo = CosmosWorkflowExecutionStepRepository(container)

        step = WorkflowExecutionStep(
            step_execution_id=StepId("se1"),
            workflow_execution_id=ExecutionId("e1"),
            step_id="s1",
            step_name="Step 1",
            step_type=StepType.AGENT,
            status=StepStatus.IDLE,
            attempt_count=0,
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(step)
        assert result.step_execution_id == "se1"

    async def test_list_by_execution(self) -> None:
        container = _mock_container()
        repo = CosmosWorkflowExecutionStepRepository(container)

        with patch(
            "src.platform.infrastructure.db.cosmos.repositories.cosmos_workflow_execution_step_repository.paginate",
            return_value=([self._step_doc()], None),
        ):
            results, _token = await repo.list_by_execution(ExecutionId("e1"))

        assert len(results) == 1
        assert results[0].step_execution_id == "se1"


class TestCosmosSessionRepositoryExtended:
    def _session_doc(self) -> dict[str, Any]:
        return {
            "id": "sess1",
            "sessionId": "sess1",
            "userId": "u1",
            "status": "active",
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_create(self) -> None:
        container = _mock_container()
        container.create_item.return_value = self._session_doc()
        repo = CosmosSessionRepository(container)

        session = Session(
            session_id=SessionId("sess1"),
            user_id=UserId("u1"),
            status=SessionStatus.ACTIVE,
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(session)
        assert result.session_id == "sess1"

    async def test_delete(self) -> None:
        container = _mock_container()
        repo = CosmosSessionRepository(container)
        await repo.delete(SessionId("sess1"))
        container.delete_item.assert_awaited_once()

    async def test_list_by_user(self) -> None:
        container = _mock_container()
        repo = CosmosSessionRepository(container)

        with patch(
            "src.platform.infrastructure.db.cosmos.repositories.cosmos_session_repository.paginate",
            return_value=([self._session_doc()], "next"),
        ):
            results, token = await repo.list_by_user(UserId("u1"))

        assert len(results) == 1
        assert results[0].session_id == "sess1"
        assert token == "next"

    async def test_get_with_optional_fields(self) -> None:
        container = _mock_container()
        doc = self._session_doc()
        doc["title"] = "Test Session"
        doc["workflowExecutionId"] = "e1"
        doc["ttl"] = 3600
        container.read_item.return_value = doc
        repo = CosmosSessionRepository(container)

        result = await repo.get(SessionId("sess1"))
        assert result.title == "Test Session"
        assert result.workflow_execution_id == "e1"
        assert result.ttl == 3600


class TestCosmosUserRepositoryExtended:
    def _user_doc(self) -> dict[str, Any]:
        return {
            "id": "u1",
            "displayName": "Test User",
            "role": "operator",
            "status": "active",
            "schemaVersion": 1,
            "createdAt": NOW_ISO,
            "updatedAt": NOW_ISO,
        }

    async def test_create(self) -> None:
        container = _mock_container()
        container.create_item.return_value = self._user_doc()
        repo = CosmosUserRepository(container)

        user = User(
            user_id=UserId("u1"),
            display_name="Test User",
            role=UserRole.OPERATOR,
            status=UserStatus.ACTIVE,
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        result = await repo.create(user)
        assert result.user_id == "u1"

    async def test_get_with_optional_fields(self) -> None:
        container = _mock_container()
        doc = self._user_doc()
        doc["email"] = "test@example.com"
        doc["preferences"] = {"lang": "ja"}
        doc["lastLoginAt"] = NOW_ISO
        container.read_item.return_value = doc
        repo = CosmosUserRepository(container)

        result = await repo.get(UserId("u1"))
        assert result.email == "test@example.com"
        assert result.preferences == {"lang": "ja"}
        assert result.last_login_at is not None
