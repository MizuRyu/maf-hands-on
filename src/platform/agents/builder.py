"""PlatformAgentBuilder — 共通 Middleware / ContextProvider を自動注入するファクトリ。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent_framework import Agent, AgentMiddleware, BaseChatClient
from agent_framework._sessions import ContextProvider
from agent_framework_azure_cosmos import CosmosHistoryProvider

from src.platform.agents.middleware import AuditMiddleware, SecurityMiddleware
from src.platform.agents.policy import PlatformPolicy

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

        # REQUIRED middleware (先頭) + Agent 固有 (末尾)
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
