# Microsoft Foundry + MAF: エンタープライズ認証・認可・セキュリティ調査

**調査日:** 2026-04-10

---

## 概要

Azure AI Foundry（旧 Azure AI Studio）と Microsoft Agent Framework (MAF) のエンタープライズ利用における認証・認可・セキュリティ機能を調査。Foundry はプラットフォーム側のセキュリティ基盤を、MAF はアプリケーション側のミドルウェアベースの制御を提供し、両者の組み合わせでエンタープライズ要件を満たす構成となる。

---

## 1. Azure AI Foundry のエージェント認証・認可

### 1.1 認証方式: Entra ID vs API キー

Foundry は **Microsoft Entra ID**（旧 Azure AD）と **API キー** の2方式をサポート。

| 項目 | Entra ID | API キー |
|------|----------|---------|
| **推奨用途** | 本番ワークロード | プロトタイプ・テスト |
| **ユーザー識別** | トークンに tenant/object ID 含む | 不可（誰が呼んだか追跡できない） |
| **RBAC** | きめ細かいロール割り当て可 | リソース単位の全 or 無 |
| **条件付きアクセス** | MFA・JIT アクセス対応 | 非対応 |
| **マネージド ID** | 対応（シークレットレス） | 非対応 |
| **即時失効** | ロール削除/プリンシパル無効化 | キーローテーション必要 |
| **監査** | プリンシパルごとの追跡可 | 困難 |

**重要:** Agent Service は **Entra ID のみ対応**（API キー不可）。Evaluations も同様。

ref: [Authentication and authorization in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/authentication-authorization-foundry)

### 1.2 機能別認証サポートマトリクス

| 機能 | API キー | Entra ID | 備考 |
|------|---------|---------|------|
| モデル推論（chat, embeddings） | Yes | Yes | |
| ファインチューニング | Yes | Yes | Entra ID でプリンシパル監査可 |
| **Agent Service** | **No** | **Yes** | Entra ID 必須 |
| **Evaluations** | **No** | **Yes** | Entra ID 必須 |
| Content Safety | Yes | Yes | RBAC で高リスク操作制限推奨 |
| Playground | Yes | Yes | |
| Private Link | Yes | Yes | Entra ID で条件付きアクセス追加 |

### 1.3 RBAC（ロールベースアクセス制御）

Foundry は **リソーススコープ** と **プロジェクトスコープ** の2階層で RBAC を適用。

#### 組み込みロール

| ロール | プロジェクト作成 | アカウント作成 | データアクション（ビルド） | ロール割り当て | モデル管理 |
|--------|:---:|:---:|:---:|:---:|:---:|
| **Azure AI User** | - | - | ✔ | - | - |
| **Azure AI Project Manager** | - | - | ✔ | ✔（AI User のみ） | - |
| **Azure AI Account Owner** | ✔ | ✔ | - | ✔（AI User のみ） | ✔ |
| **Azure AI Owner** | ✔ | ✔ | ✔ | ✔ | ✔ |

#### エンタープライズ RBAC マッピング例

| ペルソナ | ロール / スコープ | 目的 |
|---------|------------------|------|
| IT 管理者 | Owner @ サブスクリプション | 基盤管理、Manager へのロール委任 |
| マネージャー | AI Account Owner @ Foundry リソース | モデルデプロイ、接続管理、AI User の割り当て |
| チームリード | AI Project Manager @ Foundry リソース | プロジェクト作成、メンバー招待 |
| 開発者 | AI User @ プロジェクト + Reader @ リソース | エージェント開発・テスト |

#### カスタムロール

組み込みロールで不足する場合、カスタムロールを定義可能:

```json
{
  "roleName": "My Enterprise Foundry User",
  "permissions": [{
    "actions": ["Microsoft.CognitiveServices/*/read"],
    "dataActions": ["Microsoft.CognitiveServices/accounts/AIServices/agents/*"]
  }]
}
```

ref: [Role-based access control for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)

### 1.4 エージェント ID（Agent Identity）

Foundry は **Microsoft Entra ID に「エージェント ID」** という専用 ID タイプを導入。AI エージェント専用のサービスプリンシパル。

#### 仕組み

