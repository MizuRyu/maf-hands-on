"""環境変数 / .env から設定を読み取る。"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure AI
    azure_ai_project_endpoint: str = ""
    azure_ai_model_deployment_name: str = ""

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_model: str = ""

    # Cosmos DB
    azure_cosmos_endpoint: str = Field(default="http://localhost:8081")
    azure_cosmos_database_name: str = Field(default="maf")
    azure_cosmos_key: str = ""

    # Observability (MAF 環境変数: ENABLE_INSTRUMENTATION, ENABLE_SENSITIVE_DATA, OTEL_SERVICE_NAME)
    enable_sensitive_data: bool = False
    enable_console_exporters: bool = False


config = Config()
