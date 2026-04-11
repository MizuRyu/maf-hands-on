"""Cosmos DB による CheckpointStorage 実装。

MAF の CheckpointStorage Protocol を実装し、
ワークフローチェックポイントを Cosmos DB に永続化する。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_framework import WorkflowCheckpoint
from agent_framework._workflows._checkpoint import CheckpointID
from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.exceptions import NotFoundError
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
)

logger = logging.getLogger(__name__)

CONTAINER_NAME = "checkpoints"


class CosmosCheckpointStorage:
    """checkpoints コンテナに対する CheckpointStorage 実装。

    PK: /checkpointId（フラット）。
    MAF の load(checkpoint_id) は checkpoint_id しか受け取らないため、
    階層 PK は使用しない。
    """

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def save(self, checkpoint: WorkflowCheckpoint) -> CheckpointID:
        """チェックポイントを保存して ID を返す。"""
        doc = _to_document(checkpoint)
        async with cosmos_error_handler("Checkpoint", checkpoint.checkpoint_id):
            await self._container.upsert_item(body=doc)
        logger.debug("Saved checkpoint %s", checkpoint.checkpoint_id)
        return checkpoint.checkpoint_id

    async def load(self, checkpoint_id: CheckpointID) -> WorkflowCheckpoint:
        """ID でチェックポイントを読み込む。"""
        from agent_framework.exceptions import WorkflowCheckpointException

        try:
            async with cosmos_error_handler("Checkpoint", checkpoint_id):
                doc = await self._container.read_item(item=checkpoint_id, partition_key=checkpoint_id)
        except NotFoundError as e:
            raise WorkflowCheckpointException(f"No checkpoint found with ID {checkpoint_id}") from e
        return _from_document(doc)

    async def list_checkpoints(self, *, workflow_name: str) -> list[WorkflowCheckpoint]:
        """ワークフロー名でチェックポイントを一覧取得する。"""
        query = "SELECT * FROM c WHERE c.workflowName = @wfName"
        params: list[dict[str, object]] = [{"name": "@wfName", "value": workflow_name}]
        items: list[WorkflowCheckpoint] = []
        async for item in self._container.query_items(query=query, parameters=params):
            items.append(_from_document(item))
        return items

    async def delete(self, checkpoint_id: CheckpointID) -> bool:
        """ID でチェックポイントを削除する。"""
        try:
            async with cosmos_error_handler("Checkpoint", checkpoint_id):
                await self._container.delete_item(item=checkpoint_id, partition_key=checkpoint_id)
            logger.debug("Deleted checkpoint %s", checkpoint_id)
            return True
        except NotFoundError:
            return False

    async def get_latest(self, *, workflow_name: str) -> WorkflowCheckpoint | None:
        """ワークフロー名で最新のチェックポイントを取得する。"""
        query = "SELECT TOP 1 * FROM c WHERE c.workflowName = @wfName ORDER BY c.timestamp DESC"
        params: list[dict[str, object]] = [{"name": "@wfName", "value": workflow_name}]
        async for item in self._container.query_items(query=query, parameters=params):
            return _from_document(item)
        return None

    async def list_checkpoint_ids(self, *, workflow_name: str) -> list[CheckpointID]:
        """ワークフロー名でチェックポイント ID を一覧取得する。"""
        query = "SELECT c.checkpointId FROM c WHERE c.workflowName = @wfName"
        params: list[dict[str, object]] = [{"name": "@wfName", "value": workflow_name}]
        ids: list[CheckpointID] = []
        async for item in self._container.query_items(query=query, parameters=params):
            ids.append(item["checkpointId"])
        return ids


def _to_document(checkpoint: WorkflowCheckpoint) -> dict[str, Any]:
    """WorkflowCheckpoint を Cosmos DB ドキュメントに変換する。

    複雑なネスト構造（messages, state, pending_request_info_events）は
    JSON 文字列としてシリアライズし、Cosmos のクエリに影響しないようにする。
    """
    return {
        "id": checkpoint.checkpoint_id,
        "checkpointId": checkpoint.checkpoint_id,
        "workflowName": checkpoint.workflow_name,
        "graphSignatureHash": checkpoint.graph_signature_hash,
        "previousCheckpointId": checkpoint.previous_checkpoint_id,
        "timestamp": checkpoint.timestamp,
        "messagesJson": json.dumps(checkpoint.messages, default=str),
        "stateJson": json.dumps(checkpoint.state, default=str),
        "pendingEventsJson": json.dumps(checkpoint.pending_request_info_events, default=str),
        "iterationCount": checkpoint.iteration_count,
        "metadata": checkpoint.metadata,
        "version": checkpoint.version,
    }


def _from_document(doc: dict[str, Any]) -> WorkflowCheckpoint:
    """Cosmos DB ドキュメントから WorkflowCheckpoint を復元する。"""
    messages = json.loads(doc.get("messagesJson", "[]"))
    state = json.loads(doc.get("stateJson", "{}"))
    pending_events = json.loads(doc.get("pendingEventsJson", "[]"))

    return WorkflowCheckpoint.from_dict(
        {
            "workflow_name": doc["workflowName"],
            "graph_signature_hash": doc["graphSignatureHash"],
            "checkpoint_id": doc["checkpointId"],
            "previous_checkpoint_id": doc.get("previousCheckpointId"),
            "timestamp": doc["timestamp"],
            "messages": messages,
            "state": state,
            "pending_request_info_events": pending_events,
            "iteration_count": doc.get("iterationCount", 0),
            "metadata": doc.get("metadata", {}),
            "version": doc.get("version", "1.0"),
        }
    )
