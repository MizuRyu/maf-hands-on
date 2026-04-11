"""テキスト分析 Agent の定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent_framework import Agent, BaseChatClient
from agent_framework_azure_cosmos import CosmosHistoryProvider

from src.platform.catalog.agents.text_analyzer.prompts import INSTRUCTIONS
from src.platform.catalog.agents.text_analyzer.tools import count_words, summarize_text
from src.platform.catalog.definitions import AgentMeta

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient

AGENT_META = AgentMeta(
    name="text-analyzer",
    description="テキスト分析(単語数カウント・要約)を行う Agent",
    version=1,
    model_id="gpt-4o",
    tool_names=["count_words", "summarize_text"],
)


def build_text_analyzer_agent(
    client: BaseChatClient,
    *,
    cosmos_client: CosmosClient | None = None,
) -> Agent:
    """テキスト分析 Agent を生成する。"""
    history = CosmosHistoryProvider(cosmos_client=cosmos_client) if cosmos_client else CosmosHistoryProvider()

    return Agent(
        client=client,
        name=AGENT_META.name,
        description=AGENT_META.description,
        instructions=INSTRUCTIONS,
        tools=[count_words, summarize_text],
        context_providers=[history],
    )
