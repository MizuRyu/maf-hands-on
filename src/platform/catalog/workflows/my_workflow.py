"""カタログ用ワークフロー。3 段パイプラインでメッセージ変換を行う。

InputValidator → Processor → OutputFormatter の順に実行し、
各 Executor 間はデータクラスメッセージで連携する。
"""

# NOTE: `from __future__ import annotations` は使わない。
# @handler がランタイムで型アノテーションを参照するため、文字列化すると動作しない。

import asyncio
import logging
from dataclasses import dataclass, field

from agent_framework import Executor, Workflow, WorkflowBuilder, WorkflowContext, handler
from agent_framework._workflows._checkpoint import CheckpointStorage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# メッセージ型定義
# ---------------------------------------------------------------------------


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
    """加工済みデータ。Processor が付与したメタ情報を保持する。"""

    original_text: str
    normalized_text: str
    word_count: int
    keywords: list[str] = field(default_factory=list)


@dataclass
class FormattedOutput:
    """最終出力。ユーザーに返却するレポート形式。"""

    report: str


# ---------------------------------------------------------------------------
# Executor 定義
# ---------------------------------------------------------------------------


class InputValidator(Executor):
    """入力テキストのバリデーションと基本情報の付与を行う。

    空文字・長さ超過を検出し、正常な入力のみ後段に渡す。
    """

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: UserRequest,
        ctx: WorkflowContext[ValidatedInput, FormattedOutput],
    ) -> None:
        text = message.text.strip()

        if not text:
            logger.warning("[InputValidator] 空の入力を検出 — スキップ")
            await ctx.yield_output(FormattedOutput(report="エラー: 入力が空です。"))
            return

        if len(text) > message.max_length:
            logger.warning(
                "[InputValidator] 入力が上限 %d 文字を超過 (%d 文字)",
                message.max_length,
                len(text),
            )
            text = text[: message.max_length]

        words = text.split()
        validated = ValidatedInput(
            text=text,
            char_count=len(text),
            word_count=len(words),
        )
        logger.info(
            "[InputValidator] OK — %d 文字, %d 語",
            validated.char_count,
            validated.word_count,
        )
        await ctx.send_message(validated)


class Processor(Executor):
    """テキストの正規化とキーワード抽出を行う。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ValidatedInput,
        ctx: WorkflowContext[ProcessedData, FormattedOutput],
    ) -> None:
        # 正規化: 連続空白の除去
        normalized = " ".join(message.text.split())

        # キーワード抽出: 4 文字以上の単語を抽出 (簡易実装)
        keywords = sorted({w for w in normalized.split() if len(w) >= 4})

        processed = ProcessedData(
            original_text=message.text,
            normalized_text=normalized,
            word_count=message.word_count,
            keywords=keywords[:10],
        )
        logger.info(
            "[Processor] キーワード %d 件抽出",
            len(processed.keywords),
        )
        await ctx.send_message(processed)


class OutputFormatter(Executor):
    """加工済みデータからレポートを生成し最終出力する。"""

    @handler  # type: ignore[reportArgumentType]
    async def handle(
        self,
        message: ProcessedData,
        ctx: WorkflowContext[None, FormattedOutput],
    ) -> None:
        lines = [
            "=== 処理結果レポート ===",
            f"語数      : {message.word_count}",
            f"キーワード: {', '.join(message.keywords) if message.keywords else '(なし)'}",
            f"テキスト  : {message.normalized_text}",
            "========================",
        ]
        report = "\n".join(lines)
        logger.info("[OutputFormatter] レポート生成完了")
        await ctx.yield_output(FormattedOutput(report=report))


# ---------------------------------------------------------------------------
# ワークフロー構築
# ---------------------------------------------------------------------------


def build_my_workflow(
    checkpoint_storage: CheckpointStorage | None = None,
) -> Workflow:
    """3 段パイプラインワークフローを構築する。

    Args:
        checkpoint_storage: チェックポイント永続化先。None の場合チェックポイント無効。

    Returns:
        InputValidator → Processor → OutputFormatter の順に
        メッセージを受け渡すワークフロー。
    """
    validator = InputValidator("input-validator")
    processor = Processor("processor")
    formatter = OutputFormatter("output-formatter")

    return (
        WorkflowBuilder(start_executor=validator, checkpoint_storage=checkpoint_storage)
        .add_edge(validator, processor)
        .add_edge(processor, formatter)
        .build()
    )


# ---------------------------------------------------------------------------
# スタンドアロン実行
# ---------------------------------------------------------------------------


async def main() -> None:
    """ワークフローの動作確認用エントリーポイント。"""
    workflow = build_my_workflow()

    inputs = [
        "Microsoft Agent Framework は Semantic Kernel と AutoGen の統合フレームワークです。",
        "ワークフローは  複数の   Executor を接続して  パイプライン処理を実現します。",
        "",
    ]

    for text in inputs:
        label = text[:40] if text else "(空文字)"
        logger.info("--- Input: %s", label)
        result = await workflow.run(UserRequest(text=text))
        for output in result.get_outputs():
            logger.info("Output:\n%s\n", output.report)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
