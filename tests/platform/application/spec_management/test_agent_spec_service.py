"""AgentSpecService のユニットテスト。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.platform.application.spec_management.agent_spec_service import (
    AgentSpecService,
)
from src.platform.domain.common.enums import SpecStatus


class TestAgentSpecService:
    @pytest.fixture
    def repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, repo: AsyncMock) -> AgentSpecService:
        return AgentSpecService(repo)

    async def test_register_creates_spec(self, service: AgentSpecService, repo: AsyncMock) -> None:
        """register は新しい AgentSpec を作成してリポジトリに保存する。"""
        repo.create.return_value = MagicMock(spec_id="new-id")
        await service.register(
            name="test-agent",
            version=1,
            model_id="gpt-4o",
            instructions="テスト",
        )
        repo.create.assert_called_once()
        created_spec = repo.create.call_args[0][0]
        assert created_spec.name == "test-agent"
        assert created_spec.version == 1
        assert created_spec.status == SpecStatus.DRAFT

    async def test_update_merges_fields(self, service: AgentSpecService, repo: AsyncMock) -> None:
        """update は指定フィールドのみ更新する。"""
        existing = MagicMock()
        existing.name = "old-name"
        existing.model_id = "gpt-4o"
        existing.instructions = "old"
        existing.description = None
        existing.tool_ids = []
        existing.middleware_config = []
        existing.context_provider_config = []
        existing.response_format = None
        existing.status = SpecStatus.DRAFT
        existing.created_by = "user1"
        existing.schema_version = 1
        existing.created_at = MagicMock()
        existing.updated_at = MagicMock()
        existing.version = 1
        existing.spec_id = "spec-123"
        existing.foundry_agent_name = None
        existing.foundry_agent_version = None
        existing.foundry_deployment_type = None
        existing.foundry_synced_at = None

        # frozen dataclass のため MagicMock ではなく実際のドメインモデルを使う
        from datetime import UTC, datetime

        from src.platform.domain.common.types import SpecId, UserId
        from src.platform.domain.registry.models.agent_spec import AgentSpec

        spec = AgentSpec(
            spec_id=SpecId("spec-123"),
            name="old-name",
            version=1,
            model_id="gpt-4o",
            instructions="old",
            status=SpecStatus.DRAFT,
            created_by=UserId("user1"),
            schema_version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.get.return_value = spec
        repo.update.return_value = MagicMock()
        await service.update("spec-123", name="new-name")
        updated = repo.update.call_args[0][0]
        assert updated.name == "new-name"
        assert updated.instructions == "old"

    async def test_archive_changes_status(self, service: AgentSpecService, repo: AsyncMock) -> None:
        """archive はステータスを ARCHIVED に変更する。"""
        from datetime import UTC, datetime

        from src.platform.domain.common.types import SpecId, UserId
        from src.platform.domain.registry.models.agent_spec import AgentSpec

        spec = AgentSpec(
            spec_id=SpecId("spec-123"),
            name="test",
            version=1,
            model_id="gpt-4o",
            instructions="test",
            status=SpecStatus.ACTIVE,
            created_by=UserId("user1"),
            schema_version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.get.return_value = spec
        repo.update.return_value = MagicMock()
        await service.archive("spec-123")
        archived = repo.update.call_args[0][0]
        assert archived.status == SpecStatus.ARCHIVED