```
Agent Service
  → Blueprint 認証（マネージド ID → Entra ID）
    → Agent Identity トークン発行
      → スコープ付きトークン要求（対象リソースの audience）
        → 認証済みツール呼び出し
```

4段階の OAuth 2.0 トークン交換が自動実行される。開発者がトークンを直接管理する必要はない。

#### 2つの認証シナリオ

| シナリオ | フロー | 説明 |
|---------|-------|------|
| **Attended（委任）** | OBO (On-Behalf-Of) | ユーザーの代理で動作。ユーザーが同意・認可した範囲のみアクセス |
| **Unattended（アプリ専用）** | Client Credentials | エージェント自身の権限で動作。RBAC ロール割り当てで制御 |

#### 共有 ID vs 個別 ID

| 段階 | ID タイプ | 用途 |
|------|---------|------|
| 開発中（未公開） | **共有プロジェクト ID** | プロジェクト内の全エージェントが共通 ID を使用 |
| 公開後 | **個別エージェント ID** | エージェントごとに専用 ID。独立監査・権限管理 |

**公開時に ID が変わるため、RBAC ロール割り当ての再設定が必要。**

#### セキュリティ上の利点

- 人間/ワークロード ID とエージェントの操作を区別可能
- 最小権限アクセスの実現
- 大量エージェントの ID ライフサイクル管理
- Entra 管理センターで全テナントのエージェント ID 一覧管理可

ref: [Agent identity concepts in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity)

### 1.5 マルチテナント対応

- Entra ID のテナント分離がベース
- 各テナントの Foundry リソースは独立
- Agent Identity はテナント内のサービスプリンシパル
- Entra 管理センターでテナント横断のエージェント棚卸し可能
- 条件付きアクセスポリシーをエージェント ID に適用可能

---

## 2. MAF 側のセキュリティ機能

### 2.1 Agent / Workflow 実行時の認証フロー

MAF は以下の認証方式をサポート:

#### API キー認証（FastAPI エンドポイント）

```python
# FastAPI の dependency injection でエージェントエンドポイントに API キー認証を適用
add_agent_framework_fastapi_endpoint(
    app,
    agent,
    dependencies=[verify_api_key]
)
```

#### OAuth 2.0 / OpenID Connect

.NET では JWT Bearer トークン検証による OAuth 2.0 スコープベース認可:

- OIDC プロバイダーに対するトークン検証
- ツールごとのアクセス制御（認証済みユーザーの権限に基づく）

#### Foundry 接続時の認証

```python
from azure.identity import DefaultAzureCredential  # 開発時
from azure.identity import ManagedIdentityCredential  # 本番推奨
```

### 2.2 Session のユーザー紐付け

MAF の Purview 統合で `user_id` を使ったセッション管理:

- `Message.additional_properties` に `user_id` を設定
- Purview ポリシー評価がプロンプト・レスポンス間で同一ユーザーに一貫適用
- `user_id` 未設定時はポリシー評価がスキップされる
- `session_id` は `AgentContext.session.service_session_id` または `conversation_id` から解決

### 2.3 Tool 実行時の権限制御

#### Human-in-the-Loop 承認

```python
# ツールに承認モードを設定
agent = Agent(
    tools=[my_tool],
    approval_mode="always_require"  # or "never_require" or {tool: mode}
)
```

#### Permission Handler

`GitHubCopilotAgent` や `ClaudeAgent` 等で利用:

- シェルコマンド実行、ファイル読み書き、MCP ツール使用前にユーザー承認を要求
- `PermissionRequestResult` で `approved` / `denied-interactively-by-user` を返却

### 2.4 MCP ツールのセキュリティ

| 方式 | 説明 |
|------|------|
| **OAuth 2.0 認証** | ブラウザベース認証でアクセストークン取得。MCP サーバーとのセキュア通信 |
| **API キー認証** | 実行時に `function_invocation_kwargs` で渡す。共有クライアントへの焼き込み防止 |
| **Agent Identity 認証** | Foundry の Agent Identity トークンで MCP サーバーに認証（プレビュー） |
| **approval_mode** | `always_require` / `never_require` でツールごとに承認制御 |
| **allowed_tools** | MCP サーバーから使用可能なツールを制限 |

**信頼できる MCP サーバーのみ使用すること。** Permission Handler で許可アクションを制御。

