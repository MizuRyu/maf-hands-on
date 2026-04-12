"""ドキュメント分類 Agent のユニットテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock

from src.platform.agents.document_classifier.agent import AGENT_META, build_document_classifier_agent
from src.platform.agents.document_classifier.tools import extract_document_keywords


class TestDocumentClassifierTools:
    def test_extract_contract_keywords(self) -> None:
        """契約書キーワードが検出される。"""
        text = "本契約は甲と乙の間で締結されるものとする"
        result = extract_document_keywords.func(text)  # type: ignore[reportOptionalCall]
        assert "contract" in result
        assert "契約" in result

    def test_extract_invoice_keywords(self) -> None:
        """請求書キーワードが検出される。"""
        text = "請求金額合計をご確認の上、お支払いください"
        result = extract_document_keywords.func(text)  # type: ignore[reportOptionalCall]
        assert "invoice" in result

    def test_no_keywords_found(self) -> None:
        """キーワードが見つからない場合。"""
        text = "今日はいい天気ですね"
        result = extract_document_keywords.func(text)  # type: ignore[reportOptionalCall]
        assert "見つかりませんでした" in result


class TestDocumentClassifierAgent:
    def test_agent_meta(self) -> None:
        """AgentMeta が正しい。"""
        assert AGENT_META.name == "document-classifier"

    def test_build_agent(self) -> None:
        """structured output 付きで Agent が構築できる。"""
        mock_client = MagicMock()
        agent = build_document_classifier_agent(mock_client)
        assert agent.name == "document-classifier"
