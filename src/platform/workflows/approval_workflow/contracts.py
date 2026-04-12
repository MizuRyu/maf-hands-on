"""申請承認ワークフローのメッセージ型。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApprovalRequest:
    """ワークフローへの入力: 承認申請。"""

    request_id: str
    requester: str
    category: str
    amount: int
    description: str
    items: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationResult:
    """バリデーション結果。"""

    request_id: str
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    original_request: ApprovalRequest | None = None


@dataclass
class ClassificationResult:
    """Agent 分類結果。"""

    request_id: str
    risk_level: str  # "low", "medium", "high"
    auto_approve: bool
    reason: str
    original_request: ApprovalRequest | None = None


@dataclass
class ReviewRequest:
    """HITL 承認リクエスト。"""

    request_id: str
    requester: str
    category: str
    amount: int
    risk_level: str
    reason: str


@dataclass
class ReviewResponse:
    """HITL 承認レスポンス。"""

    approved: bool
    reviewer: str
    comment: str = ""


@dataclass
class ApprovalResult:
    """最終承認結果。"""

    request_id: str
    approved: bool
    reviewer: str
    comment: str
    notification_sent: bool = False