ref: Foundry 側 MCP 認証設定は connection の `AuthType` で `AgenticIdentityToken` を指定。

### 2.5 ミドルウェアによるカスタムセキュリティ

MAF はミドルウェアパイプラインで拡張可能:

```python
# カスタムセキュリティミドルウェアの例
class SecurityAgentMiddleware(AgentMiddleware):
    async def invoke(self, context, call_next):
        query = context.messages[-1].content.lower()
        if any(word in query for word in ["password", "secret"]):
            context.result = "Blocked: sensitive keyword detected"
            return  # call_next() を呼ばない → 後続処理停止
        await call_next(context)

agent = Agent(
    middleware=[SecurityAgentMiddleware(), LoggingFunctionMiddleware()],
    ...
)
```

- エージェントレベル（全実行に適用）またはランレベル（特定の `agent.run()` のみ）で登録可能
- `MiddlewareTermination` 例外でパイプラインを停止可能

---

## 3. エンタープライズ要件

### 3.1 監査ログ

#### Foundry レベル

- **Microsoft Purview Audit**: プロンプト・レスポンスが統合監査ログに記録
  - いつ・誰が・どのサービスで AI アプリと対話したか
  - アクセスしたファイルの秘密度ラベル情報も含む
- **DSPM for AI**: Data Security Posture Management のアクティビティエクスプローラーで分類・分析
- **OpenTelemetry**: MAF は分散トレーシングを標準サポート
  - ツール呼び出し、オーケストレーションステップ、推論フロー、パフォーマンスを追跡

#### MAF レベル

- **Purview ミドルウェア**: `PurviewPolicyMiddleware` / `PurviewChatPolicyMiddleware`
  - Pre-check（プロンプト）: `UPLOAD_TEXT` アクティビティとして評価
  - Post-check（レスポンス）: `DOWNLOAD_TEXT` アクティビティとして評価
  - ポリシー違反時はブロックメッセージで置換
  - ストリーミングレスポンスの Post-check は現時点で未サポート
- **カスタムロギング**: `LoggingFunctionMiddleware` 等でツール呼び出しを記録可能

#### エージェント可観測性（組織レベル）

- **Microsoft Agent 365**: 組織横断のエージェント監視ツール
- **Entra Agent Identity**: 全エージェントにユニーク ID を割り当て、棚卸し・監査
- **集中ログ**: Azure Log Analytics ワークスペースへの一元化推奨
- **コスト追跡**: トークン消費、コンピュート使用量をタグ付きで追跡

### 3.2 データ分離

#### ネットワーク分離

| 構成 | 説明 |
|------|------|
| **Standard + Private Networking** | BYO VNet。パブリック送信なし。サブネット注入でローカル通信 |
| **マネージド VNet** | Foundry 管理の VNet。Allow Internet Outbound / Allow Only Approved Outbound |
| **Private Endpoints** | Foundry, AI Search, Storage, Cosmos DB, Key Vault 等に対応 |
| **DNS ゾーン** | privatelink.*.windows.net / *.azure.com 等の自動構成 |

#### BYO リソース

以下を自前リソースとして持ち込み可能（データの物理的分離）:

- Azure Storage（ファイル/アーティファクト）
- Azure AI Search（ベクトル検索）
- Azure Cosmos DB（会話状態の永続化）
- Azure Key Vault（シークレット管理）

#### テナント間分離

- 各テナントは独立した Foundry リソース + Entra ID テナント
- データはテナント指定の地理的リージョンに保存
- Private Link / VNet でネットワークレベルの分離

### 3.3 コンプライアンス

#### データ所在地（Data Residency）

| デプロイタイプ | データ処理場所 |
|--------------|-------------|
| **Standard** | 指定リージョン内 |
| **DataZone** | 指定データゾーン内（例: EU 加盟国間） |
| **Global** | モデルがデプロイされた任意の地理（保存データは指定リージョン） |

- 保存データ（at rest）は常に顧客指定の地理に存在
- 推論処理のみがデプロイタイプに応じて地理をまたぐ可能性あり
- 転送中・保存中の暗号化は全デプロイタイプで適用

#### 規制準拠

