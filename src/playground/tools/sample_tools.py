"""Tool 定義サンプル。@tool デコレータと FunctionTool の使い方。"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Annotated

from agent_framework import Agent, BaseChatClient, FunctionTool, tool

from src.playground.aoai_client import get_aoai_client

logger = logging.getLogger(__name__)


# --- 方法1: 素の Python 関数をそのまま渡す ---


def get_current_time() -> str:
    """現在時刻を取得する。"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- 方法2: @tool デコレータ ---


@tool(name="dice_roll", description="サイコロを振って結果を返す")
def roll_dice(
    sides: Annotated[int, "サイコロの面数"] = 6,
    count: Annotated[int, "振る回数"] = 1,
) -> str:
    results = [random.randint(1, sides) for _ in range(count)]
    return f"結果: {results} (合計: {sum(results)})"


# --- 方法3: FunctionTool で明示的に生成 ---


def _calculate(expression: str) -> str:
    """数式を計算する。"""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"{expression} = {result}"
    except Exception as e:
        return f"計算エラー: {e}"


calculate_tool = FunctionTool(
    func=_calculate,
    name="calculate",
    description="数式を計算する。四則演算に対応。",
)


def get_tool_agent(client: BaseChatClient) -> Agent:
    """ツール付きエージェントを生成する。"""
    return Agent(
        client=client,
        name="tool-agent",
        description="ツール使用のデモ用 Agent",
        instructions="あなたはツールを使って質問に回答するアシスタントです。日本語で回答してください。",
        tools=[get_current_time, roll_dice, calculate_tool],
    )


async def main() -> None:
    client = get_aoai_client()
    agent = get_tool_agent(client)

    queries = [
        "今何時?",
        "サイコロを3回振って",
        "123 * 456 を計算して",
    ]
    for q in queries:
        logger.info("Q: %s", q)
        result = await agent.run(q)
        logger.info("A: %s\n", result.text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
