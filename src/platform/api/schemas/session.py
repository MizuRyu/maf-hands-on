"""Session API のリクエスト/レスポンススキーマ。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    agent_id: str
    title: str | None = None


class SessionUpdateRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    input: str = Field(..., min_length=1)


class SessionResponseData(BaseModel):
    session_id: str
    user_id: str
    agent_id: str
    status: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class MessageResponseData(BaseModel):
    output: str
    trace_id: str | None = None
