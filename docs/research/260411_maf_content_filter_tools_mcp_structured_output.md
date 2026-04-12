# MAF 1.0.0: Content Filter / Foundry Tools / MCP / Structured Output / Hosted Agent 調査

**調査日:** 2026-04-11
**最終更新日:** 2026-04-11

---

## 1. Foundry Content Filter / RAI

### 1.1 何ができるか

Azure AI Foundry の Content Filter はデプロイメント単位で有害コンテンツ (暴力・自傷・性的・憎悪) をフィルタリングする。
MAF からは **2つのレイヤー** でコンテンツ安全性を制御できる。

| レイヤー | 設定場所 | 仕組み |
|---------|---------|--------|
| **Foundry デプロイメントレベル** | Azure AI Foundry ポータル / REST API | モデルデプロイメントに RAI Policy を紐付け。prompt/completion 両方でフィルタ |
| **MAF Middleware レベル** | `PurviewPolicyMiddleware` | Microsoft Purview と連携し、Agent の入出力をポリシーチェック |

### 1.2 rai_config (デプロイメントレベル)

`rai_config` は **Foundry REST API でデプロイメント作成時** に指定する Content Filter 設定。
MAF 自体には `rai_config` パラメータは存在しない。Foundry サービス側の設定。

```
REST API: PUT /deployments/{deployment-name}
→ body.properties.raiPolicyName = "カスタムポリシー名"
```

設定方法:
1. Azure AI Foundry ポータル → Models + endpoints → デプロイメント → Edit → Content Filter 選択
2. REST API: `POST /rai-policies` で RAI ポリシーを作成 → デプロイメントに紐付け

フィルタ粒度:

| Severity | prompt | completion |
|----------|--------|------------|
| Low, Medium, High | Yes | Yes |
| Medium, High | Yes | Yes |
| High only | Yes | Yes |
| No filters | 要承認 | 要承認 |
| Annotate only | 要承認 | 要承認 |

### 1.3 PurviewPolicyMiddleware (MAF Middleware レベル)

パッケージ: `agent_framework_purview` (`pip install agent-framework-purview`)

```python
from agent_framework.microsoft import PurviewPolicyMiddleware, PurviewSettings
from agent_framework import Agent

credential = AzureCliCredential()
settings = PurviewSettings(app_name="My App")

agent = Agent(
    client=client,
    instructions="...",
    middleware=[PurviewPolicyMiddleware(credential, settings)],
)
```

**動作:**
- **Pre (prompt)**: ユーザー入力を Purview に送信 (`Activity.UPLOAD_TEXT`)。ブロック判定→ `"Prompt blocked by policy"` を返し `MiddlewareTermination` で中断
- **Post (response)**: Agent 応答を Purview に送信 (`Activity.DOWNLOAD_TEXT`)。ブロック判定→応答を差し替え

**クラス一覧:**

| クラス | 用途 |
|-------|------|
| `PurviewPolicyMiddleware` | AgentMiddleware。Agent レベルで適用 |
| `PurviewChatPolicyMiddleware` | ChatMiddleware。ChatClient レベルで適用 |
| `PurviewSettings` | 設定 (`app_name`, `blocked_prompt_message`, `blocked_response_message`, `ignore_exceptions`, `ignore_payment_required`) |
| `PurviewClient` | Purview API クライアント |
| `CacheProvider` | キャッシュプロバイダ (オプション) |

**制約:**
- ストリーミング応答の Post チェックは **非対応** (ログ出力のみ)
- `PurviewPaymentRequiredError` 発生時は `ignore_payment_required` で制御

### 1.4 MAF の Agent Filter / Middleware 設計 (ADR-0007)

MAF は Agent Filter Decorator パターンを採用。`DelegatingAIAgent` でラップし、実行前後にフィルタ処理を差し込む。

```csharp
// .NET: GuardrailCallbackAgent の例
internal sealed class GuardrailCallbackAgent : DelegatingAIAgent
{
    private readonly string[] _forbiddenKeywords = { "harmful", "illegal", "violence" };
    // ... 実行前後にキーワードチェック
}
```

Python ではミドルウェアパターン:
```python
agent = Agent(
    client=client,
    middleware=[PurviewPolicyMiddleware(credential, settings)],
)
```

---

## 2. Foundry Tool 連携

### 2.1 何ができるか

