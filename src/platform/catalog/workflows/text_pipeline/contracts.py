"""テキストパイプライン Executor 間メッセージ型。"""

from dataclasses import dataclass, field


@dataclass
class UserRequest:
    """ワークフローへの入力メッセージ。"""

    text: str
    max_length: int = 500


@dataclass
class ValidatedInput:
    """バリデーション済みの入力。"""

    text: str
    char_count: int
    word_count: int


@dataclass
class ProcessedData:
    """加工済みデータ。"""

    original_text: str
    normalized_text: str
    word_count: int
    keywords: list[str] = field(default_factory=list)


@dataclass
class FormattedOutput:
    """最終出力。"""

    report: str
