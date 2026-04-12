"""Platform DevUI サーバー。platform の Agent / Workflow を DevUI で提供する。

OTel は DevUI の TracerProvider 初期化より先に、MAF 公式ヘルパーで exporter を設定する。
"""

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
    """Platform DevUI サーバーを起動する。"""
    from dotenv import load_dotenv

    load_dotenv()

    import asyncio

    from src.platform.infrastructure.observability.otel.setup import setup_opentelemetry

    setup_opentelemetry()

    from agent_framework.devui import serve

    from src.platform.agents.text_analyzer import build_text_analyzer_agent
    from src.platform.infrastructure.settings.config import config
    from src.platform.workflows.text_pipeline import build_text_pipeline_workflow
    from src.playground.aoai_client import get_aoai_client

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    client = get_aoai_client()

    asyncio.run(_ensure_cosmos_startup(config))

    cosmos_client = _get_cosmos_client()
    entities = [
        build_text_analyzer_agent(client, cosmos_client=cosmos_client),
        build_text_pipeline_workflow(),
    ]

    logger.info("Starting Platform DevUI on http://%s:%s", DEVUI_HOST, DEVUI_PORT)
    serve(entities=entities, host=DEVUI_HOST, port=DEVUI_PORT, auto_open=True)


if __name__ == "__main__":
    main()
