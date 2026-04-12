"""ワークフロー定義。"""

from src.platform.workflows._types import WorkflowMeta
from src.platform.workflows.text_pipeline import build_text_pipeline_workflow

__all__ = ["WorkflowMeta", "build_text_pipeline_workflow"]
