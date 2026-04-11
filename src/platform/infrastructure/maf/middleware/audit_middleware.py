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
