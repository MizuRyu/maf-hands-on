"""playground ランナー。make play m=<module> から呼ばれる。"""

from __future__ import annotations

import asyncio
import importlib
import logging
import sys

MODULES = {
    "agent": "src.playground.agents.sample_agent",
    "tools": "src.playground.tools.sample_tools",
    "middleware": "src.playground.middleware.sample_middleware",
    "workflow": "src.playground.workflows.sample_workflow",
    "hitl": "src.playground.workflows.hitl_workflow",
    "eval": "src.playground.evaluation.sample_evaluation",
    "session": "src.playground.memory_state.sample_session",
    "compaction": "src.playground.context_providers.sample_compaction",
    "streaming": "src.playground.observability.sample_streaming",
}


def _print_usage() -> None:
    print("Usage: python -m src.playground <module>")
    print()
    print("Available modules:")
    print("  agent      - 基本 Agent")
    print("  tools      - @tool / FunctionTool")
    print("  middleware  - Agent/Function ミドルウェア")
    print("  workflow    - WorkflowBuilder パイプライン")
    print("  hitl       - HITL (Human-in-the-Loop) ワークフロー")
    print("  eval       - Evaluation")
    print("  session    - AgentSession マルチターン")
    print("  compaction - Compaction 戦略")
    print("  streaming  - ResponseStream")


def run() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in MODULES:
        _print_usage()
        sys.exit(1 if len(sys.argv) >= 2 else 0)

    name = sys.argv[1]

    # .env を先にロード
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    mod = importlib.import_module(MODULES[name])
    asyncio.run(mod.main())


if __name__ == "__main__":
    run()
