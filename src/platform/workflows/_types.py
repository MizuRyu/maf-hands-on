"""Workflow 共通メタデータ型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkflowMeta:
    """Workflow のメタデータ。コード側の宣言用軽量型。"""

    name: str
    description: str
    version: int
    foundry_kind: str = "workflow"
    max_iterations: int = 10
    executor_ids: list[str] = field(default_factory=list)