Foundry Agent Service に登録されたビルトインツールを MAF Agent から利用可能。

### 2.2 ビルトインツール一覧 (Foundry Agent Service)

| ツール | type | 説明 |
|--------|------|------|
| Web Search (Bing) | `web_search` / `bing_grounding` | リアルタイム Web 検索 + インライン引用 |
| File Search | `file_search` | アップロードファイルからの RAG |
| Code Interpreter | `code_interpreter` | サンドボックス Python 実行 |
| Azure AI Search | `azure_ai_search` | 既存 AI Search インデックス連携 |
| Azure Functions | `azure_functions` | カスタム Azure Functions 呼び出し |
| Function Calling | `function` | ローカル関数定義・実行 |
| MCP Tool | `mcp` | リモート MCP サーバー接続 |
| OpenAPI Tool | `openapi` | OpenAPI Spec 経由の Web サービス呼び出し |
| Image Generation | `image_generation` | 画像生成 |
| Browser Automation | `browser_automation` | ブラウザ操作 |
| Computer Use | `computer_use` | PC UI 操作 |
| SharePoint | `sharepoint` | SharePoint ドキュメント検索 |
| Microsoft Fabric | `fabric` | Fabric データエージェント |

### 2.3 MAF から Foundry ツールを使う方法

#### Python: Foundry Agent Service SDK 経由 (PromptAgent / Hosted Agent)

Foundry に登録したツールは **サーバーサイドで実行** される。MAF の `FoundryAgent` はこれらを Responses API 経由で利用。

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, WebSearchTool, MCPTool

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

agent = project.agents.create_version(
    agent_name="MyAgent",
    definition=PromptAgentDefinition(
        model="gpt-5-mini",
        instructions="You are helpful",
        tools=[
            WebSearchTool(),                    # Bing Web Search
            {"type": "code_interpreter"},        # Code Interpreter
            {"type": "file_search"},             # File Search
            MCPTool(                             # MCP
                server_label="github",
                server_url="https://api.githubcopilot.com/mcp",
                require_approval="always",
            ),
        ],
    ),
)
```

#### .NET: FoundryAITool ファクトリクラス

`Microsoft.Agents.AI.Foundry` パッケージの `FoundryAITool` が統一ファクトリ。

```csharp
using Microsoft.Agents.AI.Foundry;

// Bing Search
AITool bingTool = FoundryAITool.CreateBingGroundingTool(options);

// File Search
AITool fileSearchTool = FoundryAITool.CreateFileSearchTool(vectorStoreIds, maxResultCount);

// Code Interpreter
AITool codeInterpreterTool = FoundryAITool.CreateCodeInterpreterTool(container);

// Web Search
AITool webSearchTool = FoundryAITool.CreateWebSearchTool(userLocation, searchContextSize);

// OpenAPI Tool
AITool openApiTool = FoundryAITool.CreateOpenApiTool(definition);

// MCP Tool
AITool mcpTool = FoundryAITool.CreateMcpTool(serverLabel, serverUri, authorizationToken);

// Azure AI Search
AITool aiSearchTool = FoundryAITool.CreateAzureAISearchTool(options);

// SharePoint
AITool sharepointTool = FoundryAITool.CreateSharepointTool(options);

// A2A Tool
AITool a2aTool = FoundryAITool.CreateA2ATool(baseUri);

// Image Generation
AITool imageGenTool = FoundryAITool.CreateImageGenerationTool(model);
```

#### Python: MAF FoundryAgent (ローカルツール実行)

`FoundryAgent` はサーバーサイド Agent に接続しつつ、**ローカル FunctionTool も実行可能**。
ただし MCPTool や dict schema などの hosted tool は **Foundry 側で定義する必要** がある。

```python
from agent_framework.foundry import FoundryAgent

