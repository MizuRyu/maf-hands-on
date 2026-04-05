"""サンプル Agent。playground での MAF 動作確認用。"""

from __future__ import annotations

import asyncio
import logging

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)

SAMPLE_INSTRUCTIONS = """
あなたは親切なアシスタントです。
ユーザーの質問に簡潔に日本語で回答してください。
""".strip()


def get_sample_agent(client: OpenAIChatClient) -> Agent:
    """動作確認用のシンプルな Agent を生成する。"""
    return Agent(
        client=client,
        name="sample-agent",
        description="動作確認用サンプル Agent",
        instructions=SAMPLE_INSTRUCTIONS,
    )


async def main() -> None:
    """サンプル Agent を実行する。"""
    client = get_aoai_client()
    agent = get_sample_agent(client)
    result = await agent.run("こんにちは。あなたは何ができますか?")
    logger.info("Agent response: %s", result.text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
