"""ドメイン全体で使用する値型の定義。"""

from __future__ import annotations

from typing import NewType

SpecId = NewType("SpecId", str)
"""エージェント・ツール・ワークフロー仕様の一意識別子。"""

ExecutionId = NewType("ExecutionId", str)
"""ワークフロー実行インスタンスの一意識別子。"""

StepId = NewType("StepId", str)
"""ワークフロー実行ステップの一意識別子。"""

SessionId = NewType("SessionId", str)
"""チャットセッションの一意識別子。"""

UserId = NewType("UserId", str)
"""プラットフォームユーザーの一意識別子。"""

CheckpointId = NewType("CheckpointId", str)
"""MAF チェックポイントの一意識別子。"""

RunId = NewType("RunId", str)
"""Agent 実行の一意識別子。"""
