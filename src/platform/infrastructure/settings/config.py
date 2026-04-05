"""環境変数から設定を読み取る。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # Azure AI
    azure_ai_project_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""))
    azure_ai_model_deployment_name: str = field(default_factory=lambda: os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", ""))

    # Azure OpenAI
    azure_openai_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT", ""))
    azure_openai_api_key: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY", ""))
    azure_openai_model: str = field(default_factory=lambda: os.getenv("AZURE_OPENAI_MODEL", ""))

    # Cosmos DB
    cosmos_endpoint: str = field(default_factory=lambda: os.getenv("COSMOS_ENDPOINT", "http://localhost:8081"))
    cosmos_database_name: str = field(default_factory=lambda: os.getenv("COSMOS_DATABASE_NAME", "maf"))

    # Observability
    enable_instrumentation: bool = field(
        default_factory=lambda: os.getenv("ENABLE_INSTRUMENTATION", "true").lower() == "true"
    )
    enable_sensitive_data: bool = field(
        default_factory=lambda: os.getenv("ENABLE_SENSITIVE_DATA", "false").lower() == "true"
    )
    enable_console_exporters: bool = field(
        default_factory=lambda: os.getenv("ENABLE_CONSOLE_EXPORTERS", "false").lower() == "true"
    )
    otel_service_name: str = field(default_factory=lambda: os.getenv("OTEL_SERVICE_NAME", "maf-backend"))


config = Config()
