"""AuditMiddleware のテスト。"""

import pytest

from src.platform.core.middleware.audit import AuditMiddleware


class TestAuditMiddleware:
    @pytest.fixture
    def middleware(self) -> AuditMiddleware:
        return AuditMiddleware()

    def test_instantiation(self, middleware: AuditMiddleware) -> None:
        assert middleware is not None

    async def test_calls_next(self, middleware: AuditMiddleware) -> None:
        called = False

        class FakeContext:
            messages: list = []  # noqa: RUF012
            result = None
            agent_name = "test-agent"

        async def call_next() -> None:
            nonlocal called
            called = True

        await middleware.process(FakeContext(), call_next)  # type: ignore[arg-type]
        assert called is True
