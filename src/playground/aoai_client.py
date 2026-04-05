"""Azure OpenAI クライアントの生成。"""

from __future__ import annotations

from agent_framework.openai import OpenAIChatClient

from src.platform.infrastructure.settings.config import config

_client: OpenAIChatClient | None = None


def get_aoai_client() -> OpenAIChatClient:
    """シングルトンで Azure OpenAI クライアントを返す。"""
    global _client
    if _client is not None:
        return _client

    if config.azure_openai_api_key and config.azure_openai_endpoint:
        # API キー認証
        _client = OpenAIChatClient(
            model=config.azure_openai_model,
            azure_endpoint=config.azure_openai_endpoint,
            api_key=config.azure_openai_api_key,
        )
    else:
        # Azure CLI 認証
        from azure.identity.aio import AzureCliCredential

        _client = OpenAIChatClient(
            model=config.azure_openai_model,
            azure_endpoint=config.azure_openai_endpoint or config.azure_ai_project_endpoint,
            credential=AzureCliCredential(),
        )
    return _client
