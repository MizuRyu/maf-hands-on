"""Streaming サンプル。ResponseStream でリアルタイム出力。"""

from __future__ import annotations

import asyncio
import logging
import sys

from agent_framework import Agent, BaseChatClient

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)


def _build_agent(client: BaseChatClient) -> Agent:
    return Agent(
        client=client,
        name="streaming-agent",
        instructions="日本語で詳しく回答してください。",
    )


async def main() -> None:
    client = get_aoai_client()
    agent = _build_agent(client)

    # --- ストリーミング出力 ---
    print("=== Streaming ===")
    stream = agent.run("Python の async/await を簡潔に説明して", stream=True)
    async for chunk in stream:
        if chunk.text:
            sys.stdout.write(chunk.text)
            sys.stdout.flush()
    print()

    # --- 最終レスポンスも取得 ---
    final = await stream.get_final_response()
    print(f"\n=== Final response length: {len(final.text)} chars ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
