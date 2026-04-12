# プラットフォーム設計 v3

**作成日**: 2026-04-12
**方針**: Foundry-first。コアは薄く。MAF を使うが MAF に直結させない。

---

## 1. 設計原則

### 1.1 Foundry-first

Foundry が担えるエンタープライズ機能は Foundry に寄せる。自前で再実装しない。

| 領域 | Foundry / Azure に任せる | 自前に残す |
|------|------------------------|-----------|
| 実行権限 | Agent Application RBAC | 相関 ID の保存 |
| Agent Identity | Foundry Agent Identity / Entra ID | Foundry identity ref の保持 |
| Tool 認証 | Foundry managed credentials / OBO | ローカル custom tool の approval |
| Observability | OTel + App Insights + Foundry Traces | `execution_id` と `trace_id` の相関 |
| Eval | MAF LocalEvaluator + Foundry Evals | dataset 規約、release gate 閾値 |
| Content Safety | Foundry Content Filter | domain-specific policy だけ middleware で追加 |
| Versioning | Foundry Agent versioning | 自前 AgentSpec version との対応 |

### 1.2 コアは薄く保つ

```
プラットフォーム = 注入エンジン（Middleware + Provider + Policy）+ Foundry sync
利用者          = 宣言（YAML / コード で「何を実行するか」を定義）
Foundry         = エンタープライズ制御面（RBAC, Identity, Safety, Eval, Traces）
```

| 責務 | プラットフォーム | 利用者 | Foundry |
|------|----------------|--------|---------|
| Agent 構築 | PlatformAgentBuilder | instructions, tools | - |
| ポリシー | REQUIRED Middleware 注入 | DEFAULT override | Content Filter, RBAC |
| 評価 | eval runner + dataset 規約 | データセット + 評価基準 | eval engine + dashboard |
| ログ | 相関 ID 保存 | カスタム Span | OTel + App Insights + Traces |
| 認可 | - | - | Azure RBAC + Agent Application |

### 1.3 MAF との境界

```
application / api
  |
platform contract（AgentSpec, policy, registry）
  |
MAF adapter（PlatformAgentBuilder, middleware, ContextProvider）
  |
agent_framework SDK
```

過剰な抽象化はしない。現時点は builder + middleware で十分。

---

## 2. Source of Truth

- `AgentSpec` -- Agent の登録情報 + Foundry sync state
- `WorkflowSpec` -- Workflow の登録情報
- `ToolSpec` -- Tool の登録情報

AgentSpec の Foundry sync フィールド:

```
foundry_agent_name
foundry_agent_version
foundry_deployment_type
foundry_application_resource_id
foundry_synced_at
```

---

## 3. Agent 定義

### 3.1 Feature flags

全 Agent の振る舞いを feature flag で制御する。デフォルトは全 ON。

| flag | デフォルト | 説明 |
|------|-----------|------|
| `history` | `true` | 会話履歴の永続化 |
| `compaction` | `true` | 履歴の圧縮 |
| `tools` | `true` | Tool 使用の有効化 |
| `structured_output` | `false` | 構造化出力（response_format） |

```yaml
features:
  history: true
  compaction: true
  tools: true
  structured_output: false
```

`platform-policy.yaml` にデフォルトを定義。Agent 単位で override。

### 3.2 定義方法

| 種別 | 定義場所 | 対象 |
|------|---------|------|
| Config Agent | `config/agents/*.yaml` | prompt + tools の組み合わせ |
| Template Agent | `agents/<name>/` | カスタム Tool やロジックが必要 |

### 3.3 Agent 構造

```
agents/<name>/
  agent.py
  tools.py
  prompts.py
  evals/
    test_queries.jsonl
    eval_config.yaml
```

Config Agent は `config/agents/*.yaml` に YAML で定義。スキーマは `name`, `version`, `model_id`, `instructions`, `tools`, `features`, `compaction`, `response_format` を持つ。

---

## 4. Workflow 設計

### 4.1 Executor 3類型

| 類型 | 責務 | ルール |
|------|------|--------|
| **agent** | LLM 判断 | `agents/` の定義を使う。executor 内で Agent を直接生成しない |
| **human** | HITL 承認・入力 | `ctx.request_info()` + `@response_handler` |
| **logic** | 変換・バリデーション | LLM 不使用。workflow 固有 Tool は `workflows/<name>/tools/` に |

