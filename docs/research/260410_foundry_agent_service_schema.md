# Foundry Agent Service エージェント定義スキーマ調査

調査日: 2026-04-10
最終更新日: 2026-04-10

---

## 1. agent.yaml スキーマ（VS Code Classic / Prompt Agent）

VS Code 拡張で使われる Classic Prompt Agent の YAML 定義。スキーマ URL: `https://aka.ms/ai-foundry-vsc/agent/1.0.0`

```yaml
# yaml-language-server: $schema=https://aka.ms/ai-foundry-vsc/agent/1.0.0
version: 1.0.0
name: my-agent                    # 必須: エージェント名
description: Description          # 任意: 説明 (maxLength: 512)
id: ''                            # 自動生成: 一意識別子
metadata:
  authors:
    - author1
  tags:
    - tag1
model:
  id: 'gpt-4o-1'                 # 必須: デプロイ済みモデル名
  options:
    temperature: 1                # 任意: 0-2
    top_p: 1                      # 任意: 0-1
instructions: Instructions text   # 必須: システムプロンプト
tools: []                         # 任意: ツール配列
```

### フィールド一覧

| フィールド | 型 | 必須 | 説明 |
|-----------|------|------|------|
| `version` | string | Yes | スキーマバージョン（`1.0.0`） |
| `name` | string | Yes | エージェント名（英数字・ハイフン、max 63 文字） |
| `description` | string | No | 説明（max 512 文字） |
| `id` | string | Auto | VS Code 拡張が自動生成 |
| `metadata.authors` | string[] | No | 作者一覧 |
| `metadata.tags` | string[] | No | タグ一覧 |
| `model.id` | string | Yes | デプロイ済みモデルのデプロイ名 |
| `model.options.temperature` | number | No | サンプリング温度 |
| `model.options.top_p` | number | No | Nucleus サンプリング |
| `instructions` | string | Yes | システムプロンプト/指示 |
| `tools` | array | No | ツール定義の配列 |

### 利用可能なツール

- Grounding with Bing Search
- File Search
- Code Interpreter
- OpenAPI Spec Tool
- MCP (Model Context Protocol)

---

## 2. agent.yaml スキーマ（Hosted Agent / azd 拡張）

Hosted Agent は `agent.yaml` + `Dockerfile` + アプリコードの 3 点セットでデプロイする。

```yaml
name: agents-in-workflow
description: >
  A workflow agent that responds to product launch strategy inquiries
  by concurrently leveraging insights from three specialized agents.

metadata:
  authors:
    - Microsoft Agent Framework Team
  tags:
    - Azure AI AgentServer
    - Microsoft Agent Framework

template:
  name: agents-in-workflow
  kind: hosted                     # hosted / prompt / workflow
  protocols:
    - protocol: responses          # responses または activity_protocol
      version: v1                  # 省略可
  environment_variables:
    - name: AZURE_OPENAI_ENDPOINT
      value: ${AZURE_OPENAI_ENDPOINT}
    - name: AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
      value: "{{chat}}"            # resources の name を参照

resources:
  - kind: model
    id: gpt-4o-mini                # モデルカタログ上の ID
    name: chat                     # template.environment_variables から参照
```

### Hosted Agent 固有フィールド

| フィールド | 説明 |
|-----------|------|
| `template.kind` | `hosted`（コンテナベース） |
| `template.protocols` | 対応プロトコル（`responses` / `activity_protocol`） |
| `template.environment_variables` | コンテナに渡す環境変数 |
| `resources` | 依存リソース（model、connection 等） |

---

## 3. REST API のエージェント定義（AgentDefinition）

REST API `POST {endpoint}/agents?api-version=v1` で登録するリクエストボディ。

### CreateAgentRequest

| フィールド | 型 | 必須 | 説明 |
|-----------|------|------|------|
| `name` | string | Yes | 一意名（英数字+ハイフン、max 63 文字） |
| `description` | string | No | 説明（max 512 文字） |
| `metadata` | object | No | key-value 16 個まで（key max 64, value max 512） |
| `definition` | AgentDefinition | Yes | エージェント定義本体 |
| `definition.kind` | AgentKind | Yes | `prompt` / `hosted` / `workflow` / `container_app` |
| `definition.rai_config` | RaiConfig | No | Responsible AI フィルタ設定 |

### AgentKind（Discriminator）

| kind | スキーマ | 説明 |
|------|---------|------|
| `prompt` | PromptAgentDefinition | 構成のみで定義。コード不要。 |
| `hosted` | HostedAgentDefinition | コンテナベース。フレームワーク自由。 |
| `workflow` | WorkflowAgentDefinition | マルチエージェント・分岐ロジック。 |
| `container_app` | ContainerAppAgentDefinition | Container Apps ベース。 |

