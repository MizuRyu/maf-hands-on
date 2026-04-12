# PlatformAgentBuilder 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全 Agent に共通の Middleware / ContextProvider を自動注入するファクトリを作り、プラットフォームの品質基盤を確立する。

**Architecture:** `PlatformAgentBuilder` が `platform-policy.yaml` を読み込み、REQUIRED/DEFAULT middleware と ContextProvider を自動注入する。Agent 開発者は固有の部分だけ指定すればよい。Azure 未接続のため SecurityMiddleware / PurviewPolicyMiddleware はスタブ実装。

**Tech Stack:** Python 3.12, MAF 1.0.0 (Agent, AgentMiddleware, ContextProvider), PyYAML (設定読み込み), pytest

---

## ファイル構成

```
src/platform/infrastructure/maf/
├── __init__.py                    (既存、空)
├── builder.py                     (PlatformAgentBuilder)
├── middleware/
│   ├── __init__.py
│   ├── audit.py                   (AuditMiddleware)
│   └── security.py               (SecurityMiddleware スタブ)
└── policy.py                      (PlatformPolicy — YAML 読み込み)

config/
└── platform-policy.yaml           (プラットフォーム共通設定)

tests/platform/infrastructure/maf/
├── __init__.py
├── test_builder.py
├── test_audit_middleware.py
└── test_policy.py
```

---

### Task 1: PlatformPolicy — YAML 設定の読み込み

**Files:**
- Create: `config/platform-policy.yaml`
- Create: `src/platform/infrastructure/maf/policy.py`
- Create: `tests/platform/infrastructure/maf/__init__.py`
- Create: `tests/platform/infrastructure/maf/test_policy.py`

- [ ] **Step 1: platform-policy.yaml を作成**

```yaml
# config/platform-policy.yaml
defaults:
  rai_config: "standard-filter"
  compaction:
    enabled: true
    max_tokens: 4096
  history:
    enabled: true

agents: {}
```

- [ ] **Step 2: テストを書く**

```python
# tests/platform/infrastructure/maf/test_policy.py
from src.platform.infrastructure.maf.policy import PlatformPolicy


class TestPlatformPolicy:
    def test_load_default_policy(self) -> None:
        policy = PlatformPolicy.load()
        assert policy.defaults.rai_config == "standard-filter"
        assert policy.defaults.compaction_enabled is True
        assert policy.defaults.compaction_max_tokens == 4096
        assert policy.defaults.history_enabled is True

    def test_agent_override(self) -> None:
        policy = PlatformPolicy.load()
        # デフォルト設定を取得
        agent_policy = policy.for_agent("unknown-agent")
        assert agent_policy.rai_config == "standard-filter"

    def test_agent_specific_override(self, tmp_path) -> None:
        yaml_content = """
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
        assert agent_policy.history_enabled is True  # defaults から継承
```

- [ ] **Step 3: テストが失敗することを確認**

Run: `uv run pytest tests/platform/infrastructure/maf/test_policy.py -v`
Expected: FAIL (import error)

- [ ] **Step 4: PlatformPolicy を実装**

```python
# src/platform/infrastructure/maf/policy.py
"""プラットフォーム共通ポリシーの読み込み。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_POLICY_PATH = Path(__file__).parents[4] / "config" / "platform-policy.yaml"


@dataclass(frozen=True)
class AgentPolicy:
    """Agent 単位に解決されたポリシー。"""

    rai_config: str
    compaction_enabled: bool
    compaction_max_tokens: int
    history_enabled: bool


@dataclass
class PlatformPolicy:
    """platform-policy.yaml を読み込んで Agent 単位のポリシーを返す。"""

    defaults: AgentPolicy
    _agent_overrides: dict[str, dict[str, Any]]

    @classmethod
    def load(cls, path: Path | None = None) -> PlatformPolicy:
        """YAML ファイルからポリシーを読み込む。"""
        policy_path = path or _DEFAULT_POLICY_PATH
        with policy_path.open() as f:
            raw = yaml.safe_load(f)

        defaults_raw = raw.get("defaults", {})
        compaction = defaults_raw.get("compaction", {})

        defaults = AgentPolicy(
            rai_config=defaults_raw.get("rai_config", "standard-filter"),
            compaction_enabled=compaction.get("enabled", True),
            compaction_max_tokens=compaction.get("max_tokens", 4096),
            history_enabled=defaults_raw.get("history", {}).get("enabled", True),
        )

        return cls(
            defaults=defaults,
            _agent_overrides=raw.get("agents", {}),
        )

    def for_agent(self, agent_name: str) -> AgentPolicy:
        """Agent 名に基づいてポリシーを解決する。overrides があればマージ。"""
        overrides = self._agent_overrides.get(agent_name, {})
        if not overrides:
            return self.defaults

        compaction = overrides.get("compaction", {})
        return AgentPolicy(
            rai_config=overrides.get("rai_config", self.defaults.rai_config),
            compaction_enabled=compaction.get("enabled", self.defaults.compaction_enabled),
            compaction_max_tokens=compaction.get("max_tokens", self.defaults.compaction_max_tokens),
            history_enabled=overrides.get("history", {}).get("enabled", self.defaults.history_enabled),
        )
```

