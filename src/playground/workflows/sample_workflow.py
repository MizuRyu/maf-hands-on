"""Workflow サンプル。WorkflowBuilder でグラフベースの処理パイプライン。"""

# NOTE: `from __future__ import annotations` は使わない。
# @handler がランタイムで型アノテーションを参照するため、文字列化すると動作しない。

import asyncio
import logging
from dataclasses import dataclass

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

logger = logging.getLogger(__name__)


# --- メッセージ型定義 ---


@dataclass
class RawInput:
    text: str


@dataclass
class Processed:
    text: str
    word_count: int


@dataclass
class Result:
    summary: str


# --- Executor 定義 ---


class Preprocessor(Executor):
    """入力テキストを前処理する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(self, message: RawInput, ctx: WorkflowContext[Processed, Result]) -> None:
        cleaned = message.text.strip()
        word_count = len(cleaned.split())
        logger.info("[Preprocessor] %d words", word_count)
        await ctx.send_message(Processed(text=cleaned, word_count=word_count))


class Analyzer(Executor):
    """テキストを分析して結果を出力する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(self, message: Processed, ctx: WorkflowContext[None, Result]) -> None:
        if len(message.text) > 50:
            summary = f"テキスト ({message.word_count}語): '{message.text[:50]}...'"
        else:
            summary = f"テキスト ({message.word_count}語): '{message.text}'"
        logger.info("[Analyzer] %s", summary)
        await ctx.yield_output(Result(summary=summary))


def build_sample_workflow():
    """サンプルワークフローを構築する。"""
    preprocessor = Preprocessor("preprocessor")
    analyzer = Analyzer("analyzer")
    return WorkflowBuilder(start_executor=preprocessor).add_edge(preprocessor, analyzer).build()


async def main() -> None:
    workflow = build_sample_workflow()

    inputs = [
        "Microsoft Agent Framework は Semantic Kernel と AutoGen の後継フレームワークです。",
        "ワークフローはグラフベースの実行エンジンで、Fan-out や Fan-in をサポートします。",
    ]

    for text in inputs:
        logger.info("--- Input: %s", text[:40])
        result = await workflow.run(RawInput(text=text))
        for output in result.get_outputs():
            logger.info("Output: %s\n", output.summary)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