- **Azure コンプライアンス認証**: ISO/IEC 27001, SOC 1/2/3, GDPR 等
- **Microsoft Purview Compliance Manager**: EU AI Act 等の規制をコントロールに変換
- **Purview API**: コンプライアンス自動化をエージェントワークフローに統合
- **データ保持ポリシー**: ログ・メモリ・学習データの保持期間を定義可能
- **Azure OpenAI**: 入出力をモデル学習に使用しない（プライバシー保証）

#### Purview 統合で利用可能な機能

1. Purview Audit（監査）
2. 機密情報タイプ（SIT）分類
3. DSPM for AI（分析・レポート）
4. Insider Risk Management
5. Communication Compliance
6. Data Lifecycle Management
7. eDiscovery

### 3.4 Responsible AI

#### コンテンツフィルタリング

全 Azure OpenAI モデルにデフォルトの安全設定が適用:

| 重大度 | プロンプト構成可 | 補完構成可 | 説明 |
|--------|:---:|:---:|------|
| Low, Medium, High | Yes | Yes | 最も厳格 |
| Medium, High | Yes | Yes | Low は通過 |
| High のみ | Yes | Yes | Low/Medium は通過 |
| フィルタなし | 承認要^1^ | 承認要^1^ | 全通過 |
| アノテーションのみ | 承認要^1^ | アノテーションは返すがブロックしない |

^1^ Modified Content Filter の申請・承認が必要

#### カテゴリ

- 暴力、ヘイト、性的コンテンツ、自傷行為
- カスタムカテゴリの定義可能（Content Safety API）
- ブロックリストによる追加フィルタ

#### Guardrails（ガードレール）

- プロンプトインジェクション対策（XPIA: Cross-Prompt Injection Attack 含む）
- Foundry Agent Service に統合済み

#### Responsible AI フレームワーク

Microsoft の RAI Standard に基づく3段階アプローチ:

1. **Discover**: デプロイ前後の品質・安全性・セキュリティリスクの発見（敵対的プロンプトテスト等）
2. **Protect**: モデル出力・エージェントランタイムレベルでの保護（コンテンツフィルタ、ガードレール）
3. **Govern**: トレーシング・モニタリングツールとコンプライアンス統合による継続的監視

#### Risks & Safety モニタリング

Azure AI Foundry でモデルデプロイメントごとにダッシュボードを提供:

- コンテンツフィルタの動作結果を可視化
- Azure Monitor との連携

ref: [Responsible AI for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/responsible-use-of-ai-overview)

---

## 4. Foundry + MAF の連携パターン

### 4.1 Hosted Agent vs Self-hosted Agent

| 項目 | Hosted Agent | Self-hosted Agent |
|------|-------------|-------------------|
| **デプロイ先** | Azure AI Foundry（マネージド） | Azure Functions, ASP.NET Core, コンソールアプリ等 |
| **定義ファイル** | `Dockerfile` + `agent.yaml` (`kind: hosted`) | アプリコード + DI 構成 |
| **ID 管理** | Foundry が自動プロビジョニング | 自前で Entra ID / API キー管理 |
| **スケーリング** | Foundry 管理 | 自前でインフラ管理 |
| **ネットワーク分離** | Foundry の VNet 統合 | 自前で VNet / NSG 構成 |
| **適用シナリオ** | マネージド運用、迅速なデプロイ | カスタム要件、既存インフラ活用 |

### 4.2 Foundry がカバーする範囲 vs 自前実装

| 領域 | Foundry が提供 | 自前で実装が必要 |
|------|--------------|----------------|
| **認証基盤** | Entra ID 統合、Agent Identity、RBAC | アプリ層の認証フロー（OAuth redirect 等） |
| **コンテンツ安全性** | Content Filter、Guardrails、XPIA 対策 | ドメイン固有のフィルタリングルール |
| **監査** | Purview Audit、DSPM for AI | アプリ固有のビジネスログ |
| **ネットワーク** | Private Link、VNet 注入、DNS | オンプレミス接続（VPN/ExpressRoute） |
| **モデル管理** | デプロイ、バージョニング、クォータ | プロンプトエンジニアリング、評価基準 |
| **ツール認証** | Agent Identity → MCP/A2A トークン交換 | 外部 API の認証設定（コネクション作成） |
| **状態管理** | BYO Cosmos DB for 会話状態 | ビジネスロジックの状態管理 |
| **データ分類** | Purview SIT 分類、ラベル | ドメイン固有の機密データ定義 |

