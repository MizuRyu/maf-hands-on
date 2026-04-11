"""ユーザーの Cosmos DB リポジトリ実装。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from azure.cosmos.aio import ContainerProxy

from src.platform.domain.common.enums import UserRole, UserStatus
from src.platform.domain.common.types import UserId
from src.platform.domain.users.models.user import User
from src.platform.domain.users.repositories.user_repository import UserRepository
from src.platform.infrastructure.db.cosmos.cosmos_helpers import (
    cosmos_error_handler,
    paginate,
)

CONTAINER_NAME = "users"
ENTITY_TYPE = "User"


class CosmosUserRepository(UserRepository):
    """users コンテナに対する CRUD 実装。"""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def get(self, user_id: UserId) -> User:
        async with cosmos_error_handler(ENTITY_TYPE, user_id):
            doc = await self._container.read_item(item=user_id, partition_key=user_id)
        return _from_document(doc)

    async def get_by_email(self, email: str) -> User:
        docs, _ = await paginate(
            self._container,
            "SELECT * FROM c WHERE c.email = @email",
            [{"name": "@email", "value": email}],
            max_items=1,
        )
        if not docs:
            from src.platform.domain.common.exceptions import NotFoundError

            raise NotFoundError(ENTITY_TYPE, email)
        return _from_document(docs[0])

    async def create(self, entity: User) -> User:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.user_id):
            created = await self._container.create_item(body=doc)
        return _from_document(created)

    async def update(self, entity: User) -> User:
        doc = _to_document(entity)
        async with cosmos_error_handler(ENTITY_TYPE, entity.user_id):
            replaced = await self._container.replace_item(item=entity.user_id, body=doc)
        return _from_document(replaced)

    async def delete(self, user_id: UserId) -> None:
        async with cosmos_error_handler(ENTITY_TYPE, user_id):
            await self._container.delete_item(item=user_id, partition_key=user_id)


def _to_document(entity: User) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": entity.user_id,
        "displayName": entity.display_name,
        "role": entity.role.value,
        "status": entity.status.value,
        "schemaVersion": entity.schema_version,
        "createdAt": entity.created_at.isoformat(),
        "updatedAt": entity.updated_at.isoformat(),
    }
    if entity.email is not None:
        doc["email"] = entity.email
    if entity.preferences is not None:
        doc["preferences"] = entity.preferences
    if entity.last_login_at is not None:
        doc["lastLoginAt"] = entity.last_login_at.isoformat()
    return doc


def _from_document(doc: dict[str, Any]) -> User:
    last_login = doc.get("lastLoginAt")
    return User(
        user_id=UserId(doc["id"]),
        display_name=doc["displayName"],
        role=UserRole(doc["role"]),
        status=UserStatus(doc["status"]),
        schema_version=doc["schemaVersion"],
        created_at=datetime.fromisoformat(doc["createdAt"]),
        updated_at=datetime.fromisoformat(doc["updatedAt"]),
        email=doc.get("email"),
        preferences=doc.get("preferences"),
        last_login_at=(datetime.fromisoformat(last_login) if last_login else None),
    )
