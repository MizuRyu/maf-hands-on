"""AgentSpec 関連の API スキーマ。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.platform.domain.common.enums import FoundryDeploymentType, SpecStatus


class AgentSpecCreateRequest(BaseModel):
    """AgentSpec 新規登録リクエスト。"""

    name: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    model_id: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    description: str | None = None
    tool_ids: list[str] = Field(default_factory=list)
    middleware_config: list[dict[str, Any]] = Field(default_factory=list)
    context_provider_config: list[dict[str, Any]] = Field(default_factory=list)
    response_format: dict[str, Any] | None = None
    foundry_deployment_type: FoundryDeploymentType | None = None


class AgentSpecUpdateRequest(BaseModel):
    """AgentSpec 更新リクエスト。"""

    name: str | None = None
    model_id: str | None = None
    instructions: str | None = None
    description: str | None = None
    tool_ids: list[str] | None = None
    middleware_config: list[dict[str, Any]] | None = None
    context_provider_config: list[dict[str, Any]] | None = None
    response_format: dict[str, Any] | None = None


class AgentSpecResponseData(BaseModel):
    """AgentSpec レスポンス。"""

    spec_id: str
    name: str
    version: int
    model_id: str
    instructions: str
    status: SpecStatus
    created_by: str
    schema_version: int
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    tool_ids: list[str] = Field(default_factory=list)
    middleware_config: list[dict[str, Any]] = Field(default_factory=list)
    context_provider_config: list[dict[str, Any]] = Field(default_factory=list)
    response_format: dict[str, Any] | None = None
    foundry_agent_name: str | None = None
    foundry_agent_version: str | None = None
    foundry_deployment_type: FoundryDeploymentType | None = None
    foundry_synced_at: datetime | None = None
