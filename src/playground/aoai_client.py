"""Azure OpenAI クライアントの生成。

デフォルトは MockChatClient (LLM 呼び出しなし・課金ゼロ)。
ALLOW_LLM_CALLS=true を設定すると本物の OpenAIChatClient を返す。
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator, Awaitable, Mapping, Sequence
from typing import Any

from agent_framework import BaseChatClient
from agent_framework._types import (
    ChatResponse,
    ChatResponseUpdate,
    Content,
    Message,
    ResponseStream,
)

logger = logging.getLogger(__name__)

_client: BaseChatClient | None = None

MOCK_RESPONSE = "これはモックレスポンスです。実際の LLM は呼び出されていません。"


class MockChatClient(BaseChatClient):
    """LLM を呼び出さないフェイククライアント。固定レスポンスを返す。"""

    def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> Awaitable[ChatResponse] | ResponseStream[ChatResponseUpdate, ChatResponse]:
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.role == "user" and msg.contents:
                last_user_msg = str(msg.contents[0])
                break

        reply_text = f"[Mock] 入力を受け取りました: '{last_user_msg[:50]}' — {MOCK_RESPONSE}"

        if stream:

            async def _stream() -> AsyncIterator[ChatResponseUpdate]:
                yield ChatResponseUpdate(role="assistant", contents=[Content.from_text(reply_text)])

            return ResponseStream(_stream())

        async def _respond() -> ChatResponse:
            return ChatResponse(
                messages=Message("assistant", [Content.from_text(reply_text)]),
                model="mock-model",
                finish_reason="stop",
            )

        return _respond()


def _is_llm_calls_allowed() -> bool:
    return os.getenv("ALLOW_LLM_CALLS", "").lower() == "true"


def get_aoai_client() -> BaseChatClient:
    """クライアントをシングルトンで返す。

    - ALLOW_LLM_CALLS=true → 本物の OpenAIChatClient
    - それ以外 (デフォルト) → MockChatClient (課金ゼロ)
    """
    global _client
    if _client is not None:
        return _client

    if _is_llm_calls_allowed():
        from agent_framework.openai import OpenAIChatClient

        from src.platform.infrastructure.settings.config import config

        if config.azure_openai_api_key and config.azure_openai_endpoint:
            _client = OpenAIChatClient(
                model=config.azure_openai_model,
                azure_endpoint=config.azure_openai_endpoint,
                api_key=config.azure_openai_api_key,
            )
        else:
            from azure.identity.aio import AzureCliCredential

            _client = OpenAIChatClient(
                model=config.azure_openai_model,
                azure_endpoint=config.azure_openai_endpoint or config.azure_ai_project_endpoint,
                credential=AzureCliCredential(),
            )
        logger.info("Using real OpenAIChatClient (ALLOW_LLM_CALLS=true)")
    else:
        _client = MockChatClient()
        logger.info("Using MockChatClient (set ALLOW_LLM_CALLS=true for real LLM)")

    return _client
