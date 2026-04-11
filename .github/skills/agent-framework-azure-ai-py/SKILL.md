---
name: agent-framework-azure-ai-py
description: |
  Microsoft Agent Framework Python SDK (v1.0.0) を使って Azure AI Foundry 上にエージェントを構築する。
  FoundryChatClient によるエージェント作成、@tool デコレータ、ホステッドツール（Code Interpreter / File Search / Web Search）、
  MCP サーバー統合、セッション管理、ストリーミング応答、構造化出力をカバー。
  「MAFでエージェント作って」「Foundryエージェント」「agent-framework」と依頼されたときに使う。
license: MIT
metadata:
  author: Microsoft
  version: "1.0.0"
  package: agent-framework
---

# Agent Framework v1.0.0 — Azure AI Foundry エージェント構築ガイド

Microsoft Agent Framework Python SDK を使って Azure AI Foundry 上に永続エージェントを構築する。

## アーキテクチャ

```
ユーザークエリ → FoundryChatClient → Azure AI Foundry (永続エージェント)
                       ↓
                 Agent.run() / Agent.run(stream=True)
                       ↓
                 ツール: @tool 関数 | ホステッド (Code/Search/Web) | MCP
                       ↓
                 セッション (会話の永続化)
```

## インストール

```bash
# フルフレームワーク（推奨）
pip install agent-framework

# Foundry 固有パッケージのみ
pip install agent-framework-foundry

# OpenAI 用
pip install agent-framework-openai
```

> **注意**: v1.0.0 は GA リリース。`--pre` フラグは不要。

## パッケージ構成 (v1.0.0)

| パッケージ | 用途 |
|-----------|------|
| `agent-framework` | メタパッケージ（全部入り） |
| `agent-framework-core` | コア: `Agent`, `Message`, `tool`, MCP ツール |
| `agent-framework-foundry` | `FoundryChatClient`（Azure AI Foundry 推奨） |
| `agent-framework-openai` | `OpenAIChatClient`（OpenAI / Azure OpenAI） |
| `agent-framework-azure-ai` | `AzureAIAgentsProvider`（Persistent Agents V1、非推奨方向） |

## 環境変数

```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<project>.services.ai.azure.com"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
export BING_CONNECTION_ID="your-bing-connection-id"  # Web Search 用
```

## 認証

```python
from azure.identity import AzureCliCredential, DefaultAzureCredential

# 開発環境
credential = AzureCliCredential()

# 本番環境
credential = DefaultAzureCredential()
```

> **v1.0.0 変更点**: 同期版 `azure.identity` を使用（`azure.identity.aio` ではない）。

## コアワークフロー

### 基本エージェント（FoundryChatClient 推奨）

```python
import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )
    agent = Agent(client=client, name="MyAgent", instructions="あなたは親切なアシスタントです。")

    result = await agent.run("こんにちは！")
    print(result.text)

asyncio.run(main())
```

### 関数ツール付きエージェント

```python
from typing import Annotated
from pydantic import Field
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

@tool
def get_weather(
    location: Annotated[str, Field(description="天気を取得する都市名")],
) -> str:
    """指定した場所の現在の天気を取得する。"""
    return f"{location} の天気: 22°C、晴れ"

@tool
def get_current_time() -> str:
    """現在の UTC 時刻を取得する。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )
    agent = Agent(
        client=client,
        name="WeatherAgent",
        instructions="天気と時刻に関する質問に答えます。",
        tools=[get_weather, get_current_time],  # 関数を直接渡す
    )

    result = await agent.run("東京の天気は？")
    print(result.text)
```

### ホステッドツール付きエージェント

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )

    agent = Agent(
        client=client,
        name="MultiToolAgent",
        instructions="コード実行、ファイル検索、Web 検索が可能です。",
        tools=[
            client.get_code_interpreter_tool(),
            client.get_web_search_tool(),
        ],
    )

    result = await agent.run("Python で 20 の階乗を計算して")
    print(result.text)
