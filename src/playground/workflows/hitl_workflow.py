"""HITL (Human-in-the-Loop) Workflow サンプル。

ワークフロー実行中にユーザー承認を要求し、一時停止→再開する。
LLM 不要。make playground m=hitl で実行可能。
"""

# NOTE: `from __future__ import annotations` は使わない。
# @handler / @response_handler がランタイムで型アノテーションを参照するため。

import asyncio
import logging
from dataclasses import dataclass

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler
from agent_framework._workflows._request_info_mixin import response_handler

logger = logging.getLogger(__name__)


# --- メッセージ型定義 ---


@dataclass
class Order:
    item: str
    quantity: int
    price: int


@dataclass
class ApprovalRequest:
    order: Order
    reason: str


@dataclass
class OrderResult:
    status: str
    detail: str


# --- Executor 定義 ---


class OrderProcessor(Executor):
    """注文を受け付けて承認を要求する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(self, message: Order, ctx: WorkflowContext[Order, OrderResult]) -> None:
        total = message.quantity * message.price
        logger.info(
            "[OrderProcessor] 注文受付: %s x%d = %d円",
            message.item,
            message.quantity,
            total,
        )

        if total >= 10000:
            logger.info("[OrderProcessor] 高額注文のため承認を要求します")
            await ctx.request_info(
                ApprovalRequest(order=message, reason=f"合計 {total}円 (10,000円以上)"),
                response_type=str,
                request_id="order-approval",
            )
        else:
            logger.info("[OrderProcessor] 自動承認 (10,000円未満)")
            await ctx.send_message(message)

    @response_handler  # type: ignore[reportArgumentType]
    async def handle_approval(
        self,
        original_request: ApprovalRequest,
        response: str,
        ctx: WorkflowContext[Order, OrderResult],
    ) -> None:
        """承認レスポンスを受け取って処理を続行する。"""
        if response.lower() in ("yes", "y", "ok", "approve"):
            logger.info("[OrderProcessor] 承認されました: %s", response)
            await ctx.send_message(original_request.order)
        else:
            logger.info("[OrderProcessor] 却下されました: %s", response)
            await ctx.yield_output(OrderResult(status="rejected", detail=f"却下理由: {response}"))


class OrderFulfiller(Executor):
    """承認済み注文を処理する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(self, message: Order, ctx: WorkflowContext[None, OrderResult]) -> None:
        total = message.quantity * message.price
        logger.info("[OrderFulfiller] 注文確定: %s x%d = %d円", message.item, message.quantity, total)
        await ctx.yield_output(
            OrderResult(status="completed", detail=f"{message.item} x{message.quantity} ({total}円) 処理完了")
        )


def build_hitl_workflow():
    """HITL ワークフローを構築する。"""
    processor = OrderProcessor("order-processor")
    fulfiller = OrderFulfiller("order-fulfiller")
    return WorkflowBuilder(start_executor=processor).add_edge(processor, fulfiller).build()


async def main() -> None:
    workflow = build_hitl_workflow()

    # --- ケース1: 低額注文 (自動承認) ---
    logger.info("=== ケース1: 低額注文 (自動承認) ===")
    result = await workflow.run(Order(item="ペン", quantity=2, price=200))
    for output in result.get_outputs():
        logger.info("Result: %s\n", output.detail)

    # --- ケース2: 高額注文 (HITL 承認フロー) ---
    logger.info("=== ケース2: 高額注文 (HITL 承認フロー) ===")
    result = await workflow.run(Order(item="モニター", quantity=3, price=50000))

    # ワークフローが一時停止。pending requests を確認
    pending = result.get_request_info_events()
    for event in pending:
        logger.info("Pending request: id=%s, type=%s", event.request_id, event.request_type)

    # ユーザーが承認
    logger.info("[User] 承認します → 'yes'")
    result = await workflow.run(responses={"order-approval": "yes"})
    for output in result.get_outputs():
        logger.info("Result: %s\n", output.detail)

    # --- ケース3: 高額注文 (却下) ---
    logger.info("=== ケース3: 高額注文 (却下) ===")
    result = await workflow.run(Order(item="サーバー", quantity=1, price=500000))

    logger.info("[User] 却下します → 'no: 予算超過'")
    result = await workflow.run(responses={"order-approval": "no: 予算超過"})
    for output in result.get_outputs():
        logger.info("Result: %s\n", output.detail)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
