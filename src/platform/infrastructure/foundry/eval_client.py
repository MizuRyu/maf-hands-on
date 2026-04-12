"""Foundry Evals クライアント。

ローカル環境ではモック実装を提供する。
Azure Foundry Evals が利用可能な場合は、実際の API 呼び出しに差し替える。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class EvalRunStatus(StrEnum):
    """Eval 実行のステータス。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class FoundryEvalRun:
    """Foundry Eval 実行結果。"""

    run_id: str
    status: EvalRunStatus
    submitted_at: datetime
    completed_at: datetime | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


class FoundryEvalClient:
    """Foundry Evals Service クライアント (モック実装)。"""

    def __init__(self, *, dry_run: bool = True) -> None:
        self._dry_run = dry_run
        self._runs: dict[str, FoundryEvalRun] = {}

    async def submit_eval_run(
        self,
        dataset_path: str,
        evaluator_names: list[str],
        agent_name: str | None = None,
    ) -> str:
        """Eval 実行を送信する。"""
        import uuid

        run_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        logger.info(
            "Foundry eval submit: run_id=%s, dataset=%s, evaluators=%s, dry_run=%s",
            run_id,
            dataset_path,
            evaluator_names,
            self._dry_run,
        )

        if self._dry_run:
            run = FoundryEvalRun(
                run_id=run_id,
                status=EvalRunStatus.COMPLETED,
                submitted_at=now,
                completed_at=now,
                metrics={
                    "relevance": 0.85,
                    "coherence": 0.90,
                    "groundedness": 0.80,
                },
                details={
                    "mode": "dry_run",
                    "agent_name": agent_name,
                    "dataset": dataset_path,
                },
            )
        else:
            run = FoundryEvalRun(
                run_id=run_id,
                status=EvalRunStatus.PENDING,
                submitted_at=now,
                details={"agent_name": agent_name},
            )
        self._runs[run_id] = run
        return run_id

    async def get_eval_results(self, run_id: str) -> FoundryEvalRun:
        """Eval 実行結果を取得する。"""
        if run_id in self._runs:
            return self._runs[run_id]
        return FoundryEvalRun(
            run_id=run_id,
            status=EvalRunStatus.FAILED,
            submitted_at=datetime.now(UTC),
            details={"error": "Run not found"},
        )