### PromptAgentDefinition

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|------|------|----------|------|
| `kind` | `"prompt"` | Yes | - | |
| `model` | string | Yes | - | モデルデプロイ名 |
| `instructions` | string | No | - | システムプロンプト |
| `tools` | OpenAI.Tool[] | No | - | ツール配列 |
| `tool_choice` | string / object | No | - | ツール選択戦略 |
| `temperature` | number | No | 1 | サンプリング温度 |
| `top_p` | number | No | 1 | Nucleus サンプリング |
| `reasoning` | object | No | - | o-series/gpt-5 専用推論設定 |
| `structured_inputs` | object | No | - | テンプレート置換用入力 |
| `text.format` | object | No | - | JSON Schema / JSON Object 出力 |
| `rai_config` | RaiConfig | No | - | RAI ポリシー |

### HostedAgentDefinition

| フィールド | 型 | 必須 | 説明 |
|-----------|------|------|------|
| `kind` | `"hosted"` | Yes | |
| `image` | string | No | ACR イメージ URI（tag 付き） |
| `cpu` | string | Yes | CPU 割当（例: `"1"`） |
| `memory` | string | Yes | メモリ割当（例: `"2Gi"`） |
| `container_protocol_versions` | ProtocolVersionRecord[] | Yes | 対応プロトコル |
| `environment_variables` | object | No | コンテナ環境変数 |
| `tools` | OpenAI.Tool[] | No | Code Interpreter, MCP 等 |
| `rai_config` | RaiConfig | No | RAI ポリシー |

---

## 4. MAF Agent クラスと Foundry Agent 定義の対応関係

### .NET の場合

```
AIAgent（基底クラス）
├── Id            → AgentObject.id
├── Name          → AgentObject.name / CreateAgentRequest.name
├── Description   → CreateAgentRequest.description
└── AdditionalProperties → CreateAgentRequest.metadata

ChatClientAgent（主要な実装クラス）
├── instructions  → PromptAgentDefinition.instructions
├── tools         → PromptAgentDefinition.tools
├── model         → PromptAgentDefinition.model
├── temperature   → PromptAgentDefinition.temperature
└── topP          → PromptAgentDefinition.top_p
```

### Python の場合

```
Agent（基底クラス）
├── name          → AgentObject.name
├── instructions  → PromptAgentDefinition.instructions
├── tools         → PromptAgentDefinition.tools
└── client        → モデル接続（FoundryChatClient 等）
```

### Foundry SDK 連携コード例

```csharp
// .NET: Foundry SDK で作成 → MAF Agent として使う
var persistentAgentsClient = new PersistentAgentsClient(endpoint, credential);
AIAgent agent = await persistentAgentsClient.CreateAIAgentAsync(
    model: "gpt-4o-mini",
    name: "Joker",
    instructions: "You are good at telling jokes.",
    description: "A joke-telling agent",
    tools: myTools,
    temperature: 0.8f
);
// MAF の RunAsync でそのまま実行可能
var response = await agent.RunAsync("Tell me a joke.");
```

```python
# Python: Foundry SDK で作成 → MAF Agent として使う
from agent_framework.azure import AzureAIProjectAgentProvider
from azure.ai.projects import AIProjectClient

client = AIProjectClient(endpoint, credential)
provider = AzureAIProjectAgentProvider(client)
agent = await provider.create_agent(
    name="MyAgent",
    model="gpt-4o-mini",
    instructions="You are a helpful assistant."
)
response = await agent.run("Hello!")
```

### 対応マッピング表

| MAF プロパティ | Foundry REST API | agent.yaml (Classic) | agent.yaml (Hosted) |
|---------------|-----------------|---------------------|---------------------|
| Name | `name` | `name` | `name` |
| Description | `description` | `description` | `description` |
| Instructions | `definition.instructions` | `instructions` | コード内で設定 |
| Model | `definition.model` | `model.id` | `resources[].id` + env var |
| Tools | `definition.tools` | `tools` | `template.environment_variables` + コード |
| Temperature | `definition.temperature` | `model.options.temperature` | コード内で設定 |
| TopP | `definition.top_p` | `model.options.top_p` | コード内で設定 |
| Metadata | `metadata` | `metadata` | `metadata` |
| Id | `id` (auto) | `id` (auto) | - |

---

## 5. Hosted Agent vs Prompt Agent vs Self-hosted（MAF）の違い

### 比較表

