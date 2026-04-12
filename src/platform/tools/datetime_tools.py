"""共有ツール: 日付・期限計算。"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from agent_framework import tool


@tool
def get_current_datetime() -> str:
    """現在の日時を ISO 8601 形式で返す。"""
    return datetime.now(UTC).isoformat()


@tool
def calculate_deadline(
    days_from_now: Annotated[int, "現在からの日数"],
) -> str:
    """指定日数後の日付を計算して返す。"""
    deadline = datetime.now(UTC) + timedelta(days=days_from_now)
    return f"期限: {deadline.strftime('%Y-%m-%d')} ({days_from_now} 日後)"


@tool
def is_past_deadline(
    deadline_str: Annotated[str, "期限日 (YYYY-MM-DD 形式)"],
) -> str:
    """指定された期限日を過ぎているかを判定する。"""
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d").replace(tzinfo=UTC)
    now = datetime.now(UTC)
    if now > deadline:
        days_overdue = (now - deadline).days
        return f"期限超過: {days_overdue} 日超過しています"
    days_remaining = (deadline - now).days
    return f"期限内: 残り {days_remaining} 日です"
