"""認可チェック Middleware (スタブ)。Phase 2 で Entra ID 連携を実装する。"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from agent_framework import AgentMiddleware

if TYPE_CHECKING:
    from agent_framework import AgentContext

logger = logging.getLogger(__name__)


class SecurityMiddleware(AgentMiddleware):
    """RBAC チェック (スタブ)。"""

    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        await call_next()
