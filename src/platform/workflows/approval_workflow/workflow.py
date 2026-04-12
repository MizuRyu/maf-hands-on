"""申請承認ワークフローの定義。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import CheckpointStorage, Workflow, WorkflowBuilder

from src.platform.workflows._types import WorkflowMeta
from src.platform.workflows.approval_workflow.executors import (
    Approver,
    Notifier,
    RequestValidator,
    RiskClassifier,
)

logger = logging.getLogger(__name__)

WORKFLOW_META = WorkflowMeta(
    name="approval-workflow",
    description="申請承認ワークフロー (バリデーション → リスク分類 → 承認 → 通知)",
    version=1,
    executor_ids=["request-validator", "risk-classifier", "approver", "notifier"],
)


def build_approval_workflow(
    *,
    checkpoint_storage: CheckpointStorage | None = None,
) -> Workflow:
    """4 段階の承認ワークフローを構築する。"""
    validator = RequestValidator("request-validator")
    classifier = RiskClassifier("risk-classifier")
    approver = Approver("approver")
    notifier = Notifier("notifier")

    return (
        WorkflowBuilder(start_executor=validator, checkpoint_storage=checkpoint_storage)
        .add_edge(validator, classifier)
        .add_edge(classifier, approver)
        .add_edge(approver, notifier)
        .build()
    )
