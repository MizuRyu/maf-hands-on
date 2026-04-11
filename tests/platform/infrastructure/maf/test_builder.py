"""PlatformAgentBuilder のテスト。"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agent_framework import Agent

from src.platform.infrastructure.maf.builder import PlatformAgentBuilder
from src.platform.infrastructure.maf.middleware.audit_middleware import AuditMiddleware
from src.platform.infrastructure.maf.middleware.security_middleware import SecurityMiddleware

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


class TestPlatformAgentBuilder:
    @pytest.fixture
    def policy_file(self, tmp_path: Path) -> Path:
        """history 無効のポリシー (Cosmos 不要)"""
        f = tmp_path / "policy.yaml"
        f.write_text(_NO_HISTORY_POLICY)
        return f

    @pytest.fixture
    def builder(self, policy_file: Path) -> PlatformAgentBuilder:
        return PlatformAgentBuilder(policy_path=policy_file)

    def test_build_returns_agent(self, builder: PlatformAgentBuilder) -> None:
        client = MagicMock()
        agent = builder.build(
            client=client,
            name="test-agent",
            instructions="You are a test agent.",
            tools=[],
        )
        assert isinstance(agent, Agent)
        assert agent.name == "test-agent"

    def test_required_middleware_injected(self, builder: PlatformAgentBuilder) -> None:
        client = MagicMock()
        agent = builder.build(
            client=client,
            name="test-agent",
            instructions="test",
            tools=[],
        )
        middleware_types = [type(m) for m in (agent.middleware or [])]
        assert AuditMiddleware in middleware_types
        assert SecurityMiddleware in middleware_types

    def test_custom_middleware_appended(self, builder: PlatformAgentBuilder) -> None:
        client = MagicMock()

        class CustomMiddleware(AuditMiddleware):
            pass

        agent = builder.build(
            client=client,
            name="test-agent",
            instructions="test",
            tools=[],
            middleware=[CustomMiddleware()],
        )
        middleware_types = [type(m) for m in (agent.middleware or [])]
        assert CustomMiddleware in middleware_types
        assert AuditMiddleware in middleware_types

    def test_history_provider_injected_when_enabled(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("AZURE_COSMOS_ENDPOINT", "http://localhost:8081")
        monkeypatch.setenv("AZURE_COSMOS_DATABASE_NAME", "maf")
        monkeypatch.setenv("AZURE_COSMOS_CONTAINER_NAME", "messages")
        monkeypatch.setenv("AZURE_COSMOS_KEY", "dummykey==")

        yaml_content = """\
defaults:
  rai_config: "standard-filter"
  compaction:
    enabled: true
    max_tokens: 4096
  history:
    enabled: true

agents: {}
"""
        policy_file = tmp_path / "policy.yaml"
        policy_file.write_text(yaml_content)
        builder = PlatformAgentBuilder(policy_path=policy_file)
        client = MagicMock()
        agent = builder.build(
            client=client,
            name="test-agent",
            instructions="test",
            tools=[],
        )
        provider_types = [type(p).__name__ for p in (agent.context_providers or [])]
        assert "CosmosHistoryProvider" in provider_types

    def test_history_provider_skipped_when_disabled(self, builder: PlatformAgentBuilder) -> None:
        client = MagicMock()
        agent = builder.build(
            client=client,
            name="test-agent",
            instructions="test",
            tools=[],
        )
        provider_types = [type(p).__name__ for p in (agent.context_providers or [])]
        assert "CosmosHistoryProvider" not in provider_types
