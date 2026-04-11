# アーキテクチャ

MAF (Microsoft Agent Framework) 1.0.0 を使ったエージェント管理プラットフォーム。

## 技術スタック

| 要素 | 技術 |
|------|------|
| 言語 | Python 3.12+ |
| フレームワーク | Microsoft Agent Framework (MAF) 1.0.0 |
| パッケージ管理 | uv |
| DB | Azure Cosmos DB (`agent-framework-azure-cosmos`) |
| 可観測性 | OpenTelemetry (OTLP/gRPC) → Aspire Dashboard |
| API | FastAPI |
| コンテナ | Docker Compose |
| Linter/Formatter | ruff |
| 型チェック | pyright (basic) |
| テスト | pytest + pytest-asyncio |

## ディレクトリ構成

```
src/
├─ playground/              # MAF 機能検証の場
│
└─ platform/                # エージェントプラットフォーム本体
   ├─ agents/               # Agent 構築基盤 + テンプレート
   │  ├─ builder.py         # PlatformAgentBuilder
   │  ├─ policy.py          # PlatformPolicy (YAML 駆動)
   │  ├─ middleware/        # 共通 Middleware (Audit, Security)
   │  ├─ _types.py          # AgentMeta
   │  └─ text_analyzer/     # Agent テンプレート例
   │
   ├─ workflows/            # Workflow 定義
   │  ├─ _types.py          # WorkflowMeta
   │  └─ text_pipeline/     # Workflow テンプレート例
   │
   ├─ tools/                # プラットフォーム共有 Tool
   │
   ├─ domain/               # コアモデル（各 context に models/ + repositories/）
   │  ├─ registry/          # AgentSpec, ToolSpec, WorkflowSpec
   │  ├─ execution/         # WorkflowExecution, WorkflowExecutionStep
   │  ├─ sessions/          # Session
   │  ├─ users/             # User
   │  └─ common/            # 型定義, 列挙型, ドメイン例外
   │
   ├─ application/          # ユースケース（Phase 1 で実装）
   │
   ├─ infrastructure/       # 外部技術アダプター
   │  ├─ db/cosmos/         # Cosmos DB 永続化
   │  ├─ observability/     # OpenTelemetry
   │  └─ settings/          # Pydantic BaseSettings
   │
   └─ api/                  # HTTP 入口 (FastAPI)

tests/                      # テスト（src のミラー構造）
docs/adr/                   # アーキテクチャ意思決定記録
```

## アーキテクチャパターン

**レイヤードアーキテクチャ**

- 基本はレイヤード（domain / application / infrastructure / api）
- MAF はプラットフォームの中核。全層で利用可能
- Cosmos DB / OpenTelemetry への依存は infrastructure 層に集約

## 依存方向ルール

```
api/
  ↓
application/
  ↓
agents/, workflows/, domain/, infrastructure/
  ↓
agent_framework SDK, Cosmos DB, OpenTelemetry
```

### 許可・禁止ルール

| ルール | 許可/禁止 |
|--------|-----------|
| domain → `agent_framework` | ✅ 許可 |
| domain → `azure.cosmos`, `opentelemetry` | ❌ 禁止 |
| agents/, workflows/ → `agent_framework` | ✅ 許可 |
| agents/, workflows/ → `infrastructure/` | ❌ 禁止 |
| playground → platform | ✅ 許可 |
| platform → playground | ❌ 禁止 |

## リクエストフロー（Phase 1 以降）

### Agent 登録

```
POST /agents
  → api/routers/agents.py             # バリデーション
  → application/register_agent.py     # AgentMeta → AgentSpec 変換
  → domain/registry/repositories/     # AgentSpecRepository 経由
  → infrastructure/db/cosmos/         # Cosmos DB 保存
```

## ローカル開発環境

| サービス | ポート | 用途 |
|---------|--------|------|
| backend | 8000 | アプリケーション |
| cosmos | 8081 | Cosmos DB エミュレータ |
| aspire-dashboard | 18888 | OTel トレース可視化 |

```bash
make up      # 全サービス起動
make down    # 全サービス停止
make rebuild # キャッシュなしリビルド
```