agent = FoundryAgent(
    project_endpoint="https://your-project.services.ai.azure.com",
    agent_name="my-prompt-agent",
    agent_version="1.0",
    credential=AzureCliCredential(),
    tools=[my_local_function_tool],  # FunctionTool のみ許可
)
result = await agent.run("Hello!")
```

**制約**: `FoundryAgent` の `tools` パラメータには `FunctionTool` のみ渡せる。MCPTool / dict schemas / hosted tools は Foundry サービス側の Agent 定義で設定する。

---

## 3. MCP (Model Context Protocol) ツール

### 3.1 何ができるか

MCP はモデルが外部ツール・データソースに接続するためのオープンプロトコル。
MAF は **2つの接続パターン** を提供。

| パターン | 使い方 | 実行場所 |
|---------|--------|---------|
| **Foundry Agent Service MCP Tool** | `MCPTool` を PromptAgent 定義に追加 | サーバーサイド (Foundry) |
| **MAF ローカル MCP 接続** | `MCPTool` クラスで直接接続 | クライアントサイド (ローカル) |

### 3.2 Foundry Agent Service での MCP Tool

```python
from azure.ai.projects.models import MCPTool

tool = MCPTool(
    server_label="api-specs",
    server_url="https://api.githubcopilot.com/mcp",
    require_approval="always",               # "always" | "never" | {"always": [...]} | {"never": [...]}
    project_connection_id="my-mcp-connection", # 認証用 Project Connection
    allowed_tools=["search_code"],            # オプション: 許可ツールフィルタ
)
```

**Approval フロー:**
1. Agent が MCP ツール呼び出しを要求 → `mcp_approval_request` が output に含まれる
2. 開発者がリクエスト内容を確認
3. `mcp_approval_response` で承認/拒否を送信
4. 承認後、MCP ツールが実行され結果が返る

**認証:**
- `project_connection_id` で Foundry の Project Connection を参照
- Custom Keys 接続: `Authorization: Bearer <token>` 形式
- Azure DevOps MCP Server は Foundry カタログから直接追加可能

### 3.3 MAF ローカル MCP 接続 (Python)

`agent_framework._mcp` モジュールの `MCPTool` クラスで直接 MCP サーバーに接続。

```python
from agent_framework import Agent, MCPTool

# コンテキストマネージャとして使用
async with MCPTool(
    name="my-mcp",
    command="uvx",
    args=["my-mcp-server"],
    approval_mode="never",      # "always" | "never" | MCPSpecificApproval
) as mcp_tool:
    agent = Agent(
        client=client,
        tools=[mcp_tool],
    )
    result = await agent.run("...")
```

**MCPTool 主要パラメータ:**

| パラメータ | 型 | 説明 |
|-----------|---|------|
| `name` | str | ツール名 |
| `command` | str | stdio 接続用コマンド |
| `args` | list[str] | コマンド引数 |
| `url` | str | SSE/Streamable HTTP 接続用 URL |
| `headers` | dict | HTTP ヘッダー |
| `approval_mode` | str / MCPSpecificApproval | 承認モード |
| `env` | dict | 環境変数 |
| `timeout` | timedelta | タイムアウト |

**接続方式:**
- **stdio**: `command` + `args` でローカルプロセス起動
- **SSE / Streamable HTTP**: `url` でリモートサーバー接続

### 3.4 .NET での MCP Tool

```csharp
// FoundryAITool ファクトリ
AITool mcpTool = FoundryAITool.CreateMcpTool(
    serverLabel: "github",
    serverUri: new Uri("https://api.githubcopilot.com/mcp"),
    authorizationToken: "Bearer ...",
    allowedTools: new McpToolFilter(...),
    toolCallApprovalPolicy: new McpToolCallApprovalPolicy(
        GlobalMcpToolCallApprovalPolicy.AlwaysRequireApproval
    )
);

// ConnectorId 経由 (Foundry カタログ接続)
AITool mcpTool2 = FoundryAITool.CreateMcpTool(
    serverLabel: "devops",
    connectorId: new McpToolConnectorId("..."),
);
```

### 3.5 制約・制限事項

- Non-streaming MCP ツール呼び出しタイムアウト: **100 秒**
- Private MCP は **Standard Agent Setup + BYO VNet** が必要 (Basic では不可)
- Private MCP ホスティング: Azure Container Apps のみ検証済み
- `anyOf` / `allOf` を含む MCP スキーマは Invalid tool schema エラー
- ローカル MCP サーバーを Foundry で使うには Container Apps or Azure Functions でホスト必要

---

## 4. Foundry Agent Service との同期

### 4.1 agent.yaml スキーマ

Hosted Agent のデプロイに使用。スキーマ: `https://raw.githubusercontent.com/microsoft/AgentSchema/refs/heads/main/schemas/v1.0/ContainerAgent.yaml`

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/microsoft/AgentSchema/refs/heads/main/schemas/v1.0/ContainerAgent.yaml

