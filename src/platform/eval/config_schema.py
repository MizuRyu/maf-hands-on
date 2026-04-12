"""Eval 設定スキーマの定義。

eval_config.yaml を Pydantic モデルとしてロードする。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class EvaluatorConfig(BaseModel):
    """個別の evaluator 設定。"""

    type: str
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    params: dict[str, Any] = Field(default_factory=dict)


class EvalConfig(BaseModel):
    """Eval 設定全体。"""

    evaluators: list[EvaluatorConfig] = Field(min_length=1)
    dataset: str = Field(min_length=1)
    agent_name: str | None = None
    num_repetitions: int = Field(default=1, ge=1)


def load_eval_config(path: Path) -> EvalConfig:
    """eval_config.yaml をロードする。"""
    with path.open() as f:
        data = yaml.safe_load(f)
    if not data:
        msg = f"Empty eval config: {path}"
        raise ValueError(msg)
    return EvalConfig(**data)