### 4.2 Workflow 構造

```
workflows/<name>/
  workflow.py
  contracts.py
  tools/                # workflow 固有 Tool
  executors/
    validate.py         # logic
    analyze.py          # agent
    approve.py          # human
    notify.py           # logic
```

---

## 5. 評価設計

シンプルに保つ。

- Agent には `evals/` を必須で含める（テストデータ + eval config）
- プラットフォームに eval runner を持つ。ローカルでも Foundry でも実行可能
- ローカル: MAF `LocalEvaluator` + `@evaluator` で Agent 内で直接テスト
- リリース前: eval runner が Foundry Evals を呼ぶ
- dashboard / engine / trace 分析は Foundry に任せる

```
Agent 開発者
  -> evals/ にテストデータ + config を配置
  -> ローカルで pytest 経由の eval 実行（Agent 内で完結）
  -> リリース前に platform eval runner -> Foundry Evals
```

---

## 6. ログ・トレーシング設計

### 6.1 OTel-first

```
OTel Trace（主系）
  Agent invoke / Tool call / LLM chat の Span
  送信先: Aspire (dev) / App Insights + Foundry Traces (prod)

App Log（補助）
  get_logger() -> stderr / Log Analytics
```

### 6.2 sensitive_data 制御

**環境ごとに制御する。**

| 環境 | sensitive_data | 入出力記録 |
|------|---------------|-----------|
| dev / test | `true` | Trace に全メッセージ記録（デバッグ・eval 用） |
| staging | `true` | 同上（品質検証用） |
| production | `false` | メッセージ内容は記録しない（PII 保護） |

### 6.3 監査

AuditMiddleware -> OTel Span に属性付与。自前 DB には相関 ID のみ。Foundry Traces / App Insights が主系。

### 6.4 コスト追跡

OTel メトリクス `gen_ai.client.token.usage` で自動収集。dashboard は Foundry / App Insights。

---

## 7. ツール設計

### 7.1 ローカル Tool vs Foundry Tool

| | ローカル Tool | Foundry Tool |
|---|---|---|
| 定義場所 | `tools/` or workflow/agent 内 | Foundry Agent Service |
| 認証 | なし | Foundry Agent Identity |
| 承認 | `require_approval` | Foundry MCP `require_approval` |
| 監査 | FunctionMiddleware | Foundry Traces |

### 7.2 Tool メタデータ

docstring にサンプル値 + 制約。LLM のツール説明にそのまま渡される。

---

## 8. Compaction 設計

`features.compaction: true`（デフォルト）の Agent に適用。

| strategy | 用途 | パラメータ |
|----------|------|-----------|
| `sliding_window` | 直近 N ターン | `max_turns` |
| `token_budget` | トークン数制限 | `max_tokens` |
| `summarization` | 要約圧縮 | `max_tokens`, `model_id` |

Agent 定義内で宣言。platform-policy.yaml はデフォルトのみ。

---

## 9. ガバナンス設計

**Azure RBAC のみ。自前 ACL は持たない。**

- 本番 Agent -> Foundry Agent Application RBAC
- draft/dev -> Foundry Project RBAC
- Content Safety -> Foundry Content Filter 主系
- PurviewPolicyMiddleware -> 必要時に REQUIRED middleware に追加

---

## 10. module 構成

v3 で追加は `infrastructure/foundry/` のみ。

```
src/platform/
  agents/
  workflows/
  tools/
  domain/
  application/
  infrastructure/
    cosmos/
    foundry/           # v3 追加: Foundry sync adapter
    observability/
    config.py
  api/
```

---

## 11. ADR 候補

| # | ADR | 内容 | 優先度 |
|---|-----|------|--------|
| 006 | Foundry as Enterprise Control Plane | Foundry に任せるもの vs 自前に残すもの | 高 |
| 007 | OTel-first Observability | 監査ログは OTel/Foundry 主系。自前は相関 ID のみ | 高 |

---

将来の拡張ポイントは `platform-future-extensions.md` を参照。

**最終更新日**: 2026-04-12
