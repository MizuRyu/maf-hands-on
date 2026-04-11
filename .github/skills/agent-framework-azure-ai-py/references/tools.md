# ホステッドツール リファレンス

Agent Framework v1.0.0 で利用可能な全ホステッドツールの詳細パターン。

> **v1.0.0 変更点**: `Hosted*Tool` クラスは廃止。`client.get_*_tool()` メソッドに置換。

---

## Code Interpreter

エージェントが Azure AI サービス上で Python コードを実行できるようにする。

### 基本的な使い方

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="CodingAgent",
    instructions="Python コードを書いて実行し、問題を解決します。",
    tools=[client.get_code_interpreter_tool()],
)

result = await agent.run("Python で 20 の階乗を計算して")
print(result.text)
```

### 主なユースケース

- データ分析・可視化
- 数学的計算
- ファイル処理（CSV, JSON 等）
- コード生成・テスト

---

## File Search

ベクトルストアを使ってドキュメントを検索する。

### ベクトルストアを使ったセットアップ

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="ResearchAgent",
    instructions="ナレッジベースを検索して正確に回答します。",
    tools=[client.get_file_search_tool(vector_store_ids=["vs-my-store"])],
)

result = await agent.run("ドキュメント内の主な発見は？")
print(result.text)
```

### 主なユースケース

- ドキュメント Q&A
- ナレッジベース検索
- ポリシー・手順書の参照
- 技術ドキュメント検索

---

## Web Search

Bing を使って Web を検索する。

### 基本的な Bing グラウンディング

```python
import os
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

# BING_CONNECTION_ID 環境変数が必要
os.environ["BING_CONNECTION_ID"] = "your-bing-connection-id"

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="SearchAgent",
    instructions="Web を検索して最新の情報で回答します。",
    tools=[client.get_web_search_tool()],
)

result = await agent.run("AI の最新動向は？")
print(result.text)
```

### 主なユースケース

- 最新ニュース・イベント
- リアルタイム情報検索
- ファクトチェック
- リサーチ支援

---

## 複数ツールの組み合わせ

エージェントは複数のツールを同時に使用できる:

```python
from typing import Annotated
from pydantic import Field
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

@tool
def get_current_date() -> str:
    """今日の日付を取得する。"""
    from datetime import date
    return date.today().isoformat()

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

agent = Agent(
    client=client,
    name="SuperAgent",
    instructions="""複数の機能を持つアシスタント:
    - Python コードの実行（計算・データ分析）
    - Web の検索（最新の外部情報）
    - 現在日付の提供

    ユーザーの質問に応じて適切なツールを選択してください。""",
    tools=[
        get_current_date,
        client.get_code_interpreter_tool(),
        client.get_web_search_tool(),
    ],
)
```

---

## ツール選択ガイド

| 用途 | ツール |
|------|-------|
| コード実行、数学、データ分析 | `client.get_code_interpreter_tool()` |
| アップロード済みドキュメント検索 | `client.get_file_search_tool(...)` |
| 最新の Web 情報 | `client.get_web_search_tool()` |
| カスタムビジネスロジック | `@tool` 関数 |
| 外部 API 統合 | `client.get_mcp_tool(...)` or `MCPStreamableHTTPTool` |

---

## エラーハンドリング

```python
async for chunk in agent.run("このデータを分析して", stream=True):
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

> **v1.0.0 変更点**: ストリーミングのエラーは `AgentFrameworkException` 系の例外として送出される。
