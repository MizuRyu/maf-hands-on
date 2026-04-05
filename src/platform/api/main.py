"""FastAPI アプリケーションのエントリポイント。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.platform.infrastructure.observability.otel.setup import setup_logging, setup_opentelemetry
from src.platform.infrastructure.settings.config import config

API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """起動時にロギングと OTel を初期化する。"""
    setup_logging()
    if config.enable_instrumentation:
        setup_opentelemetry()
    yield


def create_app() -> FastAPI:
    """FastAPI アプリケーションを生成する。"""
    app = FastAPI(title="maf API", lifespan=lifespan)

    @app.get(f"{API_PREFIX}/health")
    async def get_healthcheck() -> JSONResponse:
        return JSONResponse(content={"status": "ok"})

    return app


app = create_app()