### 4.3 エージェント登録・デプロイのライフサイクル

```
1. 開発
   └─ プロジェクト内で共有 Agent Identity を使用
   └─ MAF の Agent / Workflow をローカル開発・テスト

2. 登録（Hosted Agent）
   └─ agent.yaml + Dockerfile を用意
   └─ AIProjectClient.CreateAIAgentAsync() でエージェント作成
   └─ モデル、instructions、ツールを指定

3. バージョニング
   └─ AIProjectClient.Agents.CreateAgentVersionAsync() で新バージョン
   └─ サーバーサイドでバージョン管理

4. 公開
   └─ 個別 Agent Identity が自動作成
   └─ RBAC ロールを新 ID に再割り当て
   └─ MCP/A2A の接続設定を更新

5. 運用
   └─ Purview で監査・コンプライアンス監視
   └─ Risks & Safety ダッシュボードで安全性モニタリング
   └─ OpenTelemetry で分散トレーシング

6. 削除
   └─ AIProjectClient.Agents.DeleteAgentAsync() でクリーンアップ
   └─ Agent Identity も連動して削除
```

### 4.4 Self-hosted Agent のデプロイパターン

```python
# Python: Azure Functions でホスト
from agent_framework import AgentFunctionApp

app = AgentFunctionApp(agent=my_agent)
# HTTP エンドポイントが Durable Functions 経由で自動生成
```

```csharp
// .NET: Azure Functions でホスト
builder.ConfigureDurableAgents(agent => {
    agent.AddAIAgent<MyAgent>();
});
// HTTP API エンドポイントが自動生成
```

### 4.5 マルチエージェントワークフローでの Foundry 連携

```python
# Writer-Reviewer パターン（両方 Foundry Agent）
from agent_framework.foundry import FoundryAgent
from agent_framework import WorkflowBuilder

writer = FoundryAgent(name="writer", project_client=client)
reviewer = FoundryAgent(name="reviewer", project_client=client)

workflow = WorkflowBuilder() \
    .add_agent(writer) \
    .add_agent(reviewer) \
    .build()
```

---

## 5. まとめ: エンタープライズ導入チェックリスト

### 必須

- [ ] Entra ID 認証の有効化（API キーは開発のみ）
- [ ] RBAC ロール設計（最小権限の原則）
- [ ] Agent Identity の理解と管理計画
- [ ] コンテンツフィルタの構成
- [ ] Purview 統合の有効化（監査要件がある場合）

### 推奨

- [ ] Private Networking の構成（VNet / Private Endpoint）
- [ ] BYO リソースの検討（Storage, Cosmos DB, AI Search）
- [ ] OpenTelemetry によるトレーシング設定
- [ ] MAF ミドルウェアによるカスタムセキュリティポリシー
- [ ] MCP ツールの信頼性評価と approval_mode 設定

### 検討事項

- [ ] データ所在地要件の確認（Standard vs DataZone vs Global デプロイ）
- [ ] Hosted vs Self-hosted の選定
- [ ] マルチテナント構成の設計
- [ ] エージェント公開時の ID 移行手順

---

## Sources

- [Authentication and authorization in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/authentication-authorization-foundry)
- [Role-based access control for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)
- [Agent identity concepts in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity)
- [Responsible AI for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/responsible-use-of-ai-overview)
- [What is Microsoft Foundry Agent Service?](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Set up private networking for Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/virtual-networks)
- [Manage compliance and security in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/control-plane/how-to-manage-compliance-security)
- [Content filter configurability](https://learn.microsoft.com/azure/ai-foundry/openai/concepts/content-filter-configurability)
- [Governance and security for AI agents across the organization](https://learn.microsoft.com/azure/cloud-adoption-framework/ai-agents/governance-security-across-organization)
- [Use Microsoft Purview for Microsoft Foundry](https://learn.microsoft.com/purview/ai-azure-foundry)
- [Microsoft Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Microsoft Agent Framework 1.0 Blog](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)
- [DeepWiki: microsoft/agent-framework](https://deepwiki.com/microsoft/agent-framework)
