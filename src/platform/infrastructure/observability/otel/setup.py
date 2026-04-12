"""ロギングと OpenTelemetry の初期化。"""

from __future__ import annotations

import logging
import sys

from src.platform.infrastructure.settings.config import config

_OTEL_INITIALIZED = False


def setup_logging(level: int = logging.INFO) -> None:
    """標準ロギングを設定する。"""
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    # ライブラリログの抑制
    logging.getLogger("agent_framework").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def setup_opentelemetry() -> None:
    """OpenTelemetry プロバイダーを初期化する。冪等。"""
    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED:
        return

    from agent_framework.observability import configure_otel_providers

    configure_otel_providers(
        enable_sensitive_data=config.enable_sensitive_data,
        enable_console_exporters=config.enable_console_exporters,
    )
    _OTEL_INITIALIZED = True
