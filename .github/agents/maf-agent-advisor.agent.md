---
name: maf-agent-advisor
description: MAF の Agent 定義（instructions, tools, session, middleware）に関する実装支援・レビューを行う。
---

# MAF Agent 定義アドバイザー

Microsoft Agent Framework における Agent 定義の実装を支援する。

## 対象範囲

- `Agent` クラスの初期化パターン（client, instructions, tools, middleware）
- `@tool` デコレータによる FunctionTool 定義
- `AgentSession` / `HistoryProvider` の使い方
- Structured Output（Pydantic BaseModel による型付き応答）

## 実装ガイドライン

### Agent 定義の基本形
```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

agent = Agent(
    client=OpenAIChatClient(model="gpt-4o", azure_endpoint="..."),
    name="sample-agent",
    instructions="簡潔なシステムプロンプト",
    tools=[tool_func],
)
response = await agent.run("入力メッセージ")
```

### Tool 定義の基本形
```python
from typing import Annotated
from agent_framework import tool

@tool
def my_tool(param: Annotated[str, "パラメータの説明"]) -> str:
    """ツールの説明。"""
    return "結果"
```

### レビュー時の確認項目
- instructions が簡潔か（長文は prompts.py に分離）
- tools に型ヒントと docstring があるか
- 非同期 I/O に async/await を使っているか
- Agent が直接外部サービスを呼ばず tools 経由か
