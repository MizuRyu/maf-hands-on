"""テキストパイプライン Workflow の定義。"""

# NOTE: @handler がランタイムで型アノテーションを参照するため from __future__ import annotations は使わない

import asyncio
import logging

from agent_framework import CheckpointStorage, Workflow, WorkflowBuilder

from src.platform.workflows._types import WorkflowMeta
from src.platform.workflows.text_pipeline.contracts import UserRequest
from src.platform.workflows.text_pipeline.executors import InputValidator, OutputFormatter, Processor

logger = logging.getLogger(__name__)

WORKFLOW_META = WorkflowMeta(
    name="text-pipeline",
    description="テキスト分析パイプライン (バリデーション → 正規化 → レポート生成)",
    version=1,
    executor_ids=["input-validator", "processor", "output-formatter"],
)


def build_text_pipeline_workflow(
    *,
    checkpoint_storage: CheckpointStorage | None = None,
) -> Workflow:
    """3 段パイプラインワークフローを構築する。"""
    validator = InputValidator("input-validator")
    processor = Processor("processor")
    formatter = OutputFormatter("output-formatter")

    return (
        WorkflowBuilder(start_executor=validator, checkpoint_storage=checkpoint_storage)
        .add_edge(validator, processor)
        .add_edge(processor, formatter)
        .build()
    )


async def main() -> None:
    """動作確認用エントリーポイント。"""
    workflow = build_text_pipeline_workflow()

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
