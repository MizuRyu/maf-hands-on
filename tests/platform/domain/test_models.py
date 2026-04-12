"""ドメインモデル（specs / runs / sessions / users）のテスト。"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

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
from src.platform.domain.common.types import (
    ExecutionId,
    SessionId,
    SpecId,
    StepId,
    UserId,
)
from src.platform.domain.execution.models.workflow_run import WorkflowExecution
from src.platform.domain.execution.models.workflow_step import (
    StepError,
    WorkflowExecutionStep,
)
from src.platform.domain.registry.models.agent_spec import AgentSpec
from src.platform.domain.registry.models.tool_spec import ToolSpec
from src.platform.domain.registry.models.workflow_spec import (
    WorkflowSpec,
    WorkflowStepDefinition,
)
from src.platform.domain.sessions.models.session import Session
from src.platform.domain.users.models.user import User

NOW = datetime(2024, 1, 1, tzinfo=UTC)
LATER = datetime(2024, 6, 1, tzinfo=UTC)


class TestAgentSpec:
    def _make(self, **overrides: object) -> AgentSpec:
        defaults = {
            "spec_id": SpecId("a1"),
            "name": "test-agent",
            "version": "1.0.0",
            "model_id": "gpt-5-nano",
            "instructions": "You are a helpful assistant.",
            "status": SpecStatus.DRAFT,
            "created_by": UserId("u1"),
            "schema_version": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(overrides)
        return AgentSpec(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        spec = self._make()
        assert spec.spec_id == "a1"
        assert spec.name == "test-agent"

    def test_frozen(self) -> None:
        spec = self._make()
        with pytest.raises(FrozenInstanceError):
            spec.name = "changed"  # type: ignore[misc]

    def test_with_status(self) -> None:
        spec = self._make()
        updated = spec.with_status(SpecStatus.ACTIVE, LATER)
        assert updated.status == SpecStatus.ACTIVE
        assert updated.updated_at == LATER
        assert spec.status == SpecStatus.DRAFT  # 元は不変
        assert spec.updated_at == NOW  # 元の updated_at も不変

    def test_optional_fields(self) -> None:
        spec = self._make(
            description="desc",
            tool_ids=["t1", "t2"],
            foundry_agent_name="my-agent",
            foundry_deployment_type=FoundryDeploymentType.HOSTED,
        )
        assert spec.description == "desc"
        assert spec.tool_ids == ["t1", "t2"]
        assert spec.foundry_deployment_type == FoundryDeploymentType.HOSTED


class TestToolSpec:
    def _make(self, **overrides: object) -> ToolSpec:
        defaults = {
            "spec_id": SpecId("t1"),
            "name": "my-tool",
            "version": "1.0.0",
            "description": "A test tool",
            "tool_type": ToolType.FUNCTION,
            "implementation": {"module": "tools.my_tool"},
            "status": SpecStatus.ACTIVE,
            "created_by": UserId("u1"),
            "schema_version": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(overrides)
        return ToolSpec(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        tool = self._make()
        assert tool.tool_type == ToolType.FUNCTION

    def test_with_status(self) -> None:
        tool = self._make()
        archived = tool.with_status(SpecStatus.ARCHIVED, LATER)
        assert archived.status == SpecStatus.ARCHIVED
        assert archived.updated_at == LATER
        assert tool.status == SpecStatus.ACTIVE  # 元は不変


class TestWorkflowSpec:
    def test_create(self) -> None:
        step = WorkflowStepDefinition(step_id="s1", step_name="Step 1", step_type=StepType.AGENT, depends_on=[])
        spec = WorkflowSpec(
            spec_id=SpecId("w1"),
            name="test-wf",
            version=1,
            steps={"step1": step},
            schema_version=1,
            created_at=NOW,
            updated_at=NOW,
        )
        assert spec.name == "test-wf"
        assert "step1" in spec.steps


class TestWorkflowExecution:
    def _make(self, **overrides: object) -> WorkflowExecution:
        defaults = {
            "execution_id": ExecutionId("e1"),
            "workflow_id": SpecId("w1"),
            "workflow_name": "test-wf",
            "workflow_version": "1.0.0",
            "status": RunStatus.IDLE,
            "schema_version": 1,
            "started_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(overrides)
        return WorkflowExecution(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        exe = self._make()
        assert exe.status == RunStatus.IDLE

    def test_with_status(self) -> None:
        exe = self._make()
        running = exe.with_status(RunStatus.RUNNING, LATER)
        assert running.status == RunStatus.RUNNING
        assert running.updated_at == LATER
        assert exe.status == RunStatus.IDLE  # 元は不変

    def test_optional_fields(self) -> None:
        exe = self._make(
            session_id=SessionId("sess-1"),
            variables={"key": "val"},
            active_step_ids=["step-1"],
            completed_at=LATER,
        )
        assert exe.session_id == "sess-1"
        assert exe.variables == {"key": "val"}
        assert exe.completed_at == LATER


class TestWorkflowExecutionStep:
    def _make(self, **overrides: object) -> WorkflowExecutionStep:
        defaults = {
            "step_execution_id": StepId("se1"),
            "workflow_execution_id": ExecutionId("e1"),
            "step_id": "s1",
            "step_name": "Step 1",
            "step_type": StepType.AGENT,
            "status": StepStatus.IDLE,
            "attempt_count": 0,
            "schema_version": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(overrides)
        return WorkflowExecutionStep(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        step = self._make()
        assert step.step_type == StepType.AGENT

    def test_with_status(self) -> None:
        step = self._make()
        running = step.with_status(StepStatus.RUNNING, LATER)
        assert running.status == StepStatus.RUNNING
        assert running.updated_at == LATER
        assert step.status == StepStatus.IDLE  # 元は不変

    def test_step_error_with_all_fields(self) -> None:
        err = StepError(
            code="E001",
            message="Something failed",
            detail="stack trace here",
            occurred_at=NOW,
        )
        assert err.code == "E001"
        assert err.detail == "stack trace here"
        assert err.occurred_at == NOW

    def test_step_error(self) -> None:
        err = StepError(code="E001", message="Something failed")
        assert err.code == "E001"
        assert err.detail is None


class TestSession:
    def _make(self, **overrides: object) -> Session:
        defaults = {
            "session_id": SessionId("sess1"),
            "user_id": UserId("u1"),
            "agent_id": SpecId("a1"),
            "status": SessionStatus.ACTIVE,
            "schema_version": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(overrides)
        return Session(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        session = self._make()
        assert session.status == SessionStatus.ACTIVE
        assert session.agent_id == "a1"

    def test_with_status(self) -> None:
        session = self._make()
        closed = session.with_status(SessionStatus.CLOSED, LATER)
        assert closed.status == SessionStatus.CLOSED
        assert closed.updated_at == LATER
        assert session.status == SessionStatus.ACTIVE  # 元は不変

    def test_optional_fields(self) -> None:
        session = self._make(
            title="My Session",
            ttl=3600,
        )
        assert session.title == "My Session"
        assert session.ttl == 3600


class TestUser:
    def _make(self, **overrides: object) -> User:
        defaults = {
            "user_id": UserId("u1"),
            "display_name": "Test User",
            "role": UserRole.OPERATOR,
            "status": UserStatus.ACTIVE,
            "schema_version": 1,
            "created_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(overrides)
        return User(**defaults)  # type: ignore[arg-type]

    def test_create(self) -> None:
        user = self._make()
        assert user.display_name == "Test User"

    def test_with_status(self) -> None:
        user = self._make()
        inactive = user.with_status(UserStatus.SUSPENDED, LATER)
        assert inactive.status == UserStatus.SUSPENDED
        assert inactive.updated_at == LATER
        assert user.status == UserStatus.ACTIVE  # 元は不変

    def test_optional_fields(self) -> None:
        user = self._make(
            email="test@example.com",
            preferences={"lang": "ja"},
            last_login_at=LATER,
        )
        assert user.email == "test@example.com"
        assert user.preferences == {"lang": "ja"}
        assert user.last_login_at == LATER
