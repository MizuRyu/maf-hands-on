"""PlatformAgentFactory のテスト。"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agent_framework import Agent

from src.platform.core.agent_factory import PlatformAgentFactory
from src.platform.core.middleware.audit import AuditMiddleware
from src.platform.core.middleware.security import SecurityMiddleware
from src.platform.core.types import AgentMeta

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

_TEST_META = AgentMeta(
    name="test-agent",
    description="テスト用",
    version=1,
    model_id="gpt-5-nano",
)


class TestPlatformAgentFactory:
    @pytest.fixture
    def policy_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "policy.yaml"
        f.write_text(_NO_HISTORY_POLICY)
        return f

    @pytest.fixture
    def factory(self, policy_file: Path) -> PlatformAgentFactory:
        return PlatformAgentFactory(client=MagicMock(), policy_path=policy_file)

    def test_create_returns_agent(self, factory: PlatformAgentFactory) -> None:
        agent = factory.create(meta=_TEST_META, instructions="test", tools=[])
        assert isinstance(agent, Agent)
        assert agent.name == "test-agent"

    def test_required_middleware_injected(self, factory: PlatformAgentFactory) -> None:
        agent = factory.create(meta=_TEST_META, instructions="test", tools=[])
        middleware_types = [type(m) for m in (agent.middleware or [])]
        assert AuditMiddleware in middleware_types
        assert SecurityMiddleware in middleware_types

    def test_custom_middleware_appended(self, factory: PlatformAgentFactory) -> None:
        class CustomMiddleware(AuditMiddleware):
            pass

        agent = factory.create(meta=_TEST_META, instructions="test", tools=[], middleware=[CustomMiddleware()])
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
        factory = PlatformAgentFactory(client=MagicMock(), policy_path=policy_file)
        agent = factory.create(meta=_TEST_META, instructions="test", tools=[])
        provider_types = [type(p).__name__ for p in (agent.context_providers or [])]
        assert "CosmosHistoryProvider" in provider_types

    def test_history_provider_skipped_when_disabled(self, factory: PlatformAgentFactory) -> None:
        agent = factory.create(meta=_TEST_META, instructions="test", tools=[])
        provider_types = [type(p).__name__ for p in (agent.context_providers or [])]
        assert "CosmosHistoryProvider" not in provider_types
