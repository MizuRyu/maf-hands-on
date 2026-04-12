"""経費チェッカー Agent の定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent_framework import Agent, BaseChatClient

from src.platform.agents import PlatformAgentBuilder
from src.platform.agents._types import AgentMeta
from src.platform.agents.expense_checker.prompts import INSTRUCTIONS
from src.platform.agents.expense_checker.tools import calculate_total, check_expense_policy
from src.platform.tools.datetime_tools import get_current_datetime

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient

AGENT_META = AgentMeta(
    name="expense-checker",
    description="経費ポリシーチェック・金額計算を行う Agent",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["check_expense_policy", "calculate_total", "get_current_datetime"],
)


def build_expense_checker_agent(
    client: BaseChatClient,
    *,
    cosmos_client: CosmosClient | None = None,
) -> Agent:
    """経費チェッカー Agent を生成する。"""
    builder = PlatformAgentBuilder(cosmos_client=cosmos_client)
    return builder.build(
        client=client,
        name=AGENT_META.name,
        description=AGENT_META.description,
        instructions=INSTRUCTIONS,
        tools=[check_expense_policy, calculate_total, get_current_datetime],
    )
