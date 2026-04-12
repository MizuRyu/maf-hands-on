"""テキスト分析 Agent の定義。"""

from __future__ import annotations

from src.platform.agents.text_analyzer.tools import count_words, summarize_text
from src.platform.core.types import AgentMeta

AGENT_META = AgentMeta(
    name="text-analyzer-agent",
    description="テキスト分析(単語数カウント・要約)を行う Agent",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["count_words", "summarize_text"],
)

TOOLS = [count_words, summarize_text]
