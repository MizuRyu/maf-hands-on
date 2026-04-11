# MCP 統合リファレンス

Azure AI エージェントにおける Model Context Protocol (MCP) 統合パターン。

## 概要

Agent Framework v1.0.0 では 2 種類の MCP ツールをサポート:

| ツール | 管理方式 | ユースケース |
|-------|---------|------------|
| `client.get_mcp_tool(...)` | サービス管理 | Azure AI サービスが MCP サーバーに接続 |
| `MCPStreamableHTTPTool` | クライアント管理 | 自分のコードが MCP サーバーに接続 |

> **v1.0.0 変更点**: `HostedMCPTool` クラスは廃止。`client.get_mcp_tool(...)` に置換。

---

## サービス管理 MCP (`client.get_mcp_tool`)

Azure AI サービスが MCP 接続のライフサイクルを管理する。

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
    name="DocsAgent",
    instructions="Microsoft ドキュメントを使って質問に回答します。",
    tools=[
        client.get_mcp_tool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
            approval_mode="never_require",
        ),
    ],
)

result = await agent.run("Azure Functions の使い方は？")
print(result.text)
```

### ツールフィルタ付き

```python
mcp_tool = client.get_mcp_tool(
    name="Microsoft Learn MCP",
    url="https://learn.microsoft.com/api/mcp",
    approval_mode="never_require",
    allowed_tools=["microsoft_docs_search", "microsoft_docs_read"],
)
```

### 認証ヘッダー付き

```python
mcp_tool = client.get_mcp_tool(
    name="Private MCP Server",
    url="https://my-mcp-server.example.com/mcp",
    approval_mode="never_require",
    headers={
        "Authorization": "Bearer your-api-key",
        "X-Custom-Header": "custom-value",
    },
)
```

### 承認モード

```python
# 承認不要（自動実行）
mcp_tool = client.get_mcp_tool(
    name="Safe MCP",
    url="https://safe-mcp.example.com/mcp",
    approval_mode="never_require",
)

# 常に承認必要
mcp_tool = client.get_mcp_tool(
    name="Sensitive MCP",
    url="https://sensitive-mcp.example.com/mcp",
    approval_mode="always_require",
)

# ツール別の承認設定
mcp_tool = client.get_mcp_tool(
    name="Mixed MCP",
    url="https://mcp.example.com/mcp",
    approval_mode={
        "always_require_approval": ["delete_resource", "modify_config"],
        "never_require_approval": ["search", "read"],
    },
)
```

---

## クライアント管理 MCP (`MCPStreamableHTTPTool`)

```python
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

async with MCPStreamableHTTPTool(
    name="Microsoft Learn MCP",
    url="https://learn.microsoft.com/api/mcp",
) as mcp_tool:
    agent = Agent(
        client=client,
        name="DocsAgent",
        instructions="ドキュメントを使って質問に回答します。",
        tools=[mcp_tool],
    )

    result = await agent.run("Azure AI Foundry とは？")
    print(result.text)
```

### 認証付き（header_provider パターン）

```python
from agent_framework import MCPStreamableHTTPTool

mcp_tool = MCPStreamableHTTPTool(
    name="GitHub MCP",
    url="https://api.github.com/mcp",
    header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['mcp_api_key']}"},
)

# 実行時に kwargs で API キーを渡す
result = await agent.run(
    "リポジトリの一覧を取得して",
    function_invocation_kwargs={"mcp_api_key": github_pat},
)
```

### 複数 MCP ツール

```python
async with (
    MCPStreamableHTTPTool(
        name="Docs MCP",
        url="https://learn.microsoft.com/api/mcp",
    ) as docs_mcp,
    MCPStreamableHTTPTool(
        name="GitHub MCP",
        url="https://api.github.com/mcp",
        header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['token']}"},
    ) as github_mcp,
):
    agent = Agent(
        client=client,
        name="MultiMCPAgent",
        instructions="ドキュメント検索と GitHub 操作ができます。",
        tools=[docs_mcp, github_mcp],
    )
```

---

## サービス管理 vs クライアント管理 MCP

| 観点 | `client.get_mcp_tool()` | `MCPStreamableHTTPTool` |
|------|------------------------|------------------------|
| 接続管理者 | Azure AI サービス | 自分のコード |
| コンテキストマネージャ | 不要 | 必須 |
| 最適な用途 | 公開 MCP サーバー | 認証付き/プライベートサーバー |
| 接続ライフサイクル | 自動 | 手動（コンテキストマネージャ経由） |
| 認証方法 | `headers` パラメータ | `header_provider` コールバック |

---

## MCP と他ツールの組み合わせ

```python
from agent_framework import Agent, tool, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

@tool
def get_user_id() -> str:
    """現在のユーザー ID を取得する。"""
    return "user-123"

client = FoundryChatClient(
    project_endpoint="https://<project>.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)

async with MCPStreamableHTTPTool(
    name="Company API MCP",
    url="https://internal-api.company.com/mcp",
) as company_mcp:
    agent = Agent(
        client=client,
        name="EnterpriseAgent",
        instructions="""エンタープライズアシスタント:
        - Python コード実行（分析用）
        - 社内 API へのアクセス（MCP 経由）
        - ユーザー情報の取得

        機密データへのアクセス前にユーザー認証を確認すること。""",
        tools=[
            get_user_id,
            client.get_code_interpreter_tool(),
            company_mcp,
        ],
    )
```

---

## MCP のエラーハンドリング

```python
try:
    async with MCPStreamableHTTPTool(
        name="MCP Server",
        url="https://mcp.example.com",
    ) as mcp_tool:
        agent = Agent(client=client, name="Agent", instructions="...", tools=[mcp_tool])
        result = await agent.run("MCP を使ってクエリ")

except ConnectionError as e:
    print(f"MCP サーバーへの接続失敗: {e}")
except TimeoutError as e:
    print(f"MCP 接続タイムアウト: {e}")
```

---

## ナレッジベース MCP 統合

```python
kb_mcp_endpoint = f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2025-11-01-preview"

agent = Agent(
    client=client,
    name="KBAgent",
    instructions="""ナレッジベースを使って質問に回答します。
    出典は常に次の形式で引用すること: 【source†title】""",
    tools=[
        client.get_mcp_tool(
            name="Knowledge Base",
            url=kb_mcp_endpoint,
            approval_mode="never_require",
            allowed_tools=["knowledge_base_retrieve"],
        ),
    ],
)
```
