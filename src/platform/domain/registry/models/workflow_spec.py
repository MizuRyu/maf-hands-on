"""ワークフロー定義のドメインモデル。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.platform.domain.common.enums import StepType
from src.platform.domain.common.types import SpecId


@dataclass(frozen=True)
class WorkflowStepDefinition:
    """ワークフロー内の個別ステップ定義。"""

    step_id: str
    step_name: str
    step_type: StepType
    depends_on: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkflowSpec:
    """ワークフロー定義。ステップ構成を DAG で保持する。"""

    spec_id: SpecId
    name: str
    version: int
    steps: dict[str, WorkflowStepDefinition]
    schema_version: int
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    parallel_error_policy: str = "fail_fast"
