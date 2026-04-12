"""ドメイン全体で使用する列挙型の定義。"""

from __future__ import annotations

from enum import StrEnum


class SpecStatus(StrEnum):
    """仕様（Agent / Tool / Workflow）の公開ステータス。"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RunStatus(StrEnum):
    """ワークフロー実行の業務ステータス。"""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class StepStatus(StrEnum):
    """ワークフロー実行ステップのステータス。"""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(StrEnum):
    """ワークフローステップの種別。"""

    AGENT = "agent"
    HUMAN = "human"
    LOGIC = "logic"


class AgentRunStatus(StrEnum):
    """Agent 実行のステータス。"""

    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(StrEnum):
    """チャットセッションのステータス。"""

    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class UserRole(StrEnum):
    """プラットフォームユーザーのロール。"""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class UserStatus(StrEnum):
    """プラットフォームユーザーのアカウント状態。"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class ToolType(StrEnum):
    """ツール仕様の種別。"""

    FUNCTION = "function"
    MCP = "mcp"
    AGENT_AS_TOOL = "agent_as_tool"
    HOSTED = "hosted"


class FoundryDeploymentType(StrEnum):
    """Foundry デプロイ種別。"""

    PROMPT = "prompt"
    HOSTED = "hosted"
    WORKFLOW = "workflow"
    NONE = "none"
