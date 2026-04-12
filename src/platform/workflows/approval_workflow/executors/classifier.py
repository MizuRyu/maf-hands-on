"""リスク分類 Executor。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.workflows.approval_workflow.contracts import (
    ClassificationResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)

AUTO_APPROVE_THRESHOLD = 5000
HIGH_RISK_THRESHOLD = 100_000
HIGH_RISK_CATEGORIES = {"交際費"}


class RiskClassifier(Executor):
    """申請のリスクレベルを分類する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ValidationResult,
        ctx: WorkflowContext[ClassificationResult],
    ) -> None:
        request = message.original_request
        assert request is not None

        if request.amount <= AUTO_APPROVE_THRESHOLD:
            risk_level = "low"
            auto_approve = True
            reason = f"金額 {request.amount:,}円 が自動承認閾値以下"
        elif request.amount > HIGH_RISK_THRESHOLD or request.category in HIGH_RISK_CATEGORIES:
            risk_level = "high"
            auto_approve = False
            reason = f"高リスク: 金額 {request.amount:,}円, カテゴリ {request.category}"
        else:
            risk_level = "medium"
            auto_approve = False
            reason = f"要承認: 金額 {request.amount:,}円"

        result = ClassificationResult(
            request_id=request.request_id,
            risk_level=risk_level,
            auto_approve=auto_approve,
            reason=reason,
            original_request=request,
        )
        logger.info(
            "[RiskClassifier] %s: risk=%s, auto_approve=%s",
            request.request_id,
            risk_level,
            auto_approve,
        )
        await ctx.send_message(result)
