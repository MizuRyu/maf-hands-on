"""DevUI サーバー起動スクリプト。playground + catalog のエンティティを DevUI で提供する。"""

from __future__ import annotations

import logging
import os

DEVUI_HOST = os.getenv("DEVUI_HOST", "127.0.0.1")
DEVUI_PORT = int(os.getenv("DEVUI_PORT", "8090"))


def _get_cosmos_client():
    """emulator が 127.0.0.1 をメタデータとして返すため endpoint discovery を無効化。"""
    from azure.cosmos.aio import CosmosClient

    from src.platform.infrastructure.settings.config import config

    return CosmosClient(
        url=config.azure_cosmos_endpoint,
        credential=config.azure_cosmos_key,
        enable_endpoint_discovery=False,
    )


async def _ensure_cosmos_startup(config) -> None:
    """起動時用。asyncio.run() で完結するため専用クライアントを使い捨てる。"""
    from src.platform.infrastructure.db.cosmos.create_containers import ensure_cosmos

    client = _get_cosmos_client()
    try:
        await ensure_cosmos(client, database_name=config.azure_cosmos_database_name)
    finally:
        await client.close()


def main() -> None:
    """DevUI サーバーを起動する。"""
    from dotenv import load_dotenv

    # config モジュール読み込み前に .env をロードする
    load_dotenv()

    import asyncio

    from agent_framework.devui import serve

    from src.platform.catalog.agents.my_agent import get_my_agent
    from src.platform.catalog.workflows.my_workflow import build_my_workflow
    from src.platform.infrastructure.settings.config import config
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

    # ensure_cosmos で使うクライアントは asyncio.run() でループごと閉じるため別インスタンス
    asyncio.run(_ensure_cosmos_startup(config))

    cosmos_client = _get_cosmos_client()
    entities = [
        # --- catalog ---
        get_my_agent(client, cosmos_client=cosmos_client),
        build_my_workflow(),
        # --- playground ---
        get_sample_agent(client),
        get_tool_agent(client),
        get_middleware_agent(client),
        _build_session_agent(client),
        _build_agent_with_sliding_window(client),
    ]

    logger.info("Starting DevUI on http://%s:%s", DEVUI_HOST, DEVUI_PORT)
    serve(entities=entities, host=DEVUI_HOST, port=DEVUI_PORT, auto_open=True)


if __name__ == "__main__":
    main()
