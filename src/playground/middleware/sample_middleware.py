"""Middleware サンプル。Agent / Function / Chat の3層ミドルウェア。"""

from __future__ import annotations

import asyncio
import logging
import time

from agent_framework import Agent, BaseChatClient, agent_middleware, function_middleware, tool

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)


# --- Agent Middleware: 実行全体のログ ---


@agent_middleware
async def logging_middleware(context, call_next):
    """agent.run() の前後でログを出力する。"""
    agent_name = context.agent.name
    logger.info("[middleware] Agent '%s' run started", agent_name)
    start = time.perf_counter()
    result = await call_next(context)
    elapsed = time.perf_counter() - start
    logger.info("[middleware] Agent '%s' run completed in %.2fs", agent_name, elapsed)
    return result


# --- Function Middleware: ツール実行のインターセプト ---


@function_middleware
async def tool_logging_middleware(context, call_next):
    """ツール呼び出しの前後でログを出力する。"""
    tool_name = context.function.name
    logger.info("[middleware] Tool '%s' called with args: %s", tool_name, context.arguments)
    result = await call_next(context)
    logger.info("[middleware] Tool '%s' returned: %s", tool_name, context.result)
    return result


@tool
def greet(name: str) -> str:
    """挨拶を返す。"""
    return f"こんにちは、{name}さん!"


def get_middleware_agent(client: BaseChatClient) -> Agent:
    """ミドルウェア付きエージェントを生成する。"""
    return Agent(
        client=client,
        name="middleware-agent",
        description="ミドルウェアのデモ用 Agent",
        instructions="あなたはツールを使って回答するアシスタントです。日本語で回答してください。",
        tools=[greet],
        middleware=[logging_middleware, tool_logging_middleware],
    )


async def main() -> None:
    client = get_aoai_client()
    agent = get_middleware_agent(client)
    result = await agent.run("田中さんに挨拶して")
    logger.info("Response: %s", result.text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
