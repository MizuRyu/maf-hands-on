"""FastAPI アプリケーションのエントリポイント。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from azure.cosmos.aio import CosmosClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.platform.infrastructure.db.cosmos.create_containers import ensure_cosmos
from src.platform.infrastructure.observability.otel.setup import setup_logging, setup_opentelemetry
from src.platform.infrastructure.settings.config import config

logger = logging.getLogger(__name__)

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """起動時にロギング・OTel・Cosmos DB を初期化する。"""
    setup_logging()
    if config.enable_instrumentation:
        setup_opentelemetry()

    cosmos_client = CosmosClient(
        url=config.azure_cosmos_endpoint,
        credential=config.azure_cosmos_key,
        enable_endpoint_discovery=False,
    )
    try:
        await ensure_cosmos(cosmos_client, database_name=config.azure_cosmos_database_name)
    except Exception:
        logger.warning("Cosmos DB initialization skipped (endpoint unreachable)")
    finally:
        await cosmos_client.close()

    yield


def create_app() -> FastAPI:
    """FastAPI アプリケーションを生成する。"""
    app = FastAPI(title="maf API", lifespan=lifespan)

    @app.get(f"{API_PREFIX}/health")
    async def get_healthcheck() -> JSONResponse:
        return JSONResponse(content={"status": "ok"})

    return app


app = create_app()
