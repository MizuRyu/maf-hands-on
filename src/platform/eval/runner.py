"""ローカル Eval Runner。

MAF の LocalEvaluator + @evaluator を使用し、
JSONL データセットから Agent を評価する。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent_framework import LocalEvaluator, evaluate_agent, evaluator, keyword_check

from src.platform.eval.config_schema import EvalConfig, load_eval_config

if TYPE_CHECKING:
    from agent_framework import Agent, EvalResults

logger = logging.getLogger(__name__)


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    """JSONL データセットを読み込む。

    各行: {"query": "...", "expected_output": "...", "keywords": [...]}
    """
    items: list[dict[str, Any]] = []
    with dataset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def build_evaluators_from_config(
    config: EvalConfig,
) -> list[Any]:
    """EvalConfig から evaluator インスタンス群を構築する。"""
    evals: list[Any] = []
    for ev_config in config.evaluators:
        if ev_config.type == "keyword":
            keywords = ev_config.params.get("keywords", [])
            evals.append(keyword_check(*keywords))
        elif ev_config.type == "length":
            max_words = ev_config.params.get("max_words", 500)

            @evaluator
            def is_concise(response: str, _max=max_words) -> bool:
                """応答が指定語数以下であることを確認する。"""
                return len(response.split()) <= _max

            evals.append(is_concise)
        elif ev_config.type == "contains_expected":

            @evaluator
            def contains_expected(response: str, expected_output: str) -> bool:
                """応答に期待出力が含まれることを確認する。"""
                return expected_output.lower() in response.lower()

            evals.append(contains_expected)
        else:
            logger.warning("未知の evaluator type: %s — スキップ", ev_config.type)
    return evals


async def run_eval(
    agent: Agent,
    config_path: Path,
) -> list[EvalResults]:
    """設定ファイルに基づいて Agent 評価を実行する。"""
    config = load_eval_config(config_path)
    dataset_dir = config_path.parent
    dataset_path = dataset_dir / config.dataset
    dataset = load_dataset(dataset_path)

    queries = [item["query"] for item in dataset]
    check_fns = build_evaluators_from_config(config)
    if not check_fns:
        msg = "evaluator が1つも構築されませんでした"
        raise ValueError(msg)

    local_evaluator = LocalEvaluator(*check_fns)
    results = await evaluate_agent(
        agent=agent,
        queries=queries,
        evaluators=[local_evaluator],
    )
    return list(results)
