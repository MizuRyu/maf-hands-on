"""共有ツール: 通知送信 (モック実装)。"""

import logging
from typing import Annotated

from agent_framework import tool

logger = logging.getLogger(__name__)


@tool
def send_notification(
    recipient: Annotated[str, "通知先 (メールアドレスまたはユーザーID)"],
    subject: Annotated[str, "通知の件名"],
    body: Annotated[str, "通知の本文"],
) -> str:
    """通知を送信する (モック実装)。

    実際の通知サービスへの連携はインフラ層で差し替える。
    """
    logger.info("通知送信: to=%s, subject=%s", recipient, subject)
    return f"通知を送信しました: to={recipient}, subject={subject}"


@tool
def send_approval_request(
    approver: Annotated[str, "承認者のユーザーID"],
    request_id: Annotated[str, "申請ID"],
    summary: Annotated[str, "申請内容の要約"],
) -> str:
    """承認リクエストを送信する (モック実装)。"""
    logger.info("承認リクエスト: approver=%s, request_id=%s", approver, request_id)
    return f"承認リクエストを送信しました: approver={approver}, request_id={request_id}, summary={summary}"