| 観点 | Prompt Agent | Hosted Agent (Preview) | MAF Self-hosted |
|------|-------------|----------------------|-----------------|
| **コード要否** | 不要（構成のみ） | 必要 | 必要 |
| **ホスティング** | フルマネージド | コンテナベース・マネージド | 自前（App Service, ACA 等） |
| **オーケストレーション** | シングルエージェント | カスタムロジック自由 | カスタムロジック自由 |
| **フレームワーク** | なし | MAF / LangGraph / 任意 | MAF / 任意 |
| **スケーリング** | 自動 | Foundry 管理（replica 設定可） | 自前で管理 |
| **ネットワーク分離** | VNet 対応 | Preview では VNet 未対応 | VNet 完全対応 |
| **ツール** | 組込ツール全対応 | Code Interpreter, MCP, Web Search | 自前で統合 |
| **モニタリング** | App Insights 統合 | App Insights 統合 | 自前で設定 |
| **ID/認証** | Entra ID + RBAC | マネージド ID + RBAC | 自前で設定 |
| **バージョニング** | 自動スナップショット | 自動バージョン管理 | 自前で管理 |
| **パブリッシュ** | Teams / M365 Copilot / Entra Registry | 同左 | 自前でエンドポイント公開 |
| **用途** | プロトタイプ、単純タスク | 複雑ワークフロー、マルチエージェント | 完全制御が必要な場合 |

### Hosted Agent デプロイ手順

#### 方法 1: Azure Developer CLI (azd)

```bash
# 1. テンプレート初期化
azd init -t Azure-Samples/azd-ai-starter-basic --location northcentralus

# 2. エージェント定義取り込み
azd ai agent init -m <repo-path-to-agent.yaml>

# 3. ローカルテスト
azd ai agent run
azd ai agent invoke --local "test message"

# 4. デプロイ（インフラ構築 + コンテナビルド + エージェント公開）
azd up

# 5. 確認
azd ai agent show
azd ai agent invoke "test message"
```

#### 方法 2: Python SDK

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    HostedAgentDefinition,
    ProtocolVersionRecord,
    AgentProtocol,
)
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint="https://<account>.services.ai.azure.com/api/projects/<project>",
    credential=DefaultAzureCredential(),
    allow_preview=True,
)

# Docker イメージを ACR にプッシュ済みが前提
agent = project.agents.create_version(
    agent_name="my-maf-agent",
    definition=HostedAgentDefinition(
        container_protocol_versions=[
            ProtocolVersionRecord(protocol=AgentProtocol.RESPONSES, version="v1")
        ],
        cpu="1",
        memory="2Gi",
        image="myregistry.azurecr.io/my-agent:v1",
        environment_variables={
            "AZURE_AI_PROJECT_ENDPOINT": PROJECT_ENDPOINT,
            "MODEL_NAME": "gpt-4o-mini",
        },
        tools=[
            {"type": "code_interpreter"},
        ],
    ),
)
```

#### 方法 3: VS Code 拡張

1. Command Palette → **Microsoft Foundry: Create new Hosted Agent**
2. テンプレート選択（Single Agent / Multi-Agent Workflow）
3. 言語選択（Python / C#）
4. モデル選択
5. F5 でローカルテスト
6. Command Palette → **Microsoft Foundry: Deploy Hosted Agent**

### MAF Agent を Hosted Agent としてデプロイする際の要件

1. **Responses API 互換**: `http://localhost:8088/responses` エンドポイントを公開
2. **Dockerfile**: コンテナイメージのビルド定義
3. **agent.yaml**: `template.kind: hosted` + プロトコル宣言
4. **ACR**: Azure Container Registry にイメージをプッシュ
5. **Capability Host**: Foundry アカウントに CapabilityHost 作成（`enablePublicHostingEnvironment: true`）

### Self-hosted MAF と Hosted Agent の連携パターン

```
┌─────────────────────────────────────────┐
│  Foundry Agent Service                  │
│  ┌────────────────────────────────────┐ │
│  │ Hosted Agent (MAF on container)   │ │
│  │  - Responses API 公開             │ │
│  │  - Foundry Tools 利用可           │ │
│  │  - マネージド ID 認証             │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │ Prompt Agent (構成のみ)           │ │
│  │  - OpenAPI Tool 経由で            │ │
│  │    Self-hosted MAF を呼び出し可   │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
          ↕ A2A / REST
┌─────────────────────────────────────────┐
│  Self-hosted MAF Agent                  │
│  (App Service / ACA / VM)               │
│  - 完全制御                             │
│  - VNet 統合                            │
│  - 独自ストレージ                       │
└─────────────────────────────────────────┘
```

---

## Sources

- [What is Microsoft Foundry Agent Service?](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [Create and manage Foundry agents in VS Code (classic)](https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/develop/vs-code-agents)
- [Deploy a hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Hosted agents concepts](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents)
- [azd AI agent extension](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension)
- [Foundry Project REST API](https://learn.microsoft.com/en-us/rest/api/aifoundry/aiproject)
- [Quickstart: Deploy your first hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [MAF Agent Types](https://learn.microsoft.com/en-us/agent-framework/agents/)
- [MAF / Foundry SDK Alignment spec](https://github.com/microsoft/agent-framework/blob/main/docs/specs/001-foundry-sdk-alignment.md)
- [microsoft-foundry/foundry-samples](https://github.com/microsoft-foundry/foundry-samples)
- [microsoft/agent-framework](https://github.com/microsoft/agent-framework)
