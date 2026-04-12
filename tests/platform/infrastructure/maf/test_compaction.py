"""compaction モジュールのテスト。"""

from unittest.mock import MagicMock

import pytest
from agent_framework import (
    CompactionStrategy,
    SlidingWindowStrategy,
    SummarizationStrategy,
    TokenBudgetComposedStrategy,
)

from src.platform.agents.compaction import create_compaction_strategy


class TestCreateCompactionStrategy:
    def test_sliding_window_default(self) -> None:
        strategy = create_compaction_strategy("sliding_window")
        assert isinstance(strategy, SlidingWindowStrategy)
        assert strategy.keep_last_groups == 20

    def test_sliding_window_custom_turns(self) -> None:
        strategy = create_compaction_strategy("sliding_window", {"max_turns": 10})
        assert isinstance(strategy, SlidingWindowStrategy)
        assert strategy.keep_last_groups == 10

    def test_token_budget_default(self) -> None:
        strategy = create_compaction_strategy("token_budget")
        assert isinstance(strategy, TokenBudgetComposedStrategy)
        assert strategy.token_budget == 4096

    def test_token_budget_custom(self) -> None:
        strategy = create_compaction_strategy("token_budget", {"max_tokens": 2048})
        assert isinstance(strategy, TokenBudgetComposedStrategy)
        assert strategy.token_budget == 2048

    def test_summarization_with_client(self) -> None:
        client = MagicMock()
        strategy = create_compaction_strategy(
            "summarization",
            {"target_count": 6, "threshold": 3},
            client=client,
        )
        assert isinstance(strategy, SummarizationStrategy)
        assert strategy.target_count == 6
        assert strategy.threshold == 3

    def test_summarization_without_client_raises(self) -> None:
        with pytest.raises(ValueError, match="client が必要"):
            create_compaction_strategy("summarization")

    def test_unknown_strategy_raises(self) -> None:
        with pytest.raises(ValueError, match="未知の compaction 戦略"):
            create_compaction_strategy("unknown_strategy")

    def test_returns_compaction_strategy_protocol(self) -> None:
        """生成された戦略が CompactionStrategy プロトコルを満たすことを確認。"""
        strategy = create_compaction_strategy("sliding_window")
        assert isinstance(strategy, CompactionStrategy)