- [ ] **Step 5: テストが通ることを確認**

Run: `uv run pytest tests/platform/infrastructure/maf/test_policy.py -v`
Expected: 3 passed

- [ ] **Step 6: コミット**

```bash
git add config/platform-policy.yaml src/platform/infrastructure/maf/policy.py tests/platform/infrastructure/maf/
git commit -m "feat: PlatformPolicy (platform-policy.yaml 読み込み)"
```

---

### Task 2: AuditMiddleware — 監査ログ記録

**Files:**
- Create: `src/platform/infrastructure/maf/middleware/__init__.py`
- Create: `src/platform/infrastructure/maf/middleware/audit.py`
- Create: `tests/platform/infrastructure/maf/test_audit_middleware.py`

- [ ] **Step 1: テストを書く**

```python
# tests/platform/infrastructure/maf/test_audit_middleware.py
import pytest

from src.platform.infrastructure.maf.middleware.audit import AuditMiddleware


class TestAuditMiddleware:
    @pytest.fixture
    def middleware(self) -> AuditMiddleware:
        return AuditMiddleware()

    def test_instantiation(self, middleware: AuditMiddleware) -> None:
        assert middleware is not None

    async def test_calls_next(self, middleware: AuditMiddleware) -> None:
        called = False

        class FakeContext:
            messages: list = []
            result = None
            agent_name = "test-agent"

        async def call_next() -> None:
            nonlocal called
            called = True

        await middleware.process(FakeContext(), call_next)  # type: ignore[arg-type]
        assert called is True
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/platform/infrastructure/maf/test_audit_middleware.py -v`
Expected: FAIL (import error)

- [ ] **Step 3: AuditMiddleware を実装**

```python
# src/platform/infrastructure/maf/middleware/__init__.py
"""プラットフォーム共通 Middleware。"""

from src.platform.infrastructure.maf.middleware.audit import AuditMiddleware
from src.platform.infrastructure.maf.middleware.security import SecurityMiddleware

__all__ = ["AuditMiddleware", "SecurityMiddleware"]
```

```python
# src/platform/infrastructure/maf/middleware/audit.py
"""監査ログ Middleware。全 Agent の実行を記録する。"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from agent_framework import AgentMiddleware

if TYPE_CHECKING:
    from agent_framework import AgentContext

logger = logging.getLogger(__name__)


class AuditMiddleware(AgentMiddleware):
    """Agent 実行の監査ログを記録する。"""

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        agent_name = getattr(context, "agent_name", "unknown")
        logger.info("[Audit] Agent '%s' invocation started", agent_name)

        await call_next()

        result = getattr(context, "result", None)
        if result and getattr(result, "is_error", False):
            logger.warning("[Audit] Agent '%s' returned error", agent_name)
        else:
            logger.info("[Audit] Agent '%s' invocation completed", agent_name)
```

- [ ] **Step 4: SecurityMiddleware スタブを作成**

```python
# src/platform/infrastructure/maf/middleware/security.py
"""認可チェック Middleware (スタブ)。Azure 接続後に実装。"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from agent_framework import AgentMiddleware

if TYPE_CHECKING:
    from agent_framework import AgentContext

logger = logging.getLogger(__name__)


class SecurityMiddleware(AgentMiddleware):
    """RBAC チェック (スタブ)。Phase 2 で Entra ID 連携を実装。"""

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        # Phase 2 で実装: context からユーザー情報を取得し RBAC チェック
        await call_next()
```

