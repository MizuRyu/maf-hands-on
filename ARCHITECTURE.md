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
│  ├─ agents/               # Agent 単体の実験
│  ├─ workflows/            # Workflow 単体の実験
│  ├─ tools/                # Tool / ContextProvider の試験
│  ├─ context_providers/
│  ├─ middleware/
│  ├─ memory_state/
│  ├─ evaluation/
│  └─ observability/
│
└─ platform/                # エージェントプラットフォーム本体
   ├─ domain/               # コアモデル
   │  ├─ specs/             # AgentSpec, WorkflowSpec, ToolSpec
   │  ├─ runs/              # RunRecord, RunStatus, RunResult
   │  ├─ common/            # SpecId, RunId 等の共通型
   │  └─ repository/        # リポジトリ ABC: SpecRepository, RunRepository
   │
   ├─ application/          # サービス層（ユースケース）
   │  ├─ spec_management/   # 仕様の登録・更新・一覧・取得
   │  └─ run_management/    # 実行の開始・停止・状態取得
   │
   ├─ infrastructure/       # 外部技術アダプター
   │  ├─ maf/               # MAF Runner / Factory
   │  ├─ db/                # DB 永続化
   │  │  └─ cosmos/
   │  ├─ observability/     # OpenTelemetry 連携
   │  │  └─ otel/
   │  └─ settings/          # 設定・初期化
   │
   ├─ api/                  # HTTP 入口
   │  ├─ routers/           # エンドポイント
   │  ├─ schemas/           # リクエスト / レスポンス DTO
   │  └─ deps/              # DI 設定
   │
   ├─ catalog/              # 共通資産（複数 usecase で再利用）
   │  ├─ agents/
   │  ├─ workflows/
   │  ├─ tools/
   │  ├─ prompts/
   │  └─ context_providers/
   │
   └─ usecases/             # 業務フロー別の実装
      ├─ customer_support/  # 例: 顧客対応フロー
      └─ example_flow/      # 例: サンプルフロー

tests/                      # テスト（src のミラー構造）
docs/
  adr/                      # アーキテクチャ意思決定記録
deployment/                 # Dockerfile, entrypoint
```

## アーキテクチャパターン

**レイヤードアーキテクチャ**

- 基本はレイヤード（domain / application / infrastructure / api）
- MAF はプラットフォームの中核。全層で利用可能
- Cosmos DB / OpenTelemetry への依存は infrastructure 層に集約

## 依存方向ルール

```
api/
  ↓ calls
application/ (= service 層)
  ↓ calls
usecases/, catalog/, infrastructure/
  ↓ uses MAF directly / persists state
agent_framework SDK, Cosmos DB, OpenTelemetry
```

### 許可・禁止ルール

| ルール | 許可/禁止 |
|--------|-----------|
| domain → `agent_framework` | ✅ 許可 |
| domain → `azure.cosmos`, `opentelemetry` | ❌ 禁止（infrastructure 層の責務） |
| playground → platform | ✅ 許可 |
| platform → playground | ❌ 禁止 |
| catalog → usecases | ❌ 禁止 |
| usecases 間の横断参照 | ❌ 禁止 |

## リクエストフロー

### ワークフロー実行

```
POST /workflows/customer_support/run
  → api/routers/workflows.py          # バリデーション
  → application/run_management/        # RunRecord 作成、Workflow 実行を調停
  → infrastructure/maf/maf_runner.py   # MAF Workflow 実行
  → usecases/customer_support/         # MAF Workflow/Agent 定義
```

### 仕様登録

```
POST /specs
  → api/routers/specs.py              # DTO → AgentSpec 変換
  → application/spec_management/      # バリデーション、重複チェック
  → domain/repository/                # SpecRepository 経由
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
