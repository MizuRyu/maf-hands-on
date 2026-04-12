"""バリデーション Executor。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.workflows.approval_workflow.contracts import (
    ApprovalRequest,
    ApprovalResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)

MAX_AMOUNT = 10_000_000
VALID_CATEGORIES = {"交通費", "交際費", "備品購入", "通信費", "その他"}


class RequestValidator(Executor):
    """申請内容のバリデーションを行う。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ApprovalRequest,
        ctx: WorkflowContext[ValidationResult, ApprovalResult],
    ) -> None:
        errors: list[str] = []

        if not message.request_id:
            errors.append("申請IDが空です")
        if not message.requester:
            errors.append("申請者が空です")
        if message.amount <= 0:
            errors.append("金額は正の値である必要があります")
        if message.amount > MAX_AMOUNT:
            errors.append(f"金額が上限 {MAX_AMOUNT:,}円 を超過しています")
        if message.category not in VALID_CATEGORIES:
            errors.append(f"不明なカテゴリ: {message.category}")

        if errors:
            logger.warning("[RequestValidator] バリデーションエラー: %s", errors)
            await ctx.yield_output(
                ApprovalResult(
                    request_id=message.request_id,
                    approved=False,
                    reviewer="system",
                    comment=f"バリデーションエラー: {'; '.join(errors)}",
                )
            )
            return

        result = ValidationResult(
            request_id=message.request_id,
            is_valid=True,
            original_request=message,
        )
        logger.info("[RequestValidator] バリデーションOK: %s", message.request_id)
        await ctx.send_message(result)
