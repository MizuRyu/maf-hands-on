# API 設計

**作成日**: 2026-04-12
**方式**: REST API (JSON over HTTP)
**ベース**: FastAPI (`src/platform/api/`)

---

## 1. 共通仕様

### 1.1 ベースパス

```
/api
```

### 1.2 レスポンス形式

全 API で統一する。JSON キーは snake_case。

```json
// 正常 (単体)
{
  "code": 200,
  "data": { ... }
}

// 正常 (一覧)
{
  "code": 200,
  "data": [ ... ]
}

// 正常 (返却データなし)
{
  "code": 200
}

// エラー
{
  "code": 400,
  "detail": "リクエストパラメータが不正です",
  "error_type": "validation"
}
```

### 1.3 HTTP ステータスコード

| コード | 用途 |
|--------|------|
| 200 OK | 正常 |
| 201 Created | リソース作成 |
| 202 Accepted | 非同期処理開始 (run 系)。以降はポーリングで状態取得 |
| 204 No Content | 削除成功 |
| 400 Bad Request | リクエスト形式不正 |
| 404 Not Found | リソースなし |
| 409 Conflict | ステータス競合 |
| 422 Unprocessable Entity | バリデーションエラー |
| 500 Internal Server Error | サーバー内部エラー |

### 1.4 バリデーション方針

2 段階で行う。

| レベル | タイミング | 対象 | レスポンス |
|--------|-----------|------|-----------|
| **入力検証** | 全 POST/PATCH | 型、必須フィールド、フォーマット | 422 Unprocessable Entity |
| **ビジネス検証** | `/validate` エンドポイント | tool 存在、middleware 互換性、Foundry 要件 | 200 + `valid: false` |

入力検証は各エンドポイントが自動で行う（FastAPI Pydantic）。
ビジネス検証は activate 前に明示的に呼ぶ。

### 1.5 CQRS

取得系と更新系で経路を分離する。

- **Query (GET)**: Router → Repository 直読み
- **Command (POST/PATCH/DELETE)**: Router → Application Service → Repository

### 1.6 認証

MVP は無し。後で Entra ID Bearer token。

---

## 2. Platform Options

UI の dropdown / toggle の選択肢を返す。

```
GET /api/platform/options
```

```json
{
  "code": 200,
  "data": {
    "models": ["gpt-5-nano"],
    "tool_types": ["function", "mcp", "agent_as_tool", "hosted"],
    "middleware": ["audit", "security"],
    "features": {
      "history": { "default": true },
      "compaction": { "default": true },
      "tools": { "default": true },
      "structured_output": { "default": false }
    },
    "compaction_strategies": ["sliding_window", "token_budget", "summarization"],
    "foundry": {
      "deployment_types": ["prompt", "hosted", "workflow", "none"]
    }
  }
}
```

---

## 3. Agent API

Domain model: `AgentSpec`

### 3.1 Spec 管理

```
GET    /api/agents                              # 一覧 (Query)
GET    /api/agents/{agent_id}                   # 詳細 (Query)
POST   /api/agents                              # 新規作成 (Command)
PATCH  /api/agents/{agent_id}                   # 編集 (Command)
POST   /api/agents/{agent_id}/activate          # draft -> active (Command)
POST   /api/agents/{agent_id}/archive           # -> archived (Command)
POST   /api/agents/{agent_id}/validate          # ビジネス検証 (Query)
POST   /api/agents/{agent_id}/foundry-sync      # Foundry 同期 (Command)
```

#### POST /api/agents

```json
{
  "name": "expense-checker",
  "description": "経費ポリシーチェック",
  "model_id": "gpt-5-nano",
  "instructions": "あなたは経費精算の確認エージェントです。",
  "tool_ids": ["tool_check_expense_policy"],
  "middleware_config": [],
  "context_provider_config": [],
  "response_format": null,
  "foundry_deployment_type": "none"
}
```

#### POST /api/agents/{agent_id}/validate

```json
{
  "code": 200,
  "data": {
    "valid": false,
    "errors": [
      { "field": "instructions", "message": "instructions が空です" }
    ],
    "warnings": [
      { "field": "tool_ids", "message": "tool_xxx は archived 状態です" }
    ]
  }
}
```

### 3.2 Session（Agent との会話）

Agent の実行は Session ベース。Session を作成し、メッセージを送信することで Agent が実行される。
会話履歴は MAF `CosmosHistoryProvider` が `messages` コンテナに自動保存する。

```
POST   /api/sessions                                    # セッション作成 (Command)
GET    /api/sessions                                    # セッション一覧 (Query)
GET    /api/sessions/{session_id}                       # セッション詳細 (Query)
POST   /api/sessions/{session_id}/messages              # メッセージ送信 = Agent 実行 (Command, 同期)
GET    /api/sessions/{session_id}/messages              # 会話履歴取得 (Query)
PATCH  /api/sessions/{session_id}                       # タイトル変更等 (Command)
DELETE /api/sessions/{session_id}                       # セッション終了 (Command)
```

