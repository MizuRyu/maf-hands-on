"""エージェント構築基盤。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.platform.agents._types import AgentMeta

if TYPE_CHECKING:
    from src.platform.agents.factory import PlatformAgentFactory

__all__ = ["AgentMeta", "PlatformAgentFactory"]


def __getattr__(name: str):
    """PlatformAgentFactory を遅延 import する (agent_framework 依存を遅延)。"""
    if name == "PlatformAgentFactory":
        from src.platform.agents.factory import PlatformAgentFactory

        return PlatformAgentFactory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
