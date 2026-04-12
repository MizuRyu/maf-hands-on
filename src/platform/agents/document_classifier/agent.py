"""ドキュメント分類 Agent の定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent_framework import Agent, BaseChatClient

from src.platform.agents import PlatformAgentBuilder
from src.platform.agents._types import AgentMeta
from src.platform.agents.config_loader import AgentFeatures
from src.platform.agents.document_classifier.prompts import INSTRUCTIONS
from src.platform.agents.document_classifier.tools import extract_document_keywords

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient

AGENT_META = AgentMeta(
    name="document-classifier",
    description="ドキュメント分類を行う Agent (structured output)",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["extract_document_keywords"],
)

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "DocumentClassification",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["contract", "invoice", "report", "correspondence", "manual", "other"],
                },
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["category", "confidence", "reasoning", "keywords"],
            "additionalProperties": False,
        },
    },
}


def build_document_classifier_agent(
    client: BaseChatClient,
    *,
    cosmos_client: CosmosClient | None = None,
) -> Agent:
    """ドキュメント分類 Agent を生成する。"""
    builder = PlatformAgentBuilder(cosmos_client=cosmos_client)
    return builder.build(
        client=client,
        name=AGENT_META.name,
        description=AGENT_META.description,
        instructions=INSTRUCTIONS,
        tools=[extract_document_keywords],
        features=AgentFeatures(structured_output=True),
        response_format=RESPONSE_FORMAT,
    )
