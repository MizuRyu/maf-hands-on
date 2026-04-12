"""エージェント構築基盤。"""

from src.platform.agents._types import AgentMeta

__all__ = ["AgentMeta", "PlatformAgentBuilder"]


def __getattr__(name: str):
    """PlatformAgentBuilder を遅延 import する (agent_framework 依存を遅延)。"""
    if name == "PlatformAgentBuilder":
        from src.platform.agents.builder import PlatformAgentBuilder

        return PlatformAgentBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
