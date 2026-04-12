"""API ルーターのユニットテスト。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.platform.domain.common.enums import SpecStatus
from src.platform.domain.common.exceptions import NotFoundError
from src.platform.domain.common.types import SpecId, UserId
from src.platform.domain.registry.models.agent_spec import AgentSpec


def _make_agent_spec(**overrides: Any) -> AgentSpec:
    """テスト用の AgentSpec を作成する。"""
    now = datetime.now(UTC)
    defaults = {
        "spec_id": SpecId("spec-1"),
        "name": "test-agent",
        "version": 1,
        "model_id": "gpt-5-nano",
        "instructions": "テスト用",
        "status": SpecStatus.DRAFT,
        "created_by": UserId("user1"),
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return AgentSpec(**defaults)


@pytest.fixture
def mock_agent_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_agent_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_agent_repo: AsyncMock, mock_agent_service: AsyncMock) -> TestClient:
    """ルーター付きの TestClient を生成する。"""
    from fastapi import FastAPI

    from src.platform.api.deps.services import get_agent_spec_repo, get_agent_spec_service
    from src.platform.api.routers import agents
    from src.platform.domain.common.exceptions import NotFoundError

    app = FastAPI()

    @app.exception_handler(NotFoundError)
    async def _not_found_handler(_request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.include_router(agents.router)
    app.dependency_overrides[get_agent_spec_repo] = lambda: mock_agent_repo
    app.dependency_overrides[get_agent_spec_service] = lambda: mock_agent_service
    return TestClient(app)


class TestAgentsRouter:
    def test_create_agent(self, client: TestClient, mock_agent_service: AsyncMock) -> None:
        """POST /api/agents は 201 を返す。"""
        mock_agent_service.register.return_value = _make_agent_spec()
        resp = client.post(
            "/api/agents",
            json={
                "name": "test-agent",
                "version": 1,
                "model_id": "gpt-5-nano",
                "instructions": "テスト",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["name"] == "test-agent"

    def test_get_agent(self, client: TestClient, mock_agent_repo: AsyncMock) -> None:
        """GET /api/agents/{spec_id} はエージェント情報を返す。"""
        mock_agent_repo.get.return_value = _make_agent_spec()
        resp = client.get("/api/agents/spec-1")
        assert resp.status_code == 200
        assert resp.json()["data"]["spec_id"] == "spec-1"

    def test_get_agent_not_found(self, client: TestClient, mock_agent_repo: AsyncMock) -> None:
        """GET /api/agents/{spec_id} で存在しない場合は 404。"""
        mock_agent_repo.get.side_effect = NotFoundError("AgentSpec", "missing-id")
        resp = client.get("/api/agents/missing-id")
        assert resp.status_code == 404

    def test_list_agents(self, client: TestClient, mock_agent_repo: AsyncMock) -> None:
        """GET /api/agents は一覧を返す。"""
        mock_agent_repo.list.return_value = ([_make_agent_spec()], None)
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]) == 1

    def test_update_agent(self, client: TestClient, mock_agent_service: AsyncMock) -> None:
        """PATCH /api/agents/{spec_id} は更新された情報を返す。"""
        mock_agent_service.update.return_value = _make_agent_spec(name="updated")
        resp = client.patch("/api/agents/spec-1", json={"name": "updated"})
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "updated"

    def test_archive_agent(self, client: TestClient, mock_agent_service: AsyncMock) -> None:
        """POST /api/agents/{spec_id}/archive はアーカイブする。"""
        mock_agent_service.archive.return_value = _make_agent_spec(status=SpecStatus.ARCHIVED)
        resp = client.post("/api/agents/spec-1/archive")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "archived"
