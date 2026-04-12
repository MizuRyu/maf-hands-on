"""eval config_schema / runner のユニットテスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.platform.eval.config_schema import EvalConfig, EvaluatorConfig, load_eval_config
from src.platform.eval.runner import build_evaluators_from_config, load_dataset


class TestEvalConfig:
    def test_load_valid_config(self, tmp_path: Path) -> None:
        """有効な eval_config.yaml をロードできる。"""
        config_file = tmp_path / "eval_config.yaml"
        config_file.write_text(
            """
evaluators:
  - type: keyword
    params:
      keywords: ["分析"]
  - type: length
    params:
      max_words: 200
dataset: test.jsonl
"""
        )
        config = load_eval_config(config_file)
        assert len(config.evaluators) == 2
        assert config.dataset == "test.jsonl"

    def test_load_empty_raises(self, tmp_path: Path) -> None:
        """空の YAML はエラーになる。"""
        config_file = tmp_path / "eval_config.yaml"
        config_file.write_text("")
        with pytest.raises(ValueError, match="Empty eval config"):
            load_eval_config(config_file)

    def test_missing_evaluators_raises(self, tmp_path: Path) -> None:
        """evaluators が無い場合はバリデーションエラー。"""
        config_file = tmp_path / "eval_config.yaml"
        config_file.write_text("dataset: test.jsonl\n")
        with pytest.raises(ValueError, match=r"field required|validation error"):
            load_eval_config(config_file)

    def test_model_defaults(self) -> None:
        """デフォルト値が正しい。"""
        config = EvalConfig(
            evaluators=[EvaluatorConfig(type="keyword")],
            dataset="test.jsonl",
        )
        assert config.num_repetitions == 1
        assert config.agent_name is None


class TestLoadDataset:
    def test_load_jsonl(self, tmp_path: Path) -> None:
        """JSONL を正しくロードする。"""
        dataset_file = tmp_path / "test.jsonl"
        dataset_file.write_text(
            '{"query": "テスト1", "expected_output": "結果1"}\n{"query": "テスト2", "expected_output": "結果2"}\n'
        )
        items = load_dataset(dataset_file)
        assert len(items) == 2
        assert items[0]["query"] == "テスト1"

    def test_skip_empty_lines(self, tmp_path: Path) -> None:
        """空行をスキップする。"""
        dataset_file = tmp_path / "test.jsonl"
        dataset_file.write_text('{"query": "テスト1"}\n\n{"query": "テスト2"}\n')
        items = load_dataset(dataset_file)
        assert len(items) == 2


class TestBuildEvaluators:
    def test_keyword_evaluator(self) -> None:
        """keyword タイプの evaluator を構築できる。"""
        config = EvalConfig(
            evaluators=[EvaluatorConfig(type="keyword", params={"keywords": ["テスト"]})],
            dataset="test.jsonl",
        )
        evals = build_evaluators_from_config(config)
        assert len(evals) == 1

    def test_length_evaluator(self) -> None:
        """length タイプの evaluator を構築できる。"""
        config = EvalConfig(
            evaluators=[EvaluatorConfig(type="length", params={"max_words": 100})],
            dataset="test.jsonl",
        )
        evals = build_evaluators_from_config(config)
        assert len(evals) == 1

    def test_contains_expected_evaluator(self) -> None:
        """contains_expected タイプの evaluator を構築できる。"""
        config = EvalConfig(
            evaluators=[EvaluatorConfig(type="contains_expected")],
            dataset="test.jsonl",
        )
        evals = build_evaluators_from_config(config)
        assert len(evals) == 1

    def test_unknown_type_skipped(self) -> None:
        """未知の type はスキップされる。"""
        config = EvalConfig(
            evaluators=[EvaluatorConfig(type="unknown_type")],
            dataset="test.jsonl",
        )
        evals = build_evaluators_from_config(config)
        assert len(evals) == 0
