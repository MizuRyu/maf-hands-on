"""FastAPI アプリケーションのエントリポイント。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from azure.cosmos.aio import CosmosClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.platform.api.routers import agents, executions, platform, sessions, tools, workflows
from src.platform.domain.common.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.platform.infrastructure.db.cosmos.create_containers import ensure_cosmos
from src.platform.infrastructure.observability.otel.setup import setup_logging, setup_opentelemetry
from src.platform.infrastructure.settings.config import config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """起動時にロギング・OTel・Cosmos DB を初期化する。"""
    setup_logging()
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

    # ドメイン例外 → HTTP レスポンス変換
    @app.exception_handler(NotFoundError)
    async def _not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "error_type": "not_found"},
        )

    @app.exception_handler(ConflictError)
    async def _conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "error_type": "conflict"},
        )

    @app.exception_handler(ValidationError)
    async def _validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "error_type": "validation"},
        )

    # ルーター登録
    app.include_router(agents.router)
    app.include_router(sessions.router)
    app.include_router(workflows.router)
    app.include_router(executions.router)
    app.include_router(tools.router)
    app.include_router(platform.router)

    from src.platform.api.schemas.common import API_PREFIX

    @app.get(f"{API_PREFIX}/health")
    async def get_healthcheck() -> JSONResponse:
        return JSONResponse(content={"status": "ok"})

    # 静的ファイル配信
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


app = create_app()
