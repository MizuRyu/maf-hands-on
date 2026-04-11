"""テキスト分析 Agent。文章の単語数カウントや要約を行う。"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from agent_framework import Agent, BaseChatClient, tool
from agent_framework_azure_cosmos import CosmosHistoryProvider

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient

logger = logging.getLogger(__name__)

MY_AGENT_INSTRUCTIONS = """
あなたはテキスト分析の専門アシスタントです。
ユーザーから与えられた文章に対して、単語数のカウントや要約を行います。
回答は簡潔かつ正確に、日本語で行ってください。
必要に応じてツールを活用し、根拠のある情報を提示してください。
""".strip()


@tool
def count_words(
    text: Annotated[str, "単語数をカウントする対象テキスト"],
) -> str:
    """テキストの単語数をカウントして結果を返す。

    日本語テキストは文字数、英語テキストはスペース区切りの単語数をそれぞれ集計する。
    """
    chars = len(text)
    words = len(text.split())
    return f"文字数: {chars}, 単語数(空白区切り): {words}"


@tool
def summarize_text(
    text: Annotated[str, "要約対象のテキスト"],
    max_sentences: Annotated[int, "要約の最大文数"] = 3,
) -> str:
    """テキストを指定された文数以内に要約する。

    句点(。)で文を分割し、先頭から最大文数分を抽出する簡易要約を行う。
    LLM による高度な要約が必要な場合は Agent 自身の推論に委ねる。
    """
    # 句点で分割し、空要素を除去
    sentences = [s.strip() for s in text.split("。") if s.strip()]
    selected = sentences[:max_sentences]
    summary = "。".join(selected)
    if summary and not summary.endswith("。"):
        summary += "。"
    return f"要約({len(selected)}/{len(sentences)} 文): {summary}"


def get_my_agent(
    client: BaseChatClient,
    *,
    cosmos_client: CosmosClient | None = None,
) -> Agent:
    """テキスト分析 Agent を生成する。"""
    history = CosmosHistoryProvider(cosmos_client=cosmos_client) if cosmos_client else CosmosHistoryProvider()

    return Agent(
        client=client,
        name="my-agent",
        description="テキスト分析(単語数カウント・要約)を行う Agent",
        instructions=MY_AGENT_INSTRUCTIONS,
        tools=[count_words, summarize_text],
        context_providers=[history],
    )
