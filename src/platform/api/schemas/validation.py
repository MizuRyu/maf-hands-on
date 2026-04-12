"""バリデーション関連の API スキーマ。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """バリデーション問題。"""

    field: str
    message: str


class ValidationResultResponseData(BaseModel):
    """バリデーション結果。"""

    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
