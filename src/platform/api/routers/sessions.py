"""Session ルーター。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends

from src.platform.api.deps.services import get_agent_factory, get_agent_spec_repo, get_session_repo
from src.platform.domain.registry.repositories.agent_spec_repository import AgentSpecRepository

if TYPE_CHECKING:
    from src.platform.core.agent_factory import PlatformAgentFactory
from src.platform.api.schemas.common import API_PREFIX, BaseResponse, DefaultResponse
from src.platform.api.schemas.session import (
    MessageResponseData,
    SendMessageRequest,
    SessionCreateRequest,
    SessionResponseData,
    SessionUpdateRequest,
)
from src.platform.domain.common.enums import SessionStatus
from src.platform.domain.common.types import SessionId, SpecId, UserId
from src.platform.domain.sessions.models.session import Session
from src.platform.domain.sessions.repositories.session_repository import (
    SessionRepository,
)

router = APIRouter(prefix=API_PREFIX, tags=["sessions"])


class SessionResponse(BaseResponse[SessionResponseData]):
    pass


class SessionListResponse(BaseResponse[list[SessionResponseData]]):
    pass


class MessageResponse(BaseResponse[MessageResponseData]):
    pass


def _to_data(session: Session) -> SessionResponseData:
    return SessionResponseData(
        session_id=session.session_id,
        user_id=session.user_id,
        agent_id=session.agent_id,
        status=session.status.value,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


# --- Session Query ---


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> SessionResponse:
    session = await repo.get(SessionId(session_id))
    return SessionResponse(data=_to_data(session))


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
    user_id: str = "system",
    max_items: int = 50,
) -> SessionListResponse:
    sessions, _ = await repo.list_by_user(UserId(user_id), max_items=max_items)
    return SessionListResponse(data=[_to_data(s) for s in sessions])


# --- Session Command ---


@router.post("/sessions", status_code=201, response_model=SessionResponse)
async def create_session(
    body: SessionCreateRequest,
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> SessionResponse:
    now = datetime.now(UTC)
    session = Session(
        session_id=SessionId(str(uuid.uuid4())),
        user_id=UserId("system"),
        agent_id=SpecId(body.agent_id),
        status=SessionStatus.ACTIVE,
        schema_version=1,
        created_at=now,
        updated_at=now,
        title=body.title,
    )
    created = await repo.create(session)
    return SessionResponse(code=201, data=_to_data(created))


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    body: SessionUpdateRequest,
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> SessionResponse:
    import dataclasses

    existing = await repo.get(SessionId(session_id))
    updates: dict = {}
    if body.title is not None:
        updates["title"] = body.title
    updates["updated_at"] = datetime.now(UTC)
    updated = dataclasses.replace(existing, **updates)
    saved = await repo.update(updated)
    return SessionResponse(data=_to_data(saved))


@router.delete("/sessions/{session_id}", response_model=DefaultResponse)
async def close_session(
    session_id: str,
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> DefaultResponse:
    existing = await repo.get(SessionId(session_id))
    closed = existing.with_status(SessionStatus.CLOSED, datetime.now(UTC))
    await repo.update(closed)
    return DefaultResponse()


# --- Messages ---


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
    agent_spec_repo: Annotated[AgentSpecRepository, Depends(get_agent_spec_repo)],
    factory: Annotated[PlatformAgentFactory, Depends(get_agent_factory)],
) -> MessageResponse:
    from agent_framework import AgentSession, Message

    session = await repo.get(SessionId(session_id))
    spec = await agent_spec_repo.get(session.agent_id)

    agent_session = AgentSession(session_id=session_id)
    meta = _spec_to_meta(spec)
    agent = factory.create(meta, spec.instructions, [])

    response = await agent.run(
        messages=Message("user", [body.input]),
        session=agent_session,
    )

    output = response.messages[-1].text if response.messages else ""
    trace_id = None

    return MessageResponse(data=MessageResponseData(output=output, trace_id=trace_id))


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> BaseResponse[list]:
    await repo.get(SessionId(session_id))
    return BaseResponse(data=[])


def _spec_to_meta(spec):
    from src.platform.core.types import AgentMeta

    return AgentMeta(
        name=spec.name,
        description=spec.description or "",
        version=spec.version,
        model_id=spec.model_id,
    )
