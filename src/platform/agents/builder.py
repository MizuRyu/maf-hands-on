"""PlatformAgentBuilder — 共通 Middleware / ContextProvider を自動注入するファクトリ。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent_framework import Agent, AgentMiddleware, BaseChatClient, CompactionStrategy, ContextProvider

from src.platform.agents.middleware import AuditMiddleware, SecurityMiddleware
from src.platform.agents.policy import PlatformPolicy

if TYPE_CHECKING:
    from agent_framework import TokenizerProtocol
    from agent_framework_azure_cosmos import CosmosHistoryProvider as CosmosHistoryProviderType
    from azure.cosmos.aio import CosmosClient

    from src.platform.agents.config_loader import AgentFeatures


class PlatformAgentBuilder:
    """全 Agent に共通基盤を注入するファクトリ。

    REQUIRED middleware は必ず適用される。
    DEFAULT の ContextProvider は policy で無効化可能。
    features で history / compaction / tools / structured_output を制御。
    """

    def __init__(
        self,
        *,
        policy_path: Path | None = None,
        cosmos_client: CosmosClient | None = None,
    ) -> None:
        self._policy = PlatformPolicy.load(policy_path)
        self._cosmos_client = cosmos_client
        self._audit = AuditMiddleware()
        self._security = SecurityMiddleware()

    def _create_history_provider(self) -> CosmosHistoryProviderType:
        from agent_framework_azure_cosmos import CosmosHistoryProvider

        if self._cosmos_client:
            return CosmosHistoryProvider("cosmos-history", cosmos_client=self._cosmos_client)
        return CosmosHistoryProvider("cosmos-history")

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
        features: AgentFeatures | None = None,
        compaction_strategy: CompactionStrategy | None = None,
        tokenizer: TokenizerProtocol | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> Agent:
        """Agent を構築する。共通 middleware / context_providers を自動注入。

        features が指定された場合、policy のデフォルトより features を優先する。
        """
        agent_policy = self._policy.for_agent(name)

        # features でのオーバーライド判定
        history_enabled = features.history if features else agent_policy.history_enabled
        tools_enabled = features.tools if features else True

        # REQUIRED middleware (先頭) + Agent 固有 (末尾)
        all_middleware: list[AgentMiddleware] = [
            self._audit,
            self._security,
            *(middleware or []),
        ]

        # Context Providers
        all_providers: list[ContextProvider] = []
        if history_enabled:
            all_providers.append(self._create_history_provider())
        all_providers.extend(context_providers or [])

        # Tools
        resolved_tools = list(tools) if tools_enabled else []

        # default_options (response_format 用)
        # ChatOptions は TypedDict のため cast で型合わせ
        opts: Any = None
        if response_format:
            opts = {"response_format": response_format}

        return Agent(
            client=client,
            name=name,
            description=description,
            instructions=instructions,
            tools=resolved_tools,
            middleware=all_middleware,
            context_providers=all_providers,
            compaction_strategy=compaction_strategy,
            tokenizer=tokenizer,
            default_options=opts,
        )
