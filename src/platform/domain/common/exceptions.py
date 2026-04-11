"""ドメイン例外の定義。

インフラ層で発生する技術的例外（Cosmos SDK のエラー等）を
ドメイン固有の例外に変換するために使用する。
"""

from __future__ import annotations


class DomainError(Exception):
    """ドメイン例外の基底クラス。"""


class NotFoundError(DomainError):
    """指定されたエンティティが存在しない場合に送出する。"""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id}")


class ConflictError(DomainError):
    """エンティティの作成時に ID が重複した場合に送出する。"""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} already exists: {entity_id}")


class ConcurrencyError(DomainError):
    """楽観的排他制御で ETag 不一致が検出された場合に送出する。"""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} was modified by another process: {entity_id}")


class ValidationError(DomainError):
    """ドメインバリデーションに違反した場合に送出する。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
