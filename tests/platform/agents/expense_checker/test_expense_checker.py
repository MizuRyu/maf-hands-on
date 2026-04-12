"""経費チェッカー Agent のユニットテスト。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from src.platform.agents.expense_checker.agent import AGENT_META, TOOLS
from src.platform.agents.expense_checker.tools import calculate_total, check_expense_policy


class TestExpenseCheckerTools:
    def test_check_policy_within_limit(self) -> None:
        """上限内の経費はOK。"""
        result = check_expense_policy.func("交通費", 5000)  # type: ignore[reportOptionalCall]
        assert "問題なし" in result

    def test_check_policy_exceeds_limit(self) -> None:
        """上限超過は警告。"""
        result = check_expense_policy.func("交通費", 15000)  # type: ignore[reportOptionalCall]
        assert "超過" in result

    def test_check_policy_requires_approval(self) -> None:
        """交際費は事前承認が必要。"""
        result = check_expense_policy.func("交際費", 1000)  # type: ignore[reportOptionalCall]
        assert "事前承認" in result

    def test_check_policy_unknown_category(self) -> None:
        """不明なカテゴリは警告。"""
        result = check_expense_policy.func("不明カテゴリ", 1000)  # type: ignore[reportOptionalCall]
        assert "警告" in result

    def test_calculate_total_basic(self) -> None:
        """基本的な合計計算。"""
        items = "タクシー代,3000\n昼食,1500"
        result = calculate_total.func(items, 0.10)  # type: ignore[reportOptionalCall]
        assert "4,500" in result
        assert "税込" in result

    def test_calculate_total_invalid_format(self) -> None:
        """不正フォーマットの項目はエラー表示。"""
        items = "不正な行"
        result = calculate_total.func(items, 0.10)  # type: ignore[reportOptionalCall]
        assert "フォーマットエラー" in result


class TestExpenseCheckerAgent:
    def test_agent_meta(self) -> None:
        assert AGENT_META.name == "expense-checker-agent"
        assert len(AGENT_META.tool_names) == 3

    def test_create_agent(self, tmp_path: Path) -> None:
        """Factory 経由で Agent が構築できる。"""
        from src.platform.agents.expense_checker.prompts import INSTRUCTIONS
        from src.platform.core.agent_factory import PlatformAgentFactory

        policy = tmp_path / "policy.yaml"
        policy.write_text("defaults:\n  history:\n    enabled: false\nagents: {}")
        factory = PlatformAgentFactory(client=MagicMock(), policy_path=policy)
        agent = factory.create(meta=AGENT_META, instructions=INSTRUCTIONS, tools=TOOLS)
        assert agent.name == "expense-checker-agent"
