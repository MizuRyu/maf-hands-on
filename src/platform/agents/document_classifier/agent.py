"""ドキュメント分類 Agent の定義。"""

from __future__ import annotations

from src.platform.agents.document_classifier.schemas import DocumentClassification
from src.platform.agents.document_classifier.tools import extract_document_keywords
from src.platform.core.types import AgentMeta

AGENT_META = AgentMeta(
    name="document-classifier-agent",
    description="ドキュメント分類を行う Agent (structured output)",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["extract_document_keywords"],
)

TOOLS = [extract_document_keywords]
RESPONSE_FORMAT = DocumentClassification
