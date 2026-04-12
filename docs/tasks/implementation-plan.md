# 実装計画

**作成日**: 2026-04-12
**対象**: platform-design.md (v3) に基づく未実装機能の段階的実装

---

## 現状 (実装済み)

| レイヤー | 実装状況 |
|---------|---------|
| Domain models / repositories (ABC) | 完了 |
| Cosmos DB repositories (全コンテナ) | 完了 |
| PlatformAgentFactory + Policy + Middleware | 完了 |
| OTel setup | 完了 |
| Cosmos helpers / client / checkpoint | 完了 |
| text_analyzer (Template Agent サンプル) | 完了 |
| text_pipeline (Workflow サンプル) | 完了 |
| API skeleton (空 routers) | 完了 |
| Playground samples | 完了 |

---

## Phase 1: Config Agent 基盤 + Feature Flags

**目的**: YAML で Agent を宣言的に定義し、feature flags で振る舞いを制御する仕組み。

### 1.1 Config Agent YAML ローダー

- `src/platform/agents/config_loader.py` を新設
- `config/agents/*.yaml` を読み込み、PlatformAgentFactory 経由で Agent を生成
- YAML スキーマ: `name`, `version`, `model_id`, `instructions`, `tools`, `features`, `compaction`, `response_format`

```yaml
# config/agents/expense_checker.yaml
name: expense-checker
version: 1
model_id: gpt-4o
instructions: |
  あなたは経費精算の確認エージェントです。
  提出された経費明細を確認し、ポリシー違反がないかチェックしてください。
tools:
  - check_expense_policy
  - calculate_total
features:
  history: true
  compaction: true
  tools: true
  structured_output: false
compaction:
  strategy: sliding_window
  max_turns: 20
```

### 1.2 Feature Flags の builder 統合

- `PlatformAgentFactory.build()` に `features` パラメータ追加
- `tools: false` → tools=[] で Agent 生成
- `structured_output: true` → response_format を Agent に渡す
- `history: false` → HistoryProvider を注入しない (既存)
- `compaction: false` → CompactionProvider を注入しない

### 1.3 Compaction 戦略

- `src/platform/agents/compaction.py` を新設
- MAF の `CompactionProvider` を wrap し、strategy に応じた設定を注入
- 対応戦略: `sliding_window`, `token_budget`, `summarization`

### 1.4 サンプル Config Agent YAML

- `config/agents/expense_checker.yaml`
- `config/agents/document_classifier.yaml`
- `config/agents/faq_responder.yaml`

### 成果物

```
config/agents/
  expense_checker.yaml
  document_classifier.yaml
  faq_responder.yaml
src/platform/agents/
  config_loader.py
  compaction.py
```

---

## Phase 2: Application Layer + API

**目的**: ドメインモデルと infrastructure を繋ぐユースケース層と REST API。

### 2.1 spec_management ユースケース

- `src/platform/application/spec_management/agent_spec_service.py`
  - `register_agent(dto) -> AgentSpec`
  - `get_agent(spec_id) -> AgentSpec`
  - `list_agents(filters) -> list[AgentSpec]`
  - `update_agent(spec_id, dto) -> AgentSpec`
  - `archive_agent(spec_id) -> None`
- `workflow_spec_service.py`, `tool_spec_service.py` も同様

### 2.2 run_management ユースケース

- `src/platform/application/run_management/workflow_execution_service.py`
  - `start_execution(workflow_id, variables, user_id) -> WorkflowExecution`
  - `get_execution(execution_id) -> WorkflowExecution`
  - `list_executions(filters) -> list[WorkflowExecution]`
  - `cancel_execution(execution_id) -> None`
  - `resume_execution(execution_id, response) -> None` (HITL 応答)

### 2.3 API Routers

- `src/platform/api/routers/agents.py` — Agent spec CRUD
- `src/platform/api/routers/workflows.py` — Workflow spec CRUD
- `src/platform/api/routers/executions.py` — Workflow 実行管理
- `src/platform/api/routers/tools.py` — Tool spec CRUD

### 2.4 DI (deps/)

- `src/platform/api/deps/cosmos.py` — CosmosClient / ContainerProxy 提供
- `src/platform/api/deps/services.py` — Service インスタンス提供

### 成果物