```

### ストリーミング応答

```python
async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )
    agent = Agent(client=client, name="StreamingAgent", instructions="あなたは親切なアシスタントです。")

    print("Agent: ", end="", flush=True)
    async for chunk in agent.run("短い物語を教えて", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()
```

> **v1.0.0 変更点**: `run_stream()` は廃止。`run(stream=True)` に統合。

### セッション管理（マルチターン会話）

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )
    agent = Agent(
        client=client,
        name="ChatAgent",
        instructions="あなたは親切なアシスタントです。",
        tools=[get_weather],
    )

    # セッション作成（会話の永続化）
    session = agent.create_session()

    # 1ターン目
    result1 = await agent.run("東京の天気は？", session=session)
    print(f"Agent: {result1.text}")

    # 2ターン目 — コンテキスト維持
    result2 = await agent.run("大阪はどう？", session=session)
    print(f"Agent: {result2.text}")
```

> **v1.0.0 変更点**: `AgentThread` / `get_new_thread()` → `create_session()` / `session=` パラメータ。

### 構造化出力

```python
from pydantic import BaseModel, ConfigDict
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

class WeatherResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str
    temperature: float
    unit: str
    conditions: str

async def main():
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    )
    agent = Agent(
        client=client,
        name="StructuredAgent",
        instructions="天気情報を構造化フォーマットで提供します。",
    )

    result = await agent.run(
        "東京の天気は？",
        options={"response_format": WeatherResponse},
    )
    weather = WeatherResponse.model_validate_json(result.text)
    print(f"{weather.location}: {weather.temperature}°{weather.unit}")
```

> **v1.0.0 変更点**: `response_format=Model` 直接渡し → `options={"response_format": Model}`。

## クライアントメソッド

| メソッド | 説明 |
|---------|------|
| `FoundryChatClient(...)` | Foundry クライアント作成 |
| `client.as_agent(...)` | クライアントから直接エージェント作成 |
| `client.get_code_interpreter_tool()` | Code Interpreter ツール取得 |
| `client.get_web_search_tool()` | Web Search ツール取得 |
| `client.get_file_search_tool(...)` | File Search ツール取得 |
| `client.get_mcp_tool(...)` | サービス管理 MCP ツール取得 |

## ホステッドツール早見表

| ツール | 取得方法 | 用途 |
|-------|---------|------|
| Code Interpreter | `client.get_code_interpreter_tool()` | Python コード実行 |
| File Search | `client.get_file_search_tool(...)` | ベクトルストア検索 |
| Web Search | `client.get_web_search_tool()` | Bing Web 検索 |
| MCP (サービス管理) | `client.get_mcp_tool(...)` | サービス管理 MCP |
| MCP (クライアント管理) | `MCPStreamableHTTPTool(...)` | クライアント管理 MCP |

## 完全な例

```python
import asyncio
from typing import Annotated
from pydantic import BaseModel, Field
from agent_framework import Agent, tool, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


@tool
def get_weather(
    location: Annotated[str, Field(description="都市名")],
) -> str:
    """指定した場所の天気を取得する。"""
    return f"{location} の天気: 22°C、晴れ"


class AnalysisResult(BaseModel):
    summary: str
    key_findings: list[str]
    confidence: float


async def main():
    credential = AzureCliCredential()
    client = FoundryChatClient(
        project_endpoint="https://<project>.services.ai.azure.com",
        model="gpt-4o-mini",
        credential=credential,
    )

    async with MCPStreamableHTTPTool(
        name="Docs MCP",
        url="https://learn.microsoft.com/api/mcp",
    ) as mcp_tool:
        agent = Agent(
            client=client,
            name="ResearchAssistant",
            instructions="複数の機能を持つリサーチアシスタントです。",
            tools=[
                get_weather,
                client.get_code_interpreter_tool(),
                client.get_web_search_tool(),
                mcp_tool,
            ],
        )

        session = agent.create_session()

        # 非ストリーミング
        result = await agent.run(
            "Python のベストプラクティスを検索してまとめて",
            session=session,
        )
        print(f"応答: {result.text}")

        # ストリーミング
        print("\nストリーミング: ", end="")
        async for chunk in agent.run("例を続けて", session=session, stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()

        # 構造化出力
        result = await agent.run(
            "調査結果を分析して",
            session=session,
            options={"response_format": AnalysisResult},
        )
        analysis = AnalysisResult.model_validate_json(result.text)
        print(f"\n確信度: {analysis.confidence}")


if __name__ == "__main__":
    asyncio.run(main())
```

## 規約

- `FoundryChatClient` を推奨プロバイダとして使用する
- ツールには `@tool` デコレータを使用する（旧 `@ai_function` は廃止）
- 関数パラメータには `Annotated[type, Field(description=...)]` を使用する
- マルチターン会話には `create_session()` を使用する（旧 `get_new_thread()` は廃止）
- ストリーミングは `run(stream=True)` を使用する（旧 `run_stream()` は廃止）
- 構造化出力は `options={"response_format": Model}` で渡す
- サービス管理 MCP には `client.get_mcp_tool()`、クライアント管理には `MCPStreamableHTTPTool` を使用する

## v1.0.0 での主要な破壊的変更

| 旧 (pre-release) | 新 (v1.0.0) |
|-------------------|-------------|
| `pip install agent-framework --pre` | `pip install agent-framework` |
| `ChatAgent` | `Agent` |
| `ChatMessage` | `Message` |
| `@ai_function` | `@tool` |
| `AIFunction` | `FunctionTool` |
| `agent.run_stream("...")` | `agent.run("...", stream=True)` |
| `agent.get_new_thread()` / `thread=` | `agent.create_session()` / `session=` |
| `HostedCodeInterpreterTool()` | `client.get_code_interpreter_tool()` |
| `HostedWebSearchTool()` | `client.get_web_search_tool()` |
| `HostedFileSearchTool()` | `client.get_file_search_tool(...)` |
| `HostedMCPTool(...)` | `client.get_mcp_tool(...)` |
| `response_format=Model` | `options={"response_format": Model}` |
| `azure.identity.aio` | `azure.identity`（同期版） |

## リファレンスファイル

- [references/tools.md](references/tools.md): ホステッドツールの詳細パターン
- [references/mcp.md](references/mcp.md): MCP 統合（サービス管理 + クライアント管理）
- [references/sessions.md](references/sessions.md): セッションと会話管理
- [references/advanced.md](references/advanced.md): OpenAPI、Citation、構造化出力
- [references/acceptance-criteria.md](references/acceptance-criteria.md): コード正確性の検証基準
