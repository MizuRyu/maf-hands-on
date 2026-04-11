"""Cosmos DB CheckpointStorage のテスト。

CheckpointStorage Protocol の 6 メソッドと
シリアライズ/デシリアライズの roundtrip を検証する。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent_framework import WorkflowCheckpoint
from azure.cosmos.exceptions import CosmosHttpResponseError

from src.platform.infrastructure.db.cosmos.checkpoint_storage import (
    CosmosCheckpointStorage,
    _from_document,
    _to_document,
)


def _make_checkpoint(**overrides: object) -> WorkflowCheckpoint:
    defaults: dict = {
        "workflow_name": "test-wf",
        "graph_signature_hash": "hash123",
        "checkpoint_id": "cp-1",
        "previous_checkpoint_id": None,
        "timestamp": 1704067200.0,
        "messages": {"key": "value"},
        "state": {"step": "done"},
        "pending_request_info_events": {},
        "iteration_count": 5,
        "metadata": {"author": "test"},
        "version": "1.0",
    }
    defaults.update(overrides)
    return WorkflowCheckpoint(**defaults)


def _checkpoint_doc(**overrides: object) -> dict:
    defaults: dict = {
        "id": "cp-1",
        "checkpointId": "cp-1",
        "workflowName": "test-wf",
        "graphSignatureHash": "hash123",
        "previousCheckpointId": None,
        "timestamp": 1704067200.0,
        "messagesJson": json.dumps({"key": "value"}),
        "stateJson": json.dumps({"step": "done"}),
        "pendingEventsJson": json.dumps({}),
        "iterationCount": 5,
        "metadata": {"author": "test"},
        "version": "1.0",
    }
    defaults.update(overrides)
    return defaults


def _mock_container() -> MagicMock:
    container = MagicMock()
    container.read_item = AsyncMock()
    container.upsert_item = AsyncMock()
    container.delete_item = AsyncMock()
    container.query_items = MagicMock()
    return container


class _AsyncIter:
    """query_items の戻り値をモックする非同期イテレータ。"""

    def __init__(self, items: list) -> None:
        self._items = iter(items)

    def __aiter__(self) -> _AsyncIter:
        return self

    async def __anext__(self) -> dict:
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration from None


# ── シリアライズ ──


class TestCheckpointSerialization:
    def test_to_document_roundtrip(self) -> None:
        cp = _make_checkpoint()
        doc = _to_document(cp)
        restored = _from_document(doc)

        assert restored.checkpoint_id == cp.checkpoint_id
        assert restored.workflow_name == cp.workflow_name
        assert restored.messages == cp.messages
        assert restored.state == cp.state
        assert restored.iteration_count == cp.iteration_count
        assert restored.version == cp.version

    def test_to_document_serializes_complex_fields_as_json(self) -> None:
        cp = _make_checkpoint(
            messages={"a": [1, 2]},
            state={"b": True},
            pending_request_info_events={"ev": "data"},
        )
        doc = _to_document(cp)

        assert isinstance(doc["messagesJson"], str)
        assert json.loads(doc["messagesJson"]) == {"a": [1, 2]}
        assert json.loads(doc["stateJson"]) == {"b": True}
        assert json.loads(doc["pendingEventsJson"]) == {"ev": "data"}

    def test_from_document_handles_missing_optional_fields(self) -> None:
        """iterationCount/metadata/version が欠落時のデフォルト値。"""
        doc = _checkpoint_doc()
        del doc["iterationCount"]
        del doc["metadata"]
        del doc["version"]

        restored = _from_document(doc)

        assert restored.iteration_count == 0
        assert restored.metadata == {}
        assert restored.version == "1.0"


# ── Storage CRUD ──


class TestCosmosCheckpointStorage:
    async def test_save_returns_checkpoint_id(self) -> None:
        container = _mock_container()
        storage = CosmosCheckpointStorage(container)
        cp = _make_checkpoint()

        result = await storage.save(cp)

        assert result == "cp-1"
        container.upsert_item.assert_awaited_once()

    async def test_load_returns_checkpoint(self) -> None:
        container = _mock_container()
        container.read_item.return_value = _checkpoint_doc()
        storage = CosmosCheckpointStorage(container)

        result = await storage.load("cp-1")

        assert isinstance(result, WorkflowCheckpoint)
        assert result.checkpoint_id == "cp-1"
        assert result.workflow_name == "test-wf"
        container.read_item.assert_awaited_once_with(item="cp-1", partition_key="cp-1")

    async def test_load_not_found_raises_checkpoint_exception(self) -> None:
        container = _mock_container()
        container.read_item.side_effect = CosmosHttpResponseError(status_code=404, message="not found")
        storage = CosmosCheckpointStorage(container)

        from agent_framework.exceptions import WorkflowCheckpointException

        with pytest.raises(WorkflowCheckpointException, match="cp-missing"):
            await storage.load("cp-missing")

    async def test_delete_existing_returns_true(self) -> None:
        container = _mock_container()
        storage = CosmosCheckpointStorage(container)

        result = await storage.delete("cp-1")

        assert result is True
        container.delete_item.assert_awaited_once_with(item="cp-1", partition_key="cp-1")

    async def test_delete_not_found_returns_false(self) -> None:
        container = _mock_container()
        container.delete_item.side_effect = CosmosHttpResponseError(status_code=404, message="not found")
        storage = CosmosCheckpointStorage(container)

        result = await storage.delete("missing")

        assert result is False

    async def test_list_checkpoints_returns_all_for_workflow(self) -> None:
        container = _mock_container()
        container.query_items.return_value = _AsyncIter(
            [_checkpoint_doc(), _checkpoint_doc(checkpointId="cp-2", id="cp-2")]
        )
        storage = CosmosCheckpointStorage(container)

        results = await storage.list_checkpoints(workflow_name="test-wf")

        assert len(results) == 2
        assert results[0].checkpoint_id == "cp-1"

    async def test_get_latest_returns_newest(self) -> None:
        container = _mock_container()
        container.query_items.return_value = _AsyncIter([_checkpoint_doc()])
        storage = CosmosCheckpointStorage(container)

        result = await storage.get_latest(workflow_name="test-wf")

        assert result is not None
        assert result.checkpoint_id == "cp-1"

    async def test_get_latest_returns_none_when_empty(self) -> None:
        container = _mock_container()
        container.query_items.return_value = _AsyncIter([])
        storage = CosmosCheckpointStorage(container)

        result = await storage.get_latest(workflow_name="test-wf")

        assert result is None

    async def test_list_checkpoint_ids(self) -> None:
        container = _mock_container()
        container.query_items.return_value = _AsyncIter([{"checkpointId": "cp-1"}, {"checkpointId": "cp-2"}])
        storage = CosmosCheckpointStorage(container)

        ids = await storage.list_checkpoint_ids(workflow_name="test-wf")

        assert ids == ["cp-1", "cp-2"]

    async def test_list_checkpoint_ids_empty(self) -> None:
        container = _mock_container()
        container.query_items.return_value = _AsyncIter([])
        storage = CosmosCheckpointStorage(container)

        ids = await storage.list_checkpoint_ids(workflow_name="test-wf")

        assert ids == []