```
src/platform/application/
  spec_management/
    agent_spec_service.py
    workflow_spec_service.py
    tool_spec_service.py
  run_management/
    workflow_execution_service.py
src/platform/api/
  routers/
    agents.py
    workflows.py
    executions.py
    tools.py
  deps/
    cosmos.py
    services.py
  schemas/
    agent.py
    workflow.py
    execution.py
```

---

## Phase 3: Eval Runner

**目的**: Agent の品質を定量評価する仕組み。ローカル + Foundry 両対応。

### 3.1 ローカル eval runner

- `src/platform/eval/runner.py`
- MAF `LocalEvaluator` + `@evaluator` を使用
- pytest 経由で実行可能 (`make eval`)
- eval config schema 定義

### 3.2 eval config schema

```yaml
# agents/<name>/evals/eval_config.yaml
evaluators:
  - type: relevance
    threshold: 0.8
  - type: groundedness
    threshold: 0.7
dataset: test_queries.jsonl
```

### 3.3 サンプル eval dataset

- `src/platform/agents/text_analyzer/evals/test_queries.jsonl`
- `config/agents/expense_checker/evals/test_queries.jsonl`

### 成果物

```
src/platform/eval/
  __init__.py
  runner.py
  config_schema.py
agents/text_analyzer/evals/
  eval_config.yaml
  test_queries.jsonl
```

---

## Phase 4: Foundry Sync

**目的**: AgentSpec を Foundry Agent Service に同期し、エンタープライズ機能を活用する。

### 4.1 Foundry adapter

- `src/platform/infrastructure/foundry/__init__.py`
- `src/platform/infrastructure/foundry/agent_sync.py`
  - `sync_agent_to_foundry(spec: AgentSpec) -> FoundrySyncResult`
  - `get_foundry_agent_status(foundry_agent_name) -> dict`

### 4.2 Foundry Evals 呼び出し

- `src/platform/infrastructure/foundry/eval_client.py`
  - `submit_eval_run(dataset, evaluators) -> EvalRunId`
  - `get_eval_results(run_id) -> EvalResults`

### 4.3 Sync イベント

- Application layer に `foundry_sync_service.py`
- AgentSpec 更新時に自動 sync (opt-in)

### 成果物

```
src/platform/infrastructure/foundry/
  __init__.py
  agent_sync.py
  eval_client.py
src/platform/application/
  foundry_sync_service.py
```

---

## Phase 5: ビジネスサンプル

**目的**: 実務に近いサンプルで設計の妥当性を検証する。

### 5.1 Template Agent: expense_checker

- 経費ポリシーチェック + 金額計算
- カスタム tools (check_expense_policy, calculate_total)
- evals/ 付き

### 5.2 Template Agent: document_classifier

- ドキュメント分類 + structured output
- `features.structured_output: true`

### 5.3 Workflow: 申請承認 (approval_workflow)

- Executor 構成: validate(logic) → classify(agent) → approve(human) → notify(logic)
- HITL 付き (ReviewRequest / ReviewResponse)
- agents/ の定義を executor 内から利用

### 5.4 共有 tools

- `src/platform/tools/datetime_tools.py` — 日付・期限計算
- `src/platform/tools/notification_tools.py` — 通知送信

### 成果物

```
src/platform/agents/
  expense_checker/
    agent.py, tools.py, prompts.py, evals/
  document_classifier/
    agent.py, tools.py, prompts.py, evals/
src/platform/workflows/
  approval_workflow/
    workflow.py, contracts.py, executors/, tools/
src/platform/tools/
  datetime_tools.py
  notification_tools.py
```

---

## 依存関係

```
Phase 1 (Config Agent + Feature Flags)
  |
  v
Phase 2 (Application + API)  ←  Phase 5 (ビジネスサンプル) に部分依存
  |
  v
Phase 3 (Eval Runner)
  |
  v
Phase 4 (Foundry Sync)

Phase 5 は Phase 1 完了後いつでも着手可能
```

---

## 備考

- 各 Phase 完了ごとに `make ci` を通す
- Phase 2 以降の API は OpenAPI spec 自動生成 (FastAPI)
- Foundry sync (Phase 4) は Azure 環境が必要。ローカルではモック
- playground/ は既存のまま。platform/ の実装が進んだら playground から platform を呼ぶ形に移行
