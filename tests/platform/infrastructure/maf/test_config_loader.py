"""config_loader モジュールのテスト。"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.platform.agents.config_loader import (
    AgentFeatures,
    CompactionConfig,
    ConfigAgentDefinition,
    build_agent_from_definition,
    load_agent_definition,
    load_all_definitions,
)

_VALID_YAML = """\
name: test-agent
version: 1
model_id: gpt-5-nano
description: テスト用エージェント
instructions: |
  あなたはテスト用のエージェントです。
tools:
  - tool_a
  - tool_b
features:
  history: true
  compaction: true
  tools: true
  structured_output: false
compaction:
  strategy: sliding_window
  max_turns: 15
"""

_MINIMAL_YAML = """\
name: minimal-agent
version: 1
model_id: gpt-5-nano
instructions: 最小限のエージェント
"""

_STRUCTURED_OUTPUT_YAML = """\
name: structured-agent
version: 1
model_id: gpt-5-nano
instructions: 構造化出力エージェント
features:
  structured_output: true
  tools: false
  history: false
  compaction: false
response_format:
  type: json_schema
  json_schema:
    name: Result
    schema:
      type: object
      properties:
        answer:
          type: string
"""

_INVALID_YAML_MISSING_NAME = """\
version: 1
model_id: gpt-5-nano
instructions: 名前がない
"""


class TestLoadAgentDefinition:
    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(_VALID_YAML)

        definition = load_agent_definition(yaml_file)

        assert definition.name == "test-agent"
        assert definition.version == 1
        assert definition.model_id == "gpt-5-nano"
        assert definition.description == "テスト用エージェント"
        assert "あなたはテスト用のエージェントです。" in definition.instructions
        assert definition.tool_names == ["tool_a", "tool_b"]
        assert definition.features.history is True
        assert definition.features.compaction is True
        assert definition.features.tools is True
        assert definition.features.structured_output is False
        assert definition.compaction.strategy == "sliding_window"
        assert definition.compaction.max_turns == 15

    def test_load_minimal_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "minimal.yaml"
        yaml_file.write_text(_MINIMAL_YAML)

        definition = load_agent_definition(yaml_file)

        assert definition.name == "minimal-agent"
        assert definition.tool_names == []
        assert definition.features == AgentFeatures()
        assert definition.compaction == CompactionConfig()

    def test_load_structured_output_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "structured.yaml"
        yaml_file.write_text(_STRUCTURED_OUTPUT_YAML)

        definition = load_agent_definition(yaml_file)

        assert definition.features.structured_output is True
        assert definition.features.tools is False
        assert definition.response_format is not None
        assert definition.response_format["type"] == "json_schema"

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(_INVALID_YAML_MISSING_NAME)

        with pytest.raises(ValueError, match="必須フィールド"):
            load_agent_definition(yaml_file)

    def test_empty_yaml_raises(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        with pytest.raises(ValueError, match="不正な Agent YAML"):
            load_agent_definition(yaml_file)


class TestLoadAllDefinitions:
    def test_load_multiple_yamls(self, tmp_path: Path) -> None:
        (tmp_path / "a.yaml").write_text(_VALID_YAML)
        (tmp_path / "b.yaml").write_text(_MINIMAL_YAML)

        definitions = load_all_definitions(tmp_path)

        assert len(definitions) == 2
        assert "test-agent" in definitions
        assert "minimal-agent" in definitions

    def test_nonexistent_dir_returns_empty(self, tmp_path: Path) -> None:
        definitions = load_all_definitions(tmp_path / "nonexistent")
        assert definitions == {}

    def test_skips_invalid_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "valid.yaml").write_text(_VALID_YAML)
        (tmp_path / "bad.yaml").write_text(_INVALID_YAML_MISSING_NAME)

        definitions = load_all_definitions(tmp_path)

        assert len(definitions) == 1
        assert "test-agent" in definitions


_NO_HISTORY_POLICY = """\
defaults:
  rai_config: "standard-filter"
  compaction:
    enabled: true
    max_tokens: 4096
  history:
    enabled: false

agents: {}
"""


class TestBuildAgentFromDefinition:
    @pytest.fixture
    def factory(self, tmp_path: Path):
        from src.platform.agents.factory import PlatformAgentFactory

        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(_NO_HISTORY_POLICY)
        return PlatformAgentFactory(client=MagicMock(), policy_path=policy_file)

    def test_build_with_tools(self, factory) -> None:
        definition = ConfigAgentDefinition(
            name="tool-agent",
            version=1,
            model_id="gpt-5-nano",
            instructions="テスト",
            tool_names=["my_tool"],
            features=AgentFeatures(tools=True, history=False, compaction=False),
        )

        def my_tool() -> str:
            return "hello"

        agent = build_agent_from_definition(
            definition,
            factory,
            tool_registry={"my_tool": my_tool},
        )
        assert agent.name == "tool-agent"

    def test_build_with_tools_disabled(self, factory) -> None:
        """tools: false の場合、Agent が生成される（ツール無し）。"""
        definition = ConfigAgentDefinition(
            name="no-tool-agent",
            version=1,
            model_id="gpt-5-nano",
            instructions="テスト",
            tool_names=["my_tool"],
            features=AgentFeatures(tools=False, history=False, compaction=False),
        )

        agent = build_agent_from_definition(
            definition,
            factory,
            tool_registry={"my_tool": lambda: "hello"},
        )
        assert agent.name == "no-tool-agent"

    def test_build_with_compaction(self, factory) -> None:
        definition = ConfigAgentDefinition(
            name="compacted-agent",
            version=1,
            model_id="gpt-5-nano",
            instructions="テスト",
            features=AgentFeatures(compaction=True, history=False),
            compaction=CompactionConfig(strategy="sliding_window", max_turns=10),
        )

        agent = build_agent_from_definition(definition, factory)
        assert agent.compaction_strategy is not None