Domain model: `Session`（Cosmos `sessions` コンテナ）+ MAF `CosmosHistoryProvider`（`messages` コンテナ）

#### POST /api/sessions

```json
// リクエスト
{
  "agent_id": "agent_001",
  "title": "経費チェック"
}

// レスポンス (201 Created)
{
  "code": 201,
  "data": {
    "session_id": "session_abc",
    "agent_id": "agent_001",
    "status": "active",
    "title": "経費チェック",
    "created_at": "2026-04-12T10:00:00Z"
  }
}
```

#### POST /api/sessions/{session_id}/messages

```json
// リクエスト
{
  "input": "この経費精算書を確認してください"
}

// レスポンス (200 OK — Agent 実行結果を同期返却)
{
  "code": 200,
  "data": {
    "output": "この経費精算書は承認可能です。金額は上限以内です。",
    "trace_id": "trace_xyz"
  }
}
```

会話履歴は `GET /api/sessions/{session_id}/messages` で取得。MAF `CosmosHistoryProvider` が保存したメッセージを返す。

### 3.3 Agent 評価

評価は Agent に紐づく。

```
GET    /api/agents/{agent_id}/eval/datasets              # データセット一覧 (Query)
POST   /api/agents/{agent_id}/eval/datasets              # データセット作成 (Command)
GET    /api/agents/{agent_id}/eval/datasets/{dataset_id} # データセット詳細 (Query)
POST   /api/agents/{agent_id}/eval/datasets/{dataset_id}/cases  # ケース追加 (Command)
POST   /api/agents/{agent_id}/eval/runs                  # 評価実行 (Command)
GET    /api/agents/{agent_id}/eval/runs                  # 評価一覧 (Query)
GET    /api/agents/{agent_id}/eval/runs/{eval_run_id}    # 評価結果 (Query)
```

#### POST /api/agents/{agent_id}/eval/runs

```json
// リクエスト
{
  "dataset_id": "dataset_001",
  "evaluator_type": "local",
  "evaluators": ["relevance", "groundedness"]
}

// レスポンス (202 Accepted)
{
  "code": 202,
  "data": {
    "eval_run_id": "evalrun_abc",
    "status": "running",
    "target_agent_id": "agent_001",
    "dataset_id": "dataset_001"
  }
}
```

---

## 4. Tool API

Domain model: `ToolSpec`

ライフサイクルは `SpecStatus` (draft/active/archived) で管理する。

```
GET    /api/tools                               # 一覧 (Query)
GET    /api/tools/{tool_id}                     # 詳細 (Query)
POST   /api/tools                               # 新規登録 (Command)
PATCH  /api/tools/{tool_id}                     # 編集 (Command)
POST   /api/tools/{tool_id}/archive             # archived に変更 (Command)
POST   /api/tools/{tool_id}/run                 # 単体実行 (Command)
```

#### POST /api/tools/{tool_id}/run

```json
// リクエスト
{ "arguments": { "amount": 50000, "category": "travel" } }

// レスポンス
{
  "code": 200,
  "data": {
    "tool_run_id": "toolrun_abc123",
    "status": "succeeded",
    "trace_id": "trace_xyz",
    "output": { "approved": true, "reason": "金額が上限以内" },
    "duration_ms": 120
  }
}
```

---

## 5. Workflow API

Domain model: `WorkflowSpec`

### 5.1 Spec 管理

```
GET    /api/workflows                           # 一覧 (Query)
GET    /api/workflows/{workflow_id}             # 詳細 (Query)
POST   /api/workflows                           # 新規作成 (Command)
PATCH  /api/workflows/{workflow_id}             # 編集 (Command)
DELETE /api/workflows/{workflow_id}             # 削除 (Command)
POST   /api/workflows/{workflow_id}/validate    # ステップ整合性検証 (Query)
```

#### POST /api/workflows

```json
{
  "name": "approval-workflow",
  "description": "申請承認ワークフロー",
  "steps": {
    "validate": { "step_name": "入力検証", "step_type": "logic", "order": 1 },
    "classify": { "step_name": "分類", "step_type": "agent", "order": 2 },
    "approve":  { "step_name": "承認", "step_type": "human", "order": 3 },
    "notify":   { "step_name": "通知", "step_type": "logic", "order": 4 }
  }
}
```

### 5.2 Workflow Execution

状態取得はポーリング (`GET .../executions/{execution_id}`)。SSE は使わない。

```
POST   /api/workflows/{workflow_id}/executions                              # 実行開始 (Command)
GET    /api/workflows/{workflow_id}/executions                              # 実行一覧 (Query)
GET    /api/workflows/{workflow_id}/executions/{execution_id}               # 実行詳細 (Query, ポーリング)
GET    /api/workflows/{workflow_id}/executions/{execution_id}/steps         # ステップ一覧 (Query)
POST   /api/workflows/{workflow_id}/executions/{execution_id}/cancel        # キャンセル (Command)
POST   /api/workflows/{workflow_id}/executions/{execution_id}/resume        # チェックポイント再開 (Command)
POST   /api/workflows/{workflow_id}/executions/{execution_id}/input-response  # HITL 応答 (Command)
```

