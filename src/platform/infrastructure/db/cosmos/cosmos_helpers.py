"""Cosmos DB リポジトリ共通ヘルパー。

各リポジトリで重複するエラーハンドリングとページネーションロジックを集約する。
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from azure.cosmos.aio import ContainerProxy
from azure.cosmos.exceptions import CosmosHttpResponseError

from src.platform.domain.common.exceptions import (
    ConcurrencyError,
    ConflictError,
    NotFoundError,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def cosmos_error_handler(entity_type: str, entity_id: str = "") -> AsyncIterator[None]:
    """CosmosHttpResponseError をドメイン例外に変換するコンテキストマネージャ。"""
    try:
        yield
    except CosmosHttpResponseError as e:
        if e.status_code == 404:
            raise NotFoundError(entity_type, entity_id) from e
        if e.status_code == 409:
            raise ConflictError(entity_type, entity_id) from e
        if e.status_code == 412:
            raise ConcurrencyError(entity_type, entity_id) from e
        raise


async def paginate(
    container: ContainerProxy,
    query: str,
    parameters: list[dict[str, Any]] | None = None,
    *,
    partition_key: Any = None,
    max_items: int = 50,
    continuation_token: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """continuation token ベースのページネーションを行う。

    Returns:
        (items, next_continuation_token) のタプル。
        次ページがない場合は continuation_token が None。
    """
    query_kwargs: dict[str, Any] = {
        "query": query,
        "max_item_count": max_items,
    }
    if parameters:
        query_kwargs["parameters"] = parameters
    if partition_key is not None:
        query_kwargs["partition_key"] = partition_key

    items: list[dict[str, Any]] = []
    next_token: str | None = None

    query_iterable = container.query_items(**query_kwargs)

    page_iter = query_iterable.by_page(continuation_token)
    async for page in page_iter:
        async for item in page:
            items.append(item)
        next_token = getattr(page_iter, "continuation_token", None)
        break  # 1 ページ分のみ取得

    return items, next_token
