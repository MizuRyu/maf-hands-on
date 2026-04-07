"""Compaction サンプル。長い会話でコンテキストウィンドウを管理する戦略。"""

from __future__ import annotations

import asyncio
import logging

from agent_framework import (
    Agent,
    AgentSession,
    BaseChatClient,
    InMemoryHistoryProvider,
    SlidingWindowStrategy,
    tool,
)

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)


@tool
def lookup(topic: str) -> str:
    """トピックについて調べる(モック)。"""
    return f"{topic}に関する詳細情報: これはモックデータです。実際にはDBやAPIから取得します。"


def _build_agent_with_sliding_window(client: BaseChatClient) -> Agent:
    """SlidingWindowStrategy: 直近N組のメッセージのみ保持。"""
    return Agent(
        client=client,
        name="compaction-sliding-window",
        instructions="日本語で回答。過去の会話を参照して回答してください。",
        tools=[lookup],
        context_providers=[InMemoryHistoryProvider()],
        compaction_strategy=SlidingWindowStrategy(
            keep_last_groups=5,  # 直近5グループのみ保持
            preserve_system=True,  # systemメッセージは常に保持
        ),
    )


def _build_agent_with_summarization(client: BaseChatClient) -> Agent:
    """SummarizationStrategy: 古い会話をLLMで要約して圧縮。"""
    from agent_framework import SummarizationStrategy

    return Agent(
        client=client,
        name="compaction-summarization",
        instructions="日本語で回答。会話の文脈を覚えて回答してください。",
        context_providers=[InMemoryHistoryProvider()],
        compaction_strategy=SummarizationStrategy(
            client=client,  # 要約生成に使うLLMクライアント
            target_count=4,  # 要約後に残す非systemメッセージ数
            threshold=2,  # target_count + threshold を超えたらトリガー
        ),
    )


async def demo_sliding_window() -> None:
    """SlidingWindow のデモ: 古い会話が自動的に除外される。"""
    logger.info("=== SlidingWindow Compaction ===")
    client = get_aoai_client()
    agent = _build_agent_with_sliding_window(client)
    session = AgentSession()

    messages = [
        "私の名前は田中です",
        "今日は天気がいいですね",
        "pythonについて調べて",
        "TypeScriptについても調べて",
        "Rustについても調べて",
        "Goについても調べて",
        "最初に私が言った名前は何でしたか?",  # 古い会話は除外されている可能性
    ]

    for msg in messages:
        logger.info("User: %s", msg)
        result = await agent.run(msg, session=session)
        logger.info("Agent: %s\n", result.text[:100])


async def demo_summarization() -> None:
    """Summarization のデモ: 古い会話がLLMで要約される。"""
    logger.info("=== Summarization Compaction ===")
    client = get_aoai_client()
    agent = _build_agent_with_summarization(client)
    session = AgentSession()

    messages = [
        "私の名前は田中太郎です。東京在住です。",
        "趣味はプログラミングと読書です。",
        "最近はRustを勉強しています。",
        "仕事ではPythonを使っています。",
        "MAFフレームワークの調査中です。",
        "来月から新しいプロジェクトが始まります。",
        "私のプロフィールをまとめてください。",  # 要約されたコンテキストから回答
    ]

    for msg in messages:
        logger.info("User: %s", msg)
        result = await agent.run(msg, session=session)
        logger.info("Agent: %s\n", result.text[:100])


async def main() -> None:
    # await demo_sliding_window()
    await demo_summarization()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