- [ ] **Step 5: テストが通ることを確認**

Run: `uv run pytest tests/platform/infrastructure/maf/test_audit_middleware.py -v`
Expected: 2 passed

- [ ] **Step 6: コミット**

```bash
git add src/platform/infrastructure/maf/middleware/ tests/platform/infrastructure/maf/test_audit_middleware.py
git commit -m "feat: AuditMiddleware + SecurityMiddleware スタブ"
```

---

### Task 3: PlatformAgentBuilder — ファクトリ本体

**Files:**
- Create: `src/platform/infrastructure/maf/builder.py`
- Modify: `src/platform/infrastructure/maf/__init__.py`
- Create: `tests/platform/infrastructure/maf/test_builder.py`

- [ ] **Step 1: テストを書く**

```python
# tests/platform/infrastructure/maf/test_builder.py
import pytest
from unittest.mock import MagicMock

from agent_framework import Agent

from src.platform.infrastructure.maf.builder import PlatformAgentBuilder
from src.platform.infrastructure.maf.middleware.audit import AuditMiddleware
from src.platform.infrastructure.maf.middleware.security import SecurityMiddleware


class TestPlatformAgentBuilder:
    @pytest.fixture
    def builder(self) -> PlatformAgentBuilder:
        return PlatformAgentBuilder()

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
        middleware_types = [type(m) for m in agent._middleware]
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
        middleware_types = [type(m) for m in agent._middleware]
        assert CustomMiddleware in middleware_types
        assert AuditMiddleware in middleware_types

    def test_history_provider_injected_when_enabled(self, builder: PlatformAgentBuilder) -> None:
        client = MagicMock()
        agent = builder.build(
            client=client,
            name="test-agent",
            instructions="test",
            tools=[],
        )
        # CosmosHistoryProvider が context_providers に含まれる
        provider_types = [type(p).__name__ for p in (agent._context_providers or [])]
        assert "CosmosHistoryProvider" in provider_types

    def test_history_provider_skipped_when_disabled(self, tmp_path) -> None:
        yaml_content = """
defaults:
  rai_config: "standard-filter"
  compaction:
    enabled: false
    max_tokens: 4096
  history:
    enabled: false

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
        provider_types = [type(p).__name__ for p in (agent._context_providers or [])]
        assert "CosmosHistoryProvider" not in provider_types
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `uv run pytest tests/platform/infrastructure/maf/test_builder.py -v`
Expected: FAIL (import error)

- [ ] **Step 3: PlatformAgentBuilder を実装**

```python
# src/platform/infrastructure/maf/builder.py
"""PlatformAgentBuilder — 共通 Middleware / ContextProvider を自動注入するファクトリ。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent_framework import Agent, AgentMiddleware, BaseChatClient
from agent_framework._sessions import ContextProvider
from agent_framework_azure_cosmos import CosmosHistoryProvider

from src.platform.infrastructure.maf.middleware import AuditMiddleware, SecurityMiddleware
from src.platform.infrastructure.maf.policy import PlatformPolicy

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient


class PlatformAgentBuilder:
    """全 Agent に共通基盤を注入するファクトリ。

    REQUIRED middleware は必ず適用される。
    DEFAULT の ContextProvider は policy で無効化可能。
    """

    def __init__(
        self,
        *,
        policy_path: Path | None = None,
        cosmos_client: CosmosClient | None = None,
    ) -> None:
        self._policy = PlatformPolicy.load(policy_path)
        self._cosmos_client = cosmos_client

    def build(
        self,
        client: BaseChatClient,
        name: str,
        instructions: str,
        tools: Sequence[Callable[..., Any]],
        *,
        description: str = "",
        middleware: Sequence[AgentMiddleware] | None = None,
        context_providers: Sequence[ContextProvider] | None = None,
        **kwargs: Any,
    ) -> Agent:
        """Agent を構築する。共通 middleware / context_providers を自動注入。"""
        agent_policy = self._policy.for_agent(name)

        # REQUIRED middleware + Agent 固有
        all_middleware: list[AgentMiddleware] = [
            AuditMiddleware(),
            SecurityMiddleware(),
            *(middleware or []),
        ]

        # Context Providers
        all_providers: list[ContextProvider] = []
        if agent_policy.history_enabled:
            history = (
                CosmosHistoryProvider(cosmos_client=self._cosmos_client)
                if self._cosmos_client
                else CosmosHistoryProvider()
            )
            all_providers.append(history)
        all_providers.extend(context_providers or [])

        return Agent(
            client=client,
            name=name,
            description=description,
            instructions=instructions,
            tools=list(tools),
            middleware=all_middleware,
            context_providers=all_providers,
            **kwargs,
        )
```

- [ ] **Step 4: `__init__.py` を更新**

```python
# src/platform/infrastructure/maf/__init__.py
"""MAF インフラストラクチャ。"""

from src.platform.infrastructure.maf.builder import PlatformAgentBuilder

__all__ = ["PlatformAgentBuilder"]
```

- [ ] **Step 5: テストが通ることを確認**

Run: `uv run pytest tests/platform/infrastructure/maf/test_builder.py -v`
Expected: 5 passed

- [ ] **Step 6: コミット**

```bash
git add src/platform/infrastructure/maf/ tests/platform/infrastructure/maf/test_builder.py
git commit -m "feat: PlatformAgentBuilder (共通 middleware 自動注入)"
```

---

### Task 4: text_analyzer を PlatformAgentBuilder 経由に移行

**Files:**
- Modify: `src/platform/catalog/agents/text_analyzer/agent.py`
- Modify: `src/playground/devui.py`

- [ ] **Step 1: text_analyzer/agent.py を書き換え**

```python
# src/platform/catalog/agents/text_analyzer/agent.py
"""テキスト分析 Agent の定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent_framework import Agent, BaseChatClient

