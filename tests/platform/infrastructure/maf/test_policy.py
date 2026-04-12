"""PlatformPolicy のテスト。"""

from src.platform.core.policy import PlatformPolicy


class TestPlatformPolicy:
    def test_load_default_policy(self) -> None:
        policy = PlatformPolicy.load()
        assert policy.defaults.rai_config == "standard-filter"
        assert policy.defaults.compaction_enabled is True
        assert policy.defaults.compaction_max_tokens == 4096
        assert policy.defaults.history_enabled is True

    def test_agent_fallback_to_defaults(self) -> None:
        policy = PlatformPolicy.load()
        agent_policy = policy.for_agent("unknown-agent")
        assert agent_policy.rai_config == "standard-filter"

    def test_agent_specific_override(self, tmp_path) -> None:
        yaml_content = """\
defaults:
  rai_config: "standard-filter"
  compaction:
    enabled: true
    max_tokens: 4096
  history:
    enabled: true

agents:
  legal-review:
    rai_config: "strict-filter"
    compaction:
      max_tokens: 2048
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(yaml_content)
        policy = PlatformPolicy.load(policy_file)

        agent_policy = policy.for_agent("legal-review")
        assert agent_policy.rai_config == "strict-filter"
        assert agent_policy.compaction_max_tokens == 2048
        assert agent_policy.history_enabled is True
