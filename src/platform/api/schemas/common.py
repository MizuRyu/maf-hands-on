"""API 共通のスキーマ定義。"""

from __future__ import annotations

from pydantic import BaseModel

API_PREFIX = "/api"


class BaseResponse[T](BaseModel):
    """統一レスポンスラッパー。"""

    code: int = 200
    data: T


class DefaultResponse(BaseModel):
    """データなしの成功レスポンス。"""

    code: int = 200


class ErrorResponse(BaseModel):
    """統一エラーレスポンス。"""

    code: int
    detail: str
    error_type: str
