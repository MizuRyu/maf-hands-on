"""ドメイン共通型のテスト。"""

from __future__ import annotations

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
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.platform.domain.common.types import (
    CheckpointId,
    ExecutionId,
    SessionId,
    SpecId,
    StepId,
    UserId,
)


class TestNewTypes:
    def test_spec_id_is_str(self) -> None:
        sid = SpecId("abc-123")
        assert isinstance(sid, str)
        assert sid == "abc-123"

    def test_execution_id(self) -> None:
        assert ExecutionId("e1") == "e1"

    def test_step_id(self) -> None:
        assert StepId("s1") == "s1"

    def test_session_id(self) -> None:
        assert SessionId("sess1") == "sess1"

    def test_user_id(self) -> None:
        assert UserId("u1") == "u1"

    def test_checkpoint_id(self) -> None:
        assert CheckpointId("cp1") == "cp1"


class TestEnums:
    def test_spec_status_values(self) -> None:
        assert SpecStatus.DRAFT == "draft"
        assert SpecStatus.ACTIVE == "active"
        assert SpecStatus.ARCHIVED == "archived"

    def test_run_status_values(self) -> None:
        assert RunStatus.IDLE == "idle"
        assert RunStatus.RUNNING == "running"
        assert RunStatus.WAITING == "waiting"
        assert RunStatus.COMPLETED == "completed"
        assert RunStatus.FAILED == "failed"
        assert RunStatus.CANCELLED == "cancelled"
        assert RunStatus.SUSPENDED == "suspended"
        assert RunStatus.TIMED_OUT == "timed_out"

    def test_step_type_values(self) -> None:
        assert StepType.AGENT == "agent"
        assert StepType.HUMAN == "human"
        assert StepType.LOGIC == "logic"

    def test_tool_type_values(self) -> None:
        assert ToolType.FUNCTION == "function"
        assert ToolType.MCP == "mcp"
        assert ToolType.AGENT_AS_TOOL == "agent_as_tool"
        assert ToolType.HOSTED == "hosted"

    def test_foundry_deployment_type_values(self) -> None:
        assert FoundryDeploymentType.PROMPT == "prompt"
        assert FoundryDeploymentType.HOSTED == "hosted"
        assert FoundryDeploymentType.WORKFLOW == "workflow"
        assert FoundryDeploymentType.NONE == "none"

    def test_session_status_values(self) -> None:
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.CLOSED == "closed"
        assert SessionStatus.EXPIRED == "expired"

    def test_user_role_values(self) -> None:
        assert UserRole.ADMIN == "admin"
        assert UserRole.OPERATOR == "operator"
        assert UserRole.VIEWER == "viewer"

    def test_user_status_values(self) -> None:
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.SUSPENDED == "suspended"
        assert UserStatus.DELETED == "deleted"

    def test_step_status_values(self) -> None:
        assert StepStatus.IDLE == "idle"
        assert StepStatus.RUNNING == "running"
        assert StepStatus.WAITING == "waiting"
        assert StepStatus.COMPLETED == "completed"
        assert StepStatus.FAILED == "failed"
        assert StepStatus.SKIPPED == "skipped"


class TestExceptions:
    def test_not_found_error_is_domain_error(self) -> None:
        err = NotFoundError("AgentSpec", "abc")
        assert isinstance(err, DomainError)
        assert "AgentSpec" in str(err)
        assert "abc" in str(err)

    def test_conflict_error(self) -> None:
        err = ConflictError("User", "u1")
        assert isinstance(err, DomainError)
        assert err.entity_type == "User"

    def test_concurrency_error(self) -> None:
        err = ConcurrencyError("Session", "s1")
        assert isinstance(err, DomainError)

    def test_validation_error(self) -> None:
        err = ValidationError("Invalid input")
        assert isinstance(err, DomainError)
        assert "Invalid input" in str(err)
