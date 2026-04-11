"""レポート生成 Executor。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.catalog.workflows.text_pipeline.contracts import FormattedOutput, ProcessedData

logger = logging.getLogger(__name__)


class OutputFormatter(Executor):
    """加工済みデータからレポートを生成し最終出力する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ProcessedData,
        ctx: WorkflowContext[None, FormattedOutput],
    ) -> None:
        lines = [
            "=== 処理結果レポート ===",
            f"語数      : {message.word_count}",
            f"キーワード: {', '.join(message.keywords) if message.keywords else '(なし)'}",
            f"テキスト  : {message.normalized_text}",
            "========================",
        ]
        report = "\n".join(lines)
        logger.info("[OutputFormatter] レポート生成完了")
        await ctx.yield_output(FormattedOutput(report=report))