kind: hosted                      # "hosted" (コンテナ) or "prompt" (モデル直接)
name: my-agent
description: >
  Travel assistant agent
metadata:
  authors:
    - Microsoft
  tags:
    - Azure AI AgentServer
    - Microsoft Agent Framework
protocols:
  - protocol: responses           # Responses API 準拠
    version: v1
environment_variables:
  - name: FOUNDRY_PROJECT_ENDPOINT
    value: ${FOUNDRY_PROJECT_ENDPOINT}
  - name: FOUNDRY_MODEL
    value: ${FOUNDRY_MODEL}
resources:                        # オプション: モデルリソース定義
  - name: "gpt-5.4-mini"
    kind: model
    id: gpt-5.4-mini
```

### 4.2 Hosted Agent デプロイ方法

#### Azure Developer CLI (azd) 経由 (推奨)

```bash
# 1. 拡張インストール
azd ext install azure.ai.agents

# 2. プロジェクト初期化
azd ai agent init -m <agent.yaml のURL or パス>

# 3. リソースプロビジョニング + デプロイ
azd up

# 4. ローカルテスト
azd ai agent run                     # ローカル起動
azd ai agent invoke --local "Hello"  # テストメッセージ

# 5. デプロイのみ
azd deploy
```

`azd up` が行うこと:
1. Bicep でインフラ構築 (Foundry project, ACR, App Insights, Managed Identity)
2. モデルデプロイメント作成
3. コンテナイメージビルド & ACR プッシュ
4. Agent Application 作成 & デプロイ

#### Python SDK 経由

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import HostedAgentDefinition, ProtocolVersionRecord, AgentProtocol

project = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential, allow_preview=True)

agent = project.agents.create_version(
    agent_name="my-agent",
    definition=HostedAgentDefinition(
        container_protocol_versions=[
            ProtocolVersionRecord(protocol=AgentProtocol.RESPONSES, version="v1")
        ],
        cpu="1",
        memory="2Gi",
        image="myregistry.azurecr.io/myagent:v1",
        tools=[
            {"type": "code_interpreter"},
            {"type": "mcp", "project_connection_id": "..."},
        ],
        environment_variables={
            "AZURE_AI_PROJECT_ENDPOINT": PROJECT_ENDPOINT,
            "MODEL_NAME": "gpt-5-mini",
        },
    ),
)
```

### 4.3 PromptAgent vs HostedAgent

| 項目 | PromptAgent | HostedAgent |
|-----|-------------|-------------|
| 定義 | model + instructions + tools | コンテナイメージ |
| コード実行 | サーバーサイドのみ | カスタムコード (任意フレームワーク) |
| バージョニング | `agent_version` 必須 | `agent_version` オプション |
| ローカルツール | 不可 (Foundry ビルトインのみ) | 可 (コンテナ内で自由に実行) |
| デプロイ | SDK / REST API / ポータル | azd + Docker + ACR |

### 4.4 MAF FoundryAgent クラス

MAF Python SDK で Foundry の既存 Agent に接続:

```python
from agent_framework.foundry import FoundryAgent

# PromptAgent に接続
agent = FoundryAgent(
    project_endpoint="https://your-project.services.ai.azure.com",
    agent_name="my-prompt-agent",
    agent_version="1.0",
    credential=AzureCliCredential(),
)

# HostedAgent に接続 (version 不要)
agent = FoundryAgent(
    project_endpoint="...",
    agent_name="my-hosted-agent",
    credential=AzureCliCredential(),
)

result = await agent.run("Hello!")
```

環境変数: `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_AGENT_NAME`, `FOUNDRY_AGENT_VERSION`

---

## 5. Structured Output / Response Format

### 5.1 何ができるか

Agent の出力を JSON スキーマに準拠した構造化データとして取得。Pydantic モデル / JSON Schema / dict に対応。

### 5.2 Python での使い方

#### Pydantic モデル

```python
from pydantic import BaseModel

class PersonInfo(BaseModel):
    name: str | None = None
    age: int | None = None
    occupation: str | None = None

# 方法1: run() の response_format パラメータ
response = await agent.run(
    "John Smith は 35 歳のソフトウェアエンジニアです。",
    response_format=PersonInfo,
)
person = response.value  # PersonInfo インスタンス

# 方法2: Agent コンストラクタの default_options
agent = client.as_agent(
    name="extractor",
    instructions="Extract person info.",
)
response = await agent.run(query, options={"response_format": PersonInfo})
```