#### POST /api/workflows/{workflow_id}/executions

```json
// リクエスト
{
  "variables": { "request_id": "REQ-2026-001", "amount": 150000 },
  "user_id": "user_001"
}

// レスポンス (202 Accepted)
{
  "code": 202,
  "data": {
    "execution_id": "wfe_abc123",
    "status": "running",
    "workflow_name": "approval-workflow",
    "workflow_version": 1,
    "current_step_id": "validate",
    "started_at": "2026-04-12T10:00:00Z"
  }
}
```

#### GET .../executions/{execution_id}

```json
{
  "code": 200,
  "data": {
    "execution_id": "wfe_abc123",
    "status": "waiting",
    "workflow_name": "approval-workflow",
    "current_step_id": "approve",
    "latest_checkpoint_id": "cp_xyz",
    "steps": [
      { "step_id": "validate", "status": "completed", "duration_ms": 45 },
      { "step_id": "classify", "status": "completed", "duration_ms": 1200 },
      { "step_id": "approve", "status": "waiting", "assigned_to": "manager@example.com" },
      { "step_id": "notify", "status": "idle" }
    ],
    "started_at": "2026-04-12T10:00:00Z",
    "updated_at": "2026-04-12T10:00:05Z"
  }
}
```

#### POST .../executions/{execution_id}/input-response

```json
{
  "step_id": "approve",
  "action": "approve",
  "comment": "承認します"
}
```

---

## 6. Foundry Link API

```
GET    /api/foundry/status                      # Foundry 接続状態 (Query)
GET    /api/foundry/traces/{trace_id}/link       # Trace deep link 生成 (Query)
```

Foundry sync は各リソース API に含む (`POST /api/agents/{agent_id}/foundry-sync`)。

---

## 7. チェックポイント・リトライ

| ケース | リカバリ方法 |
|--------|-------------|
| Agent ステップ失敗 | 最新チェックポイントから再開、該当ステップ再実行 |
| サーバー障害 | 最新チェックポイントから再開 |
| HITL 待機中にセッション切断 | チェックポイントに待機状態保存、再開して応答待ち |

| 項目 | 値 |
|------|----|
| 最大リトライ | 3 回 |
| 戦略 | 指数バックオフ (初回 1s, 倍率 2, 上限 30s) + ジッター |
| 429 | Retry-After ヘッダ優先 |

---

## 8. API - Domain 対応表

| API | Domain Model | Command Service | Router |
|-----|-------------|-----------------|--------|
| `/api/agents` (spec) | `AgentSpec` | `AgentSpecService` | `routers/agents.py` |
| `/api/sessions` | `Session` | `SessionService` | `routers/sessions.py` |
| `/api/sessions/{id}/messages` | MAF `Message` | `SessionService` | `routers/sessions.py` |
| `/api/agents/{id}/eval` | eval domain (TBD) | `EvalService` | `routers/agents.py` |
| `/api/tools` | `ToolSpec` | `ToolSpecService` | `routers/tools.py` |
| `/api/workflows` (spec) | `WorkflowSpec` | `WorkflowSpecService` | `routers/workflows.py` |
| `/api/workflows/{id}/executions` | `WorkflowExecution` / `Step` | `WorkflowExecutionService` | `routers/executions.py` |
| `/api/platform/options` | `PlatformPolicy` | - (Query のみ) | `routers/platform.py` |
| `/api/foundry` | - | `FoundrySyncService` | `routers/foundry.py` |

Query (GET) は Router → Repository 直読み。表の Service は Command 用。

---

## 9. ファイル構成

```
src/platform/api/
  main.py
  routers/
    agents.py           # spec + eval
    sessions.py         # session + messages
    tools.py            # spec + run
    workflows.py        # spec
    executions.py       # workflow executions
    platform.py         # options
    foundry.py          # link / status
  schemas/
    agent.py            # *Request + *ResponseData
    tool.py
    workflow.py
    execution.py
    eval.py
    common.py           # API_PREFIX, BaseResponse, ErrorResponse
  deps/
    cosmos.py           # CosmosClient DI
    services.py         # Repository / Service DI
```

---

## 10. 実装しないもの

- Foundry trace viewer の再実装
- full prompt / response / tool args の自前永続化
- 独自 IAM / RBAC
- evaluator の全面自作
- Azure Monitor の代替 dashboard

---

## 11. 既知の設計課題

| # | 課題 | 対応方針 |
|---|------|---------|
| 1 | `WorkflowSpec` に `status` / `created_by` がない | AgentSpec / ToolSpec と揃える |
| 2 | ~~`AgentRun` の domain model~~ | 削除。Session + MAF HistoryProvider で代替 |
| 3 | eval domain のモデル | Phase 3 で `eval_datasets` / `eval_runs` コンテナ追加 |

**最終更新日**: 2026-04-12
