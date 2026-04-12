"""承認 Executor (HITL)。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.workflows.approval_workflow.contracts import (
    ApprovalResult,
    ClassificationResult,
    ReviewRequest,
    ReviewResponse,
)

logger = logging.getLogger(__name__)


class Approver(Executor):
    """承認判定を行う。自動承認またはHITLで人間の判断を待つ。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ClassificationResult,
        ctx: WorkflowContext[ApprovalResult],
    ) -> None:
        request = message.original_request
        assert request is not None

        if message.auto_approve:
            logger.info("[Approver] 自動承認: %s", message.request_id)
            result = ApprovalResult(
                request_id=message.request_id,
                approved=True,
                reviewer="system",
                comment=f"自動承認 ({message.reason})",
            )
            await ctx.send_message(result)
            return

        # HITL: 人間の承認を待つ
        logger.info("[Approver] HITL承認待ち: %s (risk=%s)", message.request_id, message.risk_level)
        review_request = ReviewRequest(
            request_id=message.request_id,
            requester=request.requester,
            category=request.category,
            amount=request.amount,
            risk_level=message.risk_level,
            reason=message.reason,
        )

        review_response: ReviewResponse = await ctx.wait_for_external_input(review_request)  # type: ignore[attr-defined]

        result = ApprovalResult(
            request_id=message.request_id,
            approved=review_response.approved,
            reviewer=review_response.reviewer,
            comment=review_response.comment or ("承認" if review_response.approved else "却下"),
        )
        logger.info(
            "[Approver] HITL結果: %s approved=%s by %s",
            message.request_id,
            review_response.approved,
            review_response.reviewer,
        )
        await ctx.send_message(result)
