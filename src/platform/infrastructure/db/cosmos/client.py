"""Cosmos DB クライアント管理。

FastAPI lifespan 内でインスタンスを初期化し、
各リポジトリに CosmosClient を共有する。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy

if TYPE_CHECKING:
    from azure.identity.aio import DefaultAzureCredential

    from src.platform.infrastructure.settings.config import Config

logger = logging.getLogger(__name__)


class CosmosClientManager:
    """CosmosClient のライフサイクルを管理するシングルトン。"""

    def __init__(self, config: Config) -> None:
        self._endpoint = config.azure_cosmos_endpoint
        self._database_name = config.azure_cosmos_database_name
        self._client: CosmosClient | None = None
        self._database: DatabaseProxy | None = None
        self._credential: DefaultAzureCredential | None = None

    async def initialize(self) -> None:
        """CosmosClient を初期化し、データベースプロキシを取得する。"""
        from azure.identity.aio import DefaultAzureCredential

        self._credential = DefaultAzureCredential()
        self._client = CosmosClient(self._endpoint, credential=self._credential)
        self._database = self._client.get_database_client(self._database_name)
        logger.info(
            "Cosmos DB client initialized: endpoint=%s, database=%s",
            self._endpoint,
            self._database_name,
        )

    async def close(self) -> None:
        """CosmosClient と Credential を閉じる。"""
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._database = None
        if self._credential is not None:
            await self._credential.close()
            self._credential = None
            logger.info("Cosmos DB client closed")

    def get_container(self, container_name: str) -> ContainerProxy:
        """コンテナプロキシを取得する。"""
        if self._database is None:
            msg = "CosmosClientManager is not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return self._database.get_container_client(container_name)

    @property
    def database(self) -> DatabaseProxy:
        """データベースプロキシを取得する。"""
        if self._database is None:
            msg = "CosmosClientManager is not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return self._database
