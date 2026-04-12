"""セッションの Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import SessionStatus
from src.platform.domain.common.types import SessionId, SpecId, UserId
from src.platform.domain.sessions.models.session import Session
from src.platform.domain.sessions.repositories.session_repository import (
    SessionRepository,
)
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "sessions"
ENTITY_TYPE = "Session"


class CosmosSessionRepository(SessionRepository):
    """sessions コンテナに対する CRUD 実装。PK: /sessionId。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, session_id: SessionId) -> Session:
        async with cosmos_error_handler(ENTITY_TYPE, session_id):
            doc = await self._container.read_item(item=session_id, partition_key=session_id)
        return _from_document(doc)

    async def list_by_user(
        self,
        user_id: UserId,
        *,
        max_items: int = 50,
        continuation_token: str | None = None,
    ) -> tuple[list[Session], str | None]:
        docs, next_token = await paginate(
            self._container,
            "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.createdAt DESC",
            [{"name": "@userId", "value": user_id}],
            max_items=max_items,
            continuation_token=continuation_token,
        )
        return [_from_document(d) for d in docs], next_token

    async def create(self, entity: Session) -> Session:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.session_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: Session, *, etag: str | None = None) -> Session:
        doc = _to_document(entity)
        kwargs: dict[str, Any] = {
            "item": entity.session_id,
            "body": doc,
        }
        if etag is not None:
            kwargs["if_match"] = etag
        async with cosmos_error_handler(ENTITY_TYPE, entity.session_id):
            replaced = await self._container.replace_item(**kwargs)
        return _from_document(replaced)

    async def delete(self, session_id: SessionId) -> None:
        async with cosmos_error_handler(ENTITY_TYPE, session_id):
            await self._container.delete_item(item=session_id, partition_key=session_id)


def _to_document(entity: Session) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": entity.session_id,
        "sessionId": entity.session_id,
        "userId": entity.user_id,
        "agentId": entity.agent_id,
        "status": entity.status.value,
        "schemaVersion": entity.schema_version,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }
    if entity.title is not None:
        doc["title"] = entity.title
    if entity.ttl is not None:
        doc["ttl"] = entity.ttl
    return doc


def _from_document(doc: dict[str, Any]) -> Session:
    return Session(
        session_id=SessionId(doc["sessionId"]),
        user_id=UserId(doc["userId"]),
        agent_id=SpecId(doc["agentId"]),
        status=SessionStatus(doc["status"]),
        schema_version=doc["schemaVersion"],
        created_at=datetime.fromisoformat(doc["createdAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        title=doc.get("title"),
        ttl=doc.get("ttl"),
    )
