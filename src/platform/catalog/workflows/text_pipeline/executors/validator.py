"""入力バリデーション Executor。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import logging

from agent_framework import Executor, WorkflowContext, handler

from src.platform.catalog.workflows.text_pipeline.contracts import (
    FormattedOutput,
    UserRequest,
    ValidatedInput,
)

logger = logging.getLogger(__name__)


class InputValidator(Executor):
    """空文字・長さ超過を検出し、正常な入力のみ後段に渡す。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: UserRequest,
        ctx: WorkflowContext[ValidatedInput, FormattedOutput],
    ) -> None:
        text = message.text.strip()

        if not text:
            logger.warning("[InputValidator] 空の入力を検出 — スキップ")
            await ctx.yield_output(FormattedOutput(report="エラー: 入力が空です。"))
            return

        if len(text) > message.max_length:
            logger.warning(
                "[InputValidator] 入力が上限 %d 文字を超過 (%d 文字)",
                message.max_length,
                len(text),
            )
            text = text[: message.max_length]

        words = text.split()
        validated = ValidatedInput(
            text=text,
            char_count=len(text),
            word_count=len(words),
        )
        logger.info("[InputValidator] OK — %d 文字, %d 語", validated.char_count, validated.word_count)
        await ctx.send_message(validated)
