"""プラットフォーム共通ポリシーの読み込み。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_POLICY_PATH = Path(__file__).parents[3] / "config" / "platform-policy.yaml"


@dataclass(frozen=True)
class AgentBasePolicy:
    """Agent 単位に解決されたベースポリシー。"""

    rai_config: str
    compaction_enabled: bool
    compaction_max_tokens: int
    history_enabled: bool


@dataclass
class PlatformPolicy:
    """platform-policy.yaml を読み込み、Agent 単位のポリシーを返す。"""

    defaults: AgentBasePolicy
    _agent_overrides: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: Path | None = None) -> PlatformPolicy:
        """YAML ファイルからポリシーを読み込む。"""
        policy_path = path or _DEFAULT_POLICY_PATH
        with policy_path.open() as f:
            raw = yaml.safe_load(f)

        defaults_raw = raw.get("defaults", {})
        compaction = defaults_raw.get("compaction", {})

        defaults = AgentBasePolicy(
            rai_config=defaults_raw.get("rai_config", "standard-filter"),
            compaction_enabled=compaction.get("enabled", True),
            compaction_max_tokens=compaction.get("max_tokens", 4096),
            history_enabled=defaults_raw.get("history", {}).get("enabled", True),
        )

        return cls(
            defaults=defaults,
            _agent_overrides=raw.get("agents", {}),
        )

    def for_agent(self, agent_name: str) -> AgentBasePolicy:
        """Agent 名でポリシーを解決する。override があればデフォルトにマージ。"""
        overrides = self._agent_overrides.get(agent_name, {})
        if not overrides:
            return self.defaults

        compaction = overrides.get("compaction", {})
        return AgentBasePolicy(
            rai_config=overrides.get("rai_config", self.defaults.rai_config),
            compaction_enabled=compaction.get("enabled", self.defaults.compaction_enabled),
            compaction_max_tokens=compaction.get("max_tokens", self.defaults.compaction_max_tokens),
            history_enabled=overrides.get("history", {}).get("enabled", self.defaults.history_enabled),
        )
