"""ToolSpec 関連の API スキーマ。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.platform.domain.common.enums import SpecStatus, ToolType


class ToolSpecCreateRequest(BaseModel):
    """ToolSpec 新規登録リクエスト。"""

    name: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    description: str = Field(min_length=1)
    tool_type: ToolType
    implementation: dict[str, Any]
    parameters: dict[str, Any] | None = None


class ToolSpecUpdateRequest(BaseModel):
    """ToolSpec 更新リクエスト。"""

    name: str | None = None
    description: str | None = None
    implementation: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None


class ToolSpecResponseData(BaseModel):
    """ToolSpec レスポンス。"""

    spec_id: str
    name: str
    version: int
    description: str
    tool_type: ToolType
    implementation: dict[str, Any]
    status: SpecStatus
    created_by: str
    schema_version: int
    created_at: datetime
    updated_at: datetime
    parameters: dict[str, Any] | None = None
