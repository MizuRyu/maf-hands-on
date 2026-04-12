"""Config Agent YAML ローダー — config/agents/*.yaml から Agent を構築する。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from src.platform.agents.compaction import create_compaction_strategy

if TYPE_CHECKING:
    from collections.abc import Callable

    from agent_framework import Agent, BaseChatClient, TokenizerProtocol
    from azure.cosmos.aio import CosmosClient

    from src.platform.agents.builder import PlatformAgentBuilder

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_DIR = Path(__file__).parents[3] / "config" / "agents"


@dataclass(frozen=True)
class AgentFeatures:
    """Agent の feature flags。"""

    history: bool = True
    compaction: bool = True
    tools: bool = True
    structured_output: bool = False


@dataclass(frozen=True)
class CompactionConfig:
    """Compaction 戦略の設定。"""

    strategy: str = "sliding_window"
    max_turns: int = 20
    max_tokens: int = 4096
    target_count: int = 4
    threshold: int = 2


@dataclass(frozen=True)
class ConfigAgentDefinition:
    """YAML からロードした Agent 定義。"""

    name: str
    version: int
    model_id: str
    instructions: str
    tool_names: list[str] = field(default_factory=list)
    description: str = ""
    features: AgentFeatures = field(default_factory=AgentFeatures)
    compaction: CompactionConfig = field(default_factory=CompactionConfig)
    response_format: dict[str, Any] | None = None


def _parse_features(raw: dict[str, Any] | None) -> AgentFeatures:
    """YAML の features セクションをパースする。"""
    if not raw:
        return AgentFeatures()
    return AgentFeatures(
        history=raw.get("history", True),
        compaction=raw.get("compaction", True),
        tools=raw.get("tools", True),
        structured_output=raw.get("structured_output", False),
    )


def _parse_compaction(raw: dict[str, Any] | None) -> CompactionConfig:
    """YAML の compaction セクションをパースする。"""
    if not raw:
        return CompactionConfig()
    return CompactionConfig(
        strategy=raw.get("strategy", "sliding_window"),
        max_turns=raw.get("max_turns", 20),
        max_tokens=raw.get("max_tokens", 4096),
        target_count=raw.get("target_count", 4),
        threshold=raw.get("threshold", 2),
    )


def load_agent_definition(path: Path) -> ConfigAgentDefinition:
    """単一の YAML ファイルから ConfigAgentDefinition を読み込む。"""
    with path.open() as f:
        raw = yaml.safe_load(f)

    if not raw or not isinstance(raw, dict):
        msg = f"不正な Agent YAML: {path}"
        raise ValueError(msg)

    required = ("name", "version", "model_id", "instructions")
    missing = [k for k in required if k not in raw]
    if missing:
        msg = f"Agent YAML に必須フィールドがありません: {', '.join(missing)} ({path})"
        raise ValueError(msg)

    return ConfigAgentDefinition(
        name=raw["name"],
        version=raw["version"],
        model_id=raw["model_id"],
        instructions=raw["instructions"],
        tool_names=raw.get("tools", []),
        description=raw.get("description", ""),
        features=_parse_features(raw.get("features")),
        compaction=_parse_compaction(raw.get("compaction")),
        response_format=raw.get("response_format"),
    )


def load_all_definitions(
    config_dir: Path | None = None,
) -> dict[str, ConfigAgentDefinition]:
    """config/agents/ 配下の全 YAML を読み込み、名前 -> 定義の dict を返す。"""
    directory = config_dir or _DEFAULT_CONFIG_DIR
    if not directory.exists():
        logger.warning("Config Agent ディレクトリが存在しません: %s", directory)
        return {}

    definitions: dict[str, ConfigAgentDefinition] = {}
    for yaml_path in sorted(directory.glob("*.yaml")):
        try:
            definition = load_agent_definition(yaml_path)
            definitions[definition.name] = definition
            logger.info("Config Agent 読み込み: %s (v%d)", definition.name, definition.version)
        except Exception:
            logger.exception("Config Agent YAML の読み込みに失敗: %s", yaml_path)
    return definitions


def build_agent_from_definition(
    definition: ConfigAgentDefinition,
    builder: PlatformAgentBuilder,
    client: BaseChatClient,
    *,
    tool_registry: dict[str, Callable[..., Any]] | None = None,
    cosmos_client: CosmosClient | None = None,
    tokenizer: TokenizerProtocol | None = None,
) -> Agent:
    """ConfigAgentDefinition から Agent を構築する。

    tool_registry を使って tool_names を実際の callable に解決する。
    """
    # Tool 解決
    registry = tool_registry or {}
    tools: list[Callable[..., Any]] = []
    if definition.features.tools:
        for tool_name in definition.tool_names:
            if tool_name in registry:
                tools.append(registry[tool_name])
            else:
                logger.warning("未登録の Tool: %s (Agent: %s)", tool_name, definition.name)

    # Compaction 戦略
    compaction_strategy = None
    if definition.features.compaction:
        compaction_config = {
            "max_turns": definition.compaction.max_turns,
            "max_tokens": definition.compaction.max_tokens,
            "target_count": definition.compaction.target_count,
            "threshold": definition.compaction.threshold,
        }
        try:
            compaction_strategy = create_compaction_strategy(
                definition.compaction.strategy,
                compaction_config,
                client=client if definition.compaction.strategy == "summarization" else None,
                tokenizer=tokenizer,
            )
        except ValueError:
            logger.exception("Compaction 戦略の生成に失敗 (Agent: %s)", definition.name)

    # response_format (structured output)
    response_format = definition.response_format if definition.features.structured_output else None

    return builder.build(
        client=client,
        name=definition.name,
        instructions=definition.instructions,
        tools=tools,
        description=definition.description,
        features=definition.features,
        compaction_strategy=compaction_strategy,
        response_format=response_format,
    )
