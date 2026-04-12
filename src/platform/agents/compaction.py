"""Compaction 戦略ファクトリ — YAML 定義から MAF CompactionStrategy を生成する。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent_framework import (
    CharacterEstimatorTokenizer,
    CompactionStrategy,
    SlidingWindowStrategy,
    SummarizationStrategy,
    TokenBudgetComposedStrategy,
    TruncationStrategy,
)

if TYPE_CHECKING:
    from agent_framework import BaseChatClient, TokenizerProtocol

# YAML の strategy 名と MAF クラスのマッピング
STRATEGY_NAMES = frozenset({"sliding_window", "token_budget", "summarization"})

_DEFAULT_MAX_TURNS = 20
_DEFAULT_TOKEN_BUDGET = 4096
_DEFAULT_SUMMARIZATION_TARGET = 4


def create_compaction_strategy(
    strategy_name: str,
    config: dict[str, Any] | None = None,
    *,
    client: BaseChatClient | None = None,
    tokenizer: TokenizerProtocol | None = None,
) -> CompactionStrategy:
    """strategy 名と設定 dict から MAF CompactionStrategy を生成する。

    Args:
        strategy_name: 戦略名 (sliding_window / token_budget / summarization)
        config: 戦略固有パラメータ
        client: summarization 戦略で使用する ChatClient
        tokenizer: token_budget 戦略で使用するトークナイザ

    Raises:
        ValueError: 未知の strategy 名が指定された場合
        ValueError: summarization で client が未指定の場合
    """
    cfg = config or {}

    if strategy_name == "sliding_window":
        return SlidingWindowStrategy(
            keep_last_groups=cfg.get("max_turns", _DEFAULT_MAX_TURNS),
            preserve_system=cfg.get("preserve_system", True),
        )

    if strategy_name == "token_budget":
        tok = tokenizer or CharacterEstimatorTokenizer()
        budget = cfg.get("max_tokens", _DEFAULT_TOKEN_BUDGET)
        # TruncationStrategy をフォールバックに、TokenBudgetComposedStrategy で制御
        inner_strategies: list[CompactionStrategy] = []

        # sliding_window も内部で使う場合
        inner_max_turns = cfg.get("max_turns")
        if inner_max_turns:
            inner_strategies.append(
                SlidingWindowStrategy(keep_last_groups=inner_max_turns),
            )

        inner_strategies.append(
            TruncationStrategy(
                max_n=budget,
                compact_to=int(budget * 0.8),
                tokenizer=tok,
            ),
        )

        return TokenBudgetComposedStrategy(
            token_budget=budget,
            tokenizer=tok,
            strategies=inner_strategies,
        )

    if strategy_name == "summarization":
        if client is None:
            msg = "summarization 戦略には client が必要です"
            raise ValueError(msg)
        return SummarizationStrategy(
            client=client,
            target_count=cfg.get("target_count", _DEFAULT_SUMMARIZATION_TARGET),
            threshold=cfg.get("threshold", 2),
        )

    msg = f"未知の compaction 戦略: {strategy_name!r} (利用可能: {', '.join(sorted(STRATEGY_NAMES))})"
    raise ValueError(msg)
