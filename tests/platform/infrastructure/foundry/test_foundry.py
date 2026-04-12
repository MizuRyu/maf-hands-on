"""Foundry 同期 (Phase 4) のユニットテスト。"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.exceptions import NotFoundError
from src.platform.domain.registry.models.agent_spec import AgentSpec
from src.platform.infrastructure.foundry.agent_sync import (
    FoundryAgentSyncAdapter,
    FoundrySyncResult,
    SyncStatus,
    apply_sync_result,
)
from src.platform.infrastructure.foundry.eval_client import (
    EvalRunStatus,
    FoundryEvalClient,
)


def _make_spec(**overrides: object) -> AgentSpec:
    now = datetime.now(UTC)
    defaults = {
        "spec_id": "spec-1",
        "name": "test-agent",
        "version": 1,
        "model_id": "gpt-5-nano",
        "instructions": "test",
        "status": SpecStatus.ACTIVE,
        "created_by": "user-1",
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return AgentSpec(**defaults)  # type: ignore[arg-type]


class TestFoundryAgentSyncAdapter:
    async def test_sync_dry_run_returns_success(self) -> None:
        """dry_run モードで同期が成功する。"""
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        spec = _make_spec()
        result = await adapter.sync_agent_to_foundry(spec)
        assert result.status == SyncStatus.SUCCESS
        assert result.foundry_agent_name == "foundry-test-agent"
        assert result.foundry_agent_version == "v1"
        assert result.synced_at is not None

    async def test_sync_no_dry_run_returns_skipped(self) -> None:
        """dry_run=False で Foundry API 未設定の場合はスキップされる。"""
        adapter = FoundryAgentSyncAdapter(dry_run=False)
        spec = _make_spec()
        result = await adapter.sync_agent_to_foundry(spec)
        assert result.status == SyncStatus.SKIPPED
        assert result.error is not None

    async def test_get_status_dry_run(self) -> None:
        """dry_run モードでステータスが取得できる。"""
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        status = await adapter.get_foundry_agent_status("foundry-test")
        assert status["status"] == "deployed"

    async def test_delete_dry_run(self) -> None:
        """dry_run モードで削除が成功する。"""
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        result = await adapter.delete_foundry_agent("foundry-test")
        assert result.status == SyncStatus.SUCCESS


class TestApplySyncResult:
    def test_success_updates_spec(self) -> None:
        """成功結果で AgentSpec が更新される。"""
        spec = _make_spec()
        now = datetime.now(UTC)
        result = FoundrySyncResult(
            status=SyncStatus.SUCCESS,
            foundry_agent_name="foundry-test-agent",
            foundry_agent_version="v1",
            synced_at=now,
        )
        updated = apply_sync_result(spec, result)
        assert updated.foundry_agent_name == "foundry-test-agent"
        assert updated.foundry_synced_at == now

    def test_failed_leaves_spec_unchanged(self) -> None:
        """失敗結果では AgentSpec は変更されない。"""
        spec = _make_spec()
        result = FoundrySyncResult(
            status=SyncStatus.FAILED,
            error="some error",
        )
        updated = apply_sync_result(spec, result)
        assert updated.foundry_agent_name is None


class TestFoundryEvalClient:
    async def test_submit_dry_run(self) -> None:
        """dry_run モードで eval 実行が完了する。"""
        client = FoundryEvalClient(dry_run=True)
        run_id = await client.submit_eval_run(
            dataset_path="data.jsonl",
            evaluator_names=["relevance"],
        )
        assert run_id is not None

        result = await client.get_eval_results(run_id)
        assert result.status == EvalRunStatus.COMPLETED
        assert "relevance" in result.metrics

    async def test_get_unknown_run(self) -> None:
        """存在しない run_id は FAILED を返す。"""
        client = FoundryEvalClient(dry_run=True)
        result = await client.get_eval_results("non-existent-id")
        assert result.status == EvalRunStatus.FAILED


class TestFoundrySyncService:
    async def test_sync_agent_success(self) -> None:
        """sync_agent が成功する。"""
        from src.platform.application.foundry_sync_service import FoundrySyncService

        spec = _make_spec()
        repo = AsyncMock()
        repo.get.return_value = spec
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        service = FoundrySyncService(agent_spec_repo=repo, foundry_adapter=adapter)

        result = await service.sync_agent("spec-1")
        assert result.status == SyncStatus.SUCCESS
        repo.update.assert_called_once()

    async def test_sync_agent_not_found(self) -> None:
        """存在しない spec_id は NotFoundError。"""
        from src.platform.application.foundry_sync_service import FoundrySyncService

        repo = AsyncMock()
        repo.get.side_effect = NotFoundError("AgentSpec", "non-existent")
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        service = FoundrySyncService(agent_spec_repo=repo, foundry_adapter=adapter)

        with pytest.raises(NotFoundError):
            await service.sync_agent("non-existent")

    async def test_get_sync_status_not_synced(self) -> None:
        """Foundry 未同期の場合は synced=False。"""
        from src.platform.application.foundry_sync_service import FoundrySyncService

        spec = _make_spec()
        repo = AsyncMock()
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        service = FoundrySyncService(agent_spec_repo=repo, foundry_adapter=adapter)

        status = await service.get_sync_status(spec)
        assert status["synced"] is False

    async def test_get_sync_status_synced(self) -> None:
        """Foundry 同期済みの場合は詳細を返す。"""
        from src.platform.application.foundry_sync_service import FoundrySyncService

        spec = _make_spec(
            foundry_agent_name="foundry-test",
            foundry_agent_version="v1",
            foundry_synced_at=datetime.now(UTC),
        )
        repo = AsyncMock()
        adapter = FoundryAgentSyncAdapter(dry_run=True)
        service = FoundrySyncService(agent_spec_repo=repo, foundry_adapter=adapter)

        status = await service.get_sync_status(spec)
        assert status["synced"] is True
        assert status["foundry_agent_name"] == "foundry-test"