#### JSON Schema (dict)

```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}

response = await agent.run("...", response_format=schema)
person = response.value  # dict
```

#### ストリーミング + Structured Output

```python
stream = agent.run(query, stream=True, options={"response_format": PersonInfo})
async for update in stream:
    print(update.text, end="", flush=True)

final = await stream.get_final_response()
person = final.value  # PersonInfo
```

### 5.3 .NET での使い方

#### RunAsync\<T\> (推奨)

```csharp
AgentResponse<PersonInfo> response = await agent.RunAsync<PersonInfo>(
    "John Smith is a 35-year-old software engineer."
);
Console.WriteLine($"Name: {response.Result.Name}");
```

- `AIAgent` 基底クラスのメソッド (全デコレータ対応)
- プリミティブ・配列型もサポート (内部でラップ/アンラップ)

#### ResponseFormat (柔軟)

```csharp
AgentRunOptions options = new()
{
    ResponseFormat = ChatResponseFormat.ForJsonSchema<PersonInfo>()
};
AgentResponse response = await agent.RunAsync("...", options: options);
PersonInfo info = JsonSerializer.Deserialize<PersonInfo>(response.Text);
```

#### Raw JSON Schema

```csharp
string jsonSchema = """{"type":"object","properties":{"name":{"type":"string"}}}""";
AgentRunOptions options = new()
{
    ResponseFormat = ChatResponseFormat.ForJsonSchema(
        jsonSchemaName: "PersonInfo",
        jsonSchema: BinaryData.FromString(jsonSchema))
};
```

### 5.4 設計判断 (ADR-0016)

| アプローチ | 用途 | 制約 |
|-----------|------|------|
| `ResponseFormat` | コンパイル時に型不明 / JSON Schema テキスト / inter-agent / streaming | プリミティブ・配列 **非対応** (wrapper 必要) |
| `RunAsync<T>` / `response_format=Model` | コンパイル時に型既知 / typed result 必要 | コンパイル時型が必要 |

**プリミティブ・配列の扱い:**
- `RunAsync<T>` (Python: `response_format=Model`) → フレームワークが自動ラップ/アンラップ
- `ResponseFormat` → 呼び出し側でラッパー型を定義する必要あり

```python
# NG: list[str] は直接使えない
# OK: ラッパー
class MovieList(BaseModel):
    movies: list[str]
```

### 5.5 制約

- 全ての Agent タイプが Structured Output をサポートするわけではない (ChatClientAgent / OpenAI 系のみ)
- `useJsonSchemaResponseFormat` (LLM にスキーマをテキストで渡す方式) は信頼性不足で **非推奨**
- ストリーミング時は全チャンク受信後にデシリアライズ

---

## 参考リンク

- [Content Filter 設定](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/content-filters)
- [Responsible AI for Foundry](https://learn.microsoft.com/azure/foundry/responsible-use-of-ai-overview)
- [Foundry Agent Tools 一覧](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog)
- [MCP Tool 接続](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol)
- [Hosted Agent デプロイ](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Structured Output (MAF)](https://learn.microsoft.com/agent-framework/agents/structured-output)
- [MAF GitHub: _mcp.py](https://github.com/microsoft/agent-framework/blob/main/python/packages/core/agent_framework/_mcp.py)
- [MAF GitHub: FoundryAITool.cs](https://github.com/microsoft/agent-framework/blob/main/dotnet/src/Microsoft.Agents.AI.Foundry/FoundryAITool.cs)
- [MAF GitHub: PurviewPolicyMiddleware](https://github.com/microsoft/agent-framework/blob/main/python/packages/purview/agent_framework_purview/_middleware.py)
- [MAF ADR-0016: Structured Output](https://github.com/microsoft/agent-framework/blob/main/docs/decisions/0016-structured-output.md)
- [MAF ADR-0002: Agent Tools](https://github.com/microsoft/agent-framework/blob/main/docs/decisions/0002-agent-tools.md)
- [MAF Spec: Foundry SDK Alignment](https://github.com/microsoft/agent-framework/blob/main/docs/specs/001-foundry-sdk-alignment.md)
