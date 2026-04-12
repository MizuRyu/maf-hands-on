"""Cosmos DB データベース・コンテナの冪等作成。"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from azure.cosmos import PartitionKey

from src.platform.infrastructure.db.cosmos.client import CosmosClientManager

if TYPE_CHECKING:
    from azure.cosmos.aio import CosmosClient

logger = logging.getLogger(__name__)

CONTAINER_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "agent_specs",
        "partition_key": PartitionKey(path="/id"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/status/?"},
                {"path": "/name/?"},
                {"path": "/createdAt/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "tool_specs",
        "partition_key": PartitionKey(path="/id"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/status/?"},
                {"path": "/name/?"},
                {"path": "/toolType/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "workflows",
        "partition_key": PartitionKey(path="/id"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/name/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "workflow_executions",
        "partition_key": PartitionKey(path="/id"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/workflowId/?"},
                {"path": "/status/?"},
                {"path": "/startedAt/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "workflow_execution_steps",
        "partition_key": PartitionKey(path="/workflowExecutionId"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/status/?"},
                {"path": "/stepId/?"},
                {"path": "/createdAt/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "checkpoints",
        "partition_key": PartitionKey(path="/checkpointId"),
        "default_ttl": 2592000,  # 30 days
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/workflowName/?"},
                {"path": "/workflowExecutionId/?"},
                {"path": "/timestamp/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "sessions",
        "partition_key": PartitionKey(path="/sessionId"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/userId/?"},
                {"path": "/status/?"},
                {"path": "/createdAt/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "agent_runs",
        "partition_key": PartitionKey(path="/agentId"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/status/?"},
                {"path": "/createdBy/?"},
                {"path": "/startedAt/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
    {
        "id": "users",
        "partition_key": PartitionKey(path="/id"),
        "indexing_policy": {
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/email/?"},
                {"path": "/role/?"},
                {"path": "/status/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    },
]


async def ensure_cosmos(client: CosmosClient, database_name: str = "maf") -> None:
    """データベースと全コンテナを冪等に作成する。"""
    database = await client.create_database_if_not_exists(database_name)

    for definition in CONTAINER_DEFINITIONS:
        container_id = definition["id"]
        kwargs: dict[str, Any] = {
            "id": container_id,
            "partition_key": definition["partition_key"],
            "indexing_policy": definition["indexing_policy"],
        }
        if "default_ttl" in definition:
            kwargs["default_ttl"] = definition["default_ttl"]

        await database.create_container_if_not_exists(**kwargs)
        logger.info("Container ensured: %s", container_id)

    logger.info("Cosmos DB ready: database=%s, containers=%d", database_name, len(CONTAINER_DEFINITIONS))


async def create_containers(manager: CosmosClientManager) -> None:
    """CosmosClientManager 経由で全コンテナを作成する（冪等）。"""
    database = manager.database
    for definition in CONTAINER_DEFINITIONS:
        container_id = definition["id"]
        kwargs: dict[str, Any] = {
            "id": container_id,
            "partition_key": definition["partition_key"],
            "indexing_policy": definition["indexing_policy"],
        }
        if "default_ttl" in definition:
            kwargs["default_ttl"] = definition["default_ttl"]

        await database.create_container_if_not_exists(**kwargs)
        logger.info("Container ensured: %s", container_id)

    logger.info("All containers created successfully")


async def main() -> None:
    """CLI エントリポイント。"""
    from src.platform.infrastructure.settings.config import Config

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = Config()
    manager = CosmosClientManager(config)
    try:
        await manager.initialize()
        await create_containers(manager)
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
