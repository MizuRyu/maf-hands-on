"""ドキュメント分類 Agent のユニットテスト。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from src.platform.agents.document_classifier.agent import AGENT_META, RESPONSE_FORMAT, TOOLS
from src.platform.agents.document_classifier.tools import extract_document_keywords


class TestDocumentClassifierTools:
    def test_extract_contract_keywords(self) -> None:
        text = "本契約は甲と乙の間で締結されるものとする"
        result = extract_document_keywords.func(text)  # type: ignore[reportOptionalCall]
        assert "contract" in result
        assert "契約" in result

    def test_extract_invoice_keywords(self) -> None:
        text = "請求金額合計をご確認の上、お支払いください"
        result = extract_document_keywords.func(text)  # type: ignore[reportOptionalCall]
        assert "invoice" in result

    def test_no_keywords_found(self) -> None:
        text = "今日はいい天気ですね"
        result = extract_document_keywords.func(text)  # type: ignore[reportOptionalCall]
        assert "見つかりませんでした" in result


class TestDocumentClassifierAgent:
    def test_agent_meta(self) -> None:
        assert AGENT_META.name == "document-classifier-agent"

    def test_create_agent(self, tmp_path: Path) -> None:
        from src.platform.agents.document_classifier.prompts import INSTRUCTIONS
        from src.platform.core.agent_factory import PlatformAgentFactory
        from src.platform.core.config_loader import AgentFeatures

        policy = tmp_path / "policy.yaml"
        policy.write_text("defaults:\n  history:\n    enabled: false\nagents: {}")
        factory = PlatformAgentFactory(client=MagicMock(), policy_path=policy)
        agent = factory.create(
            meta=AGENT_META,
            instructions=INSTRUCTIONS,
            tools=TOOLS,
            features=AgentFeatures(structured_output=True),
            response_format=RESPONSE_FORMAT,
        )
        assert agent.name == "document-classifier-agent"
