"""Evaluation サンプル。ビルトインチェックとカスタム @evaluator。"""

from __future__ import annotations

import asyncio
import logging

from agent_framework import Agent, BaseChatClient, evaluate_agent, evaluator, keyword_check, tool, tool_called_check

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)


# --- カスタム評価関数 ---


@evaluator
def is_japanese(response: str) -> bool:
    """レスポンスに日本語が含まれているか。"""
    return any("\u3040" <= c <= "\u9fff" for c in response)


@evaluator
def is_concise(response: str) -> bool:
    """レスポンスが500文字以内か。"""
    return len(response) <= 500


# --- テスト用ツール ---


@tool
def get_weather(city: str) -> str:
    """指定都市の天気を返す(モック)。"""
    return f"{city}: 晴れ 22°C"


def _build_agent(client: BaseChatClient) -> Agent:
    return Agent(
        client=client,
        name="eval-target-agent",
        instructions="日本語で簡潔に回答してください。天気を聞かれたらツールを使ってください。",
        tools=[get_weather],
    )


async def main() -> None:
    client = get_aoai_client()
    agent = _build_agent(client)

    # --- 基本評価: ビルトインチェック ---
    logger.info("=== ビルトインチェック ===")
    results = await evaluate_agent(
        agent=agent,
        queries=["東京の天気は?", "大阪の天気を教えて"],
        evaluators=[
            keyword_check("晴れ"),
            tool_called_check("get_weather"),
            is_japanese,
            is_concise,
        ],
        eval_name="basic-eval",
    )

    for eval_result in results:
        logger.info("Eval: %s", eval_result.eval_id)
        logger.info("  passed=%d, failed=%d, total=%d", eval_result.passed, eval_result.failed, eval_result.total)
        for check_name, counts in eval_result.per_evaluator.items():
            logger.info("  [%s] passed=%d, failed=%d", check_name, counts.get("passed", 0), counts.get("failed", 0))

    # --- 繰り返し評価: num_repetitions ---
    logger.info("\n=== 繰り返し評価 (3回) ===")
    results = await evaluate_agent(
        agent=agent,
        queries=["こんにちは"],
        evaluators=[is_japanese, is_concise],
        num_repetitions=3,
    )

    for eval_result in results:
        logger.info("Eval: %s — all_passed=%s", eval_result.eval_id, eval_result.all_passed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
