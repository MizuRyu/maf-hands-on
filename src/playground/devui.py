"""DevUI サーバー起動スクリプト。playground のエンティティを DevUI で提供する。"""

from __future__ import annotations

import logging
import os

DEVUI_HOST = os.getenv("DEVUI_HOST", "127.0.0.1")
DEVUI_PORT = int(os.getenv("DEVUI_PORT", "8090"))


def main() -> None:
    """DevUI サーバーを起動する。"""
    from dotenv import load_dotenv

    load_dotenv()

    from agent_framework.devui import serve

    from src.playground.agents.sample_agent import get_sample_agent
    from src.playground.aoai_client import get_aoai_client
    from src.playground.context_providers.sample_compaction import (
        _build_agent_with_sliding_window,
    )
    from src.playground.memory_state.sample_session import _build_agent as _build_session_agent
    from src.playground.middleware.sample_middleware import get_middleware_agent
    from src.playground.tools.sample_tools import get_tool_agent

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    client = get_aoai_client()

    entities = [
        get_sample_agent(client),
        get_tool_agent(client),
        get_middleware_agent(client),
        _build_session_agent(client),
        _build_agent_with_sliding_window(client),
    ]

    logger.info("Starting Playground DevUI on http://%s:%s", DEVUI_HOST, DEVUI_PORT)
    serve(entities=entities, host=DEVUI_HOST, port=DEVUI_PORT, auto_open=True)


if __name__ == "__main__":
    main()
