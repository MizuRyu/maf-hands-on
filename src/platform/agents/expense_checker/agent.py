"""経費チェッカー Agent の定義。"""

from __future__ import annotations

from src.platform.agents.expense_checker.tools import calculate_total, check_expense_policy
from src.platform.core.types import AgentMeta
from src.platform.tools.datetime_tools import get_current_datetime

AGENT_META = AgentMeta(
    name="expense-checker-agent",
    description="経費ポリシーチェック・金額計算を行う Agent",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["check_expense_policy", "calculate_total", "get_current_datetime"],
)

TOOLS = [check_expense_policy, calculate_total, get_current_datetime]