from src.platform.catalog.agents.text_analyzer.prompts import INSTRUCTIONS
from src.platform.catalog.agents.text_analyzer.tools import count_words, summarize_text
from src.platform.catalog.definitions import AgentMeta
from src.platform.infrastructure.maf import PlatformAgentBuilder

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient

AGENT_META = AgentMeta(
    name="text-analyzer",
    description="テキスト分析(単語数カウント・要約)を行う Agent",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["count_words", "summarize_text"],
)


def build_text_analyzer_agent(
    client: BaseChatClient,
    *,
    cosmos_client: CosmosClient | None = None,
) -> Agent:
    """テキスト分析 Agent を生成する。"""
    builder = PlatformAgentBuilder(cosmos_client=cosmos_client)
    return builder.build(
        client=client,
        name=AGENT_META.name,
        description=AGENT_META.description,
        instructions=INSTRUCTIONS,
        tools=[count_words, summarize_text],
    )
```

- [ ] **Step 2: devui.py から cosmos_client の渡し方を確認**

`devui.py` は既に `cosmos_client` を `build_text_analyzer_agent` に渡している。変更不要。

- [ ] **Step 3: 全テスト + 型チェック**

Run: `uv run pyright src/platform/ && uv run pytest --tb=short -q`
Expected: 0 errors, all tests pass

- [ ] **Step 4: コミット**

```bash
git add src/platform/catalog/agents/text_analyzer/agent.py
git commit -m "refactor: text_analyzer を PlatformAgentBuilder 経由に移行"
```

---

### Task 5: pyproject.toml に pyyaml 依存追加

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: pyyaml が既にあるか確認**

Run: `uv run python -c "import yaml; print(yaml.__version__)"`

- [ ] **Step 2: なければ追加**

```bash
uv add pyyaml
```

- [ ] **Step 3: コミット (追加した場合のみ)**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: pyyaml 依存追加"
```

---

### Task 6: 最終検証

- [ ] **Step 1: 全テスト**

Run: `uv run pytest --tb=short -q`
Expected: all pass

- [ ] **Step 2: 型チェック**

Run: `uv run pyright src/`
Expected: 0 errors

- [ ] **Step 3: lint**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: no errors

- [ ] **Step 4: Docker で DevUI 動作確認**

Run: `docker compose restart devui && sleep 5 && docker compose logs devui --tail 10`
Expected: 起動成功、Agent registered

---
