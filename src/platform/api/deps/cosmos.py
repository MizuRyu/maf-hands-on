"""Cosmos DB クライアントの DI プロバイダ。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy

from src.platform.infrastructure.settings.config import config

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_cosmos_client: CosmosClient | None = None


async def get_cosmos_client() -> AsyncIterator[CosmosClient]:
    """CosmosClient をリクエストスコープで提供する。"""
    global _cosmos_client
    if _cosmos_client is None:
        _cosmos_client = CosmosClient(
            url=config.azure_cosmos_endpoint,
            credential=config.azure_cosmos_key,
            enable_endpoint_discovery=False,
        )
    yield _cosmos_client


async def get_database(
    client: CosmosClient,
) -> DatabaseProxy:
    """データベースプロキシを取得する。"""
    return client.get_database_client(config.azure_cosmos_database_name)


async def get_container(
    database: DatabaseProxy,
    container_name: str,
) -> ContainerProxy:
    """コンテナプロキシを取得する。"""
    return database.get_container_client(container_name)
