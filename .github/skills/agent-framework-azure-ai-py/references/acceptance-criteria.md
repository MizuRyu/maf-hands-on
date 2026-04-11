# Agent Framework v1.0.0 Python 受入基準

**SDK**: `agent-framework` (v1.0.0 GA)
**リポジトリ**: https://github.com/microsoft/agent-framework
**目的**: 生成コードの正確性を検証するための受入基準

---

## 1. 正しい import パターン

### 1.1 コア import
```python
from agent_framework import Agent, Message, tool
```

### 1.2 プロバイダ import
```python
# Foundry（推奨）
from agent_framework.foundry import FoundryChatClient

# OpenAI
from agent_framework.openai import OpenAIChatClient

# Azure AI Persistent Agents V1（非推奨方向）
from agent_framework.azure import AzureAIAgentsProvider
```

### 1.3 認証 import
```python
from azure.identity import AzureCliCredential, DefaultAzureCredential
```

### 1.4 MCP ツール import
```python
from agent_framework import MCPStreamableHTTPTool
```

### 1.5 アンチパターン（エラー）
```python
# NG — 旧クラス名
from agent_framework import ChatAgent  # → Agent を使う

# NG — 旧ツールクラス（v1.0.0 で廃止）
from agent_framework import HostedCodeInterpreterTool
from agent_framework import HostedMCPTool

# NG — 旧デコレータ
from agent_framework import ai_function  # → tool を使う

# NG — async 版の identity（v1.0.0 では同期版を使用）
from azure.identity.aio import AzureCliCredential

# NG — Provider をコアから直接 import
from agent_framework import AzureAIAgentsProvider
```

---

## 2. エージェント作成パターン

### 2.1 FoundryChatClient（推奨）
```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)
agent = Agent(client=client, name="MyAgent", instructions="...")
```

### 2.2 as_agent ショートカット
```python
agent = client.as_agent(name="MyAgent", instructions="...")
```

### 2.3 アンチパターン（エラー）
- `model_id=` → `model=` を使う
- `ChatAgent(...)` → `Agent(...)` を使う
- `--pre` フラグ付きインストール → 不要（GA リリース）

---

## 3. セッション管理

### 3.1 正しいパターン
```python
session = agent.create_session()
result = await agent.run("こんにちは", session=session)
```

### 3.2 サーバーサイドセッションの再開
```python
session = agent.create_session(service_session_id="existing-session-id")
result = await agent.run("会話を続けて", session=session)
```

### 3.3 アンチパターン（エラー）
```python
# NG — 旧 API
thread = agent.get_new_thread()
result = await agent.run("...", thread=thread)

# NG — AgentThread の直接使用
from agent_framework import AgentThread
thread = AgentThread(service_thread_id="...")
```

---

## 4. ホステッドツール

### 4.1 正しいパターン
```python
tools = [
    client.get_code_interpreter_tool(),
    client.get_web_search_tool(),
    client.get_file_search_tool(vector_store_ids=["vs-123"]),
    client.get_mcp_tool(name="MCP", url="https://...", approval_mode="never_require"),
]
```

### 4.2 アンチパターン（エラー）
```python
# NG — 旧クラスベース API（v1.0.0 で廃止）
tools = [HostedCodeInterpreterTool()]
tools = [HostedWebSearchTool(name="Bing")]
tools = [HostedMCPTool(name="MCP", url="...")]
```

---

## 5. ツール定義

### 5.1 正しいパターン
```python
from agent_framework import tool

@tool
def my_function(param: str) -> str:
    """関数の説明。"""
    return "結果"
```

### 5.2 アンチパターン（エラー）
```python
# NG — 旧デコレータ
@ai_function
def my_function(param: str) -> str: ...
```

---

## 6. ストリーミング

### 6.1 正しいパターン
```python
async for chunk in agent.run("質問", stream=True):
    if chunk.text:
        print(chunk.text, end="")
```

### 6.2 アンチパターン（エラー）
```python
# NG — 旧メソッド（v1.0.0 で廃止）
async for chunk in agent.run_stream("質問"):
    ...
```

---

## 7. 構造化出力

### 7.1 正しいパターン
```python
result = await agent.run("質問", options={"response_format": MyModel})
```

### 7.2 アンチパターン（エラー）
```python
# NG — 旧 API（直接パラメータ渡し）
result = await agent.run("質問", response_format=MyModel)
```

---

## 8. v1.0.0 変更チェックリスト

| チェック項目 | 旧 | 新 |
|-------------|----|----|
| パッケージインストール | `pip install agent-framework --pre` | `pip install agent-framework` |
| エージェントクラス | `ChatAgent` | `Agent` |
| メッセージクラス | `ChatMessage` | `Message` |
| ツールデコレータ | `@ai_function` | `@tool` |
| ツール型 | `AIFunction` | `FunctionTool` |
| ストリーミング | `run_stream()` | `run(stream=True)` |
| セッション | `get_new_thread()` / `thread=` | `create_session()` / `session=` |
| ホステッドツール | `Hosted*Tool()` クラス | `client.get_*_tool()` メソッド |
| 構造化出力 | `response_format=Model` | `options={"response_format": Model}` |
| 認証 | `azure.identity.aio` | `azure.identity` |
