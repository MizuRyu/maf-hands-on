"""共有ツールのユニットテスト。"""

from __future__ import annotations

from src.platform.tools.datetime_tools import calculate_deadline, get_current_datetime, is_past_deadline
from src.platform.tools.notification_tools import send_approval_request, send_notification


class TestDatetimeTools:
    def test_get_current_datetime(self) -> None:
        """現在時刻が ISO 8601 形式で返る。"""
        result = get_current_datetime.func()  # type: ignore[reportOptionalCall]
        assert "T" in result

    def test_calculate_deadline(self) -> None:
        """期限計算が正しい。"""
        result = calculate_deadline.func(7)  # type: ignore[reportOptionalCall]
        assert "7 日後" in result

    def test_is_past_deadline_future(self) -> None:
        """未来の期限は期限内。"""
        result = is_past_deadline.func("2099-12-31")  # type: ignore[reportOptionalCall]
        assert "期限内" in result

    def test_is_past_deadline_past(self) -> None:
        """過去の期限は期限超過。"""
        result = is_past_deadline.func("2020-01-01")  # type: ignore[reportOptionalCall]
        assert "期限超過" in result


class TestNotificationTools:
    def test_send_notification(self) -> None:
        """通知が送信される。"""
        result = send_notification.func("user@example.com", "テスト", "本文")  # type: ignore[reportOptionalCall]
        assert "送信しました" in result

    def test_send_approval_request(self) -> None:
        """承認リクエストが送信される。"""
        result = send_approval_request.func("approver-1", "req-001", "テスト申請")  # type: ignore[reportOptionalCall]
        assert "送信しました" in result
