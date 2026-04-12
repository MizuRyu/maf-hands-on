"""通知 Executor。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.workflows.approval_workflow.contracts import ApprovalResult

logger = logging.getLogger(__name__)


class Notifier(Executor):
    """承認結果を通知する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ApprovalResult,
        ctx: WorkflowContext[ApprovalResult, ApprovalResult],
    ) -> None:
        status = "承認" if message.approved else "却下"
        logger.info(
            "[Notifier] 通知: request_id=%s, status=%s, reviewer=%s",
            message.request_id,
            status,
            message.reviewer,
        )

        import dataclasses

        notified = dataclasses.replace(message, notification_sent=True)
        await ctx.yield_output(notified)
