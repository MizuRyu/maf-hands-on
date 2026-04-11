"""テキスト正規化・キーワード抽出 Executor。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.catalog.workflows.text_pipeline.contracts import ProcessedData, ValidatedInput

logger = logging.getLogger(__name__)


class Processor(Executor):
    """テキストの正規化とキーワード抽出を行う。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ValidatedInput,
        ctx: WorkflowContext[ProcessedData],
    ) -> None:
        normalized = " ".join(message.text.split())
        # 4 文字以上の単語をキーワードとして抽出 (簡易実装)
        keywords = sorted({w for w in normalized.split() if len(w) >= 4})

        processed = ProcessedData(
            original_text=message.text,
            normalized_text=normalized,
            word_count=message.word_count,
            keywords=keywords[:10],
        )
        logger.info("[Processor] キーワード %d 件抽出", len(processed.keywords))
        await ctx.send_message(processed)
