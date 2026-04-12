"""WorkflowSpec 関連の API スキーマ。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.platform.domain.common.enums import StepType


class WorkflowStepCreateRequest(BaseModel):
    """ワークフローステップの作成リクエスト。"""

    step_id: str = Field(min_length=1)
    step_name: str = Field(min_length=1)
    step_type: StepType
    order: int = Field(ge=0)


class WorkflowSpecCreateRequest(BaseModel):
    """WorkflowSpec 新規登録リクエスト。"""

    name: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    steps: list[WorkflowStepCreateRequest]
    description: str | None = None


class WorkflowSpecUpdateRequest(BaseModel):
    """WorkflowSpec 更新リクエスト。"""

    name: str | None = None
    steps: list[WorkflowStepCreateRequest] | None = None
    description: str | None = None


class WorkflowStepResponseData(BaseModel):
    """ワークフローステップのレスポンス。"""

    step_id: str
    step_name: str
    step_type: StepType
    order: int


class WorkflowSpecResponseData(BaseModel):
    """WorkflowSpec レスポンス。"""

    spec_id: str
    name: str
    version: int
    steps: dict[str, WorkflowStepResponseData]
    schema_version: int
    created_at: datetime
    updated_at: datetime
    description: str | None = None
