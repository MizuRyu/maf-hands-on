# UI 設計

**作成日**: 2026-04-12
**方式**: 静的 HTML + vanilla JS (React は後日)
**配置**: `src/platform/static/` or Jinja2 テンプレート

---

## 1. 目的

UI は 2 つの視点を持つ。

| 視点 | 誰が | 何をする |
|------|------|---------|
| **管理 (Admin)** | プラットフォーム管理者・開発者 | AgentSpec / WorkflowSpec / ToolSpec を作成・設定・検証する |
| **利用 (User)** | 業務利用者 | 定義済みの Agent / Workflow を実行し、結果を確認する |

両方を同一アプリ内に持つ。管理側で定義 → 利用側で実行 → プラットフォームに溜まるログ・実行結果を管理側で確認、という流れを 1 つの検証ワークベンチで完結させる。

### 検証で確認したいこと

- プラットフォーム上で作った Agent / Workflow / Tool が業務利用できるか
- 実行時に tool call / approval / checkpoint が正しく動くか
- プラットフォーム側に溜まる実行ログ・トレース相関が管理に十分か
- eval case 化 → 回帰テストの流れが成立するか

---

## 2. 技術方針

| 項目 | 選定 |
|------|------|
| レンダリング | 静的 HTML。サーバーサイドテンプレートは使わない |
| JS | vanilla JS (`fetch()` で API 呼び出し) |
| CSS | 最小限。classless CSS or 手書き |
| 非同期更新 | Agent run: 同期レスポンス。Workflow execution: ポーリング |
| SPA 化 | しない。ページ遷移は `<a>` で画面切替 |
| React 移行 | バックエンドが安定してから |

---

## 3. 画面一覧

### 3.1 管理 (Admin) 画面

| # | 画面 | 概要 | Phase | 主要 API |
|---|------|------|-------|----------|
| A1 | Dashboard | Agent / Workflow / Tool の件数サマリ、最近の実行 | P0 | `GET /api/agents`, etc. |
| A2 | Agent 一覧 | spec テーブル + status フィルタ | P0 | `GET /api/agents` |
| A3 | Agent 作成・編集 | フォーム。tool / middleware / features を select/toggle | P0 | `POST/PATCH /api/agents/{id}` |
| A4 | Agent バリデーション | activate 前のビジネス検証結果表示 | P0 | `POST /api/agents/{id}/validate` |
| A5 | Tool 一覧 | spec テーブル + type / status フィルタ。archive 操作 | P0 | `GET /api/tools`, `POST .../archive` |
| A6 | Tool 登録 | フォーム。parameters JSON Schema 入力 | P1 | `POST /api/tools` |
| A7 | Tool 単体実行 | JSON Schema から入力フォーム、結果表示 | P0 | `POST /api/tools/{id}/run` |
| A8 | Workflow 一覧 | spec テーブル | P1 | `GET /api/workflows` |
| A9 | Workflow 作成・編集 | step 追加・並べ替え。executor type 選択 | P1 | `POST/PATCH /api/workflows/{id}` |
| A10 | 実行ログ一覧 | 全 run 横断。type / status / agent / workflow フィルタ | P0 | `GET /api/agents/{id}/runs`, `GET /api/workflows/{id}/executions` |
| A11 | 実行ログ詳細 | run detail + trace link + step timeline | P0 | `GET .../runs/{id}`, `GET .../executions/{id}` |
| A12 | Eval データセット管理 | ケース一覧、run result からの追加 | P1 | eval API |
| A13 | Eval 実行・結果 | local eval 実行、per-case 結果 | P1 | eval API |
| A14 | Foundry Sync 状態 | 同期状態、deep link | P1 | foundry API |
| A15 | Platform 設定 | policy / features のデフォルト確認 | P1 | `GET /api/platform/options` |

### 3.2 利用 (User) 画面

業務利用者が Agent / Workflow を実際に使う画面。

| # | 画面 | 概要 | Phase | 主要 API |
|---|------|------|-------|----------|
| U1 | 利用可能 Agent 一覧 | active な Agent のカード表示 | P0 | `GET /api/agents` (status=active) |
| U2 | Agent 実行コンソール | input 入力、同期レスポンス表示、tool call 表示 | P0 | `POST /api/agents/{id}/runs` (同期) |
| U3 | Tool Approval 画面 | waiting_approval 時の承認/拒否 → input-response | P0 | `POST .../runs/{id}/input-response` |
| U4 | 利用可能 Workflow 一覧 | active な Workflow のカード表示 | P1 | `GET /api/workflows` (status=active) |
| U5 | Workflow 実行コンソール | input 入力、step 進行表示、HITL 応答 | P1 | `POST /api/workflows/{id}/executions`, polling |
| U6 | HITL 応答画面 | human step の pending input に応答 | P1 | `POST .../executions/{id}/input-response` |
| U7 | 自分の実行履歴 | userId フィルタで自分の run だけ表示 | P0 | runs API (filter: userId) |
| U8 | 実行結果詳細 | output + trace link | P0 | `GET .../runs/{id}` |

---

## 4. 画面詳細

### 4.1 Agent 実行コンソール (U2)

利用者が Agent を選んで実行する中核画面。
Agent run は同期レスポンス。送信 → レスポンス完了まで待つ。
`waiting_approval` が返ったら承認/拒否 UI を表示し、input-response で応答。

**レイアウト:**

```
+--------------------------------------------------+
| Agent: expense-checker (v1)          [Session: ▼] |
+--------------------------------------------------+
| [実行履歴エリア]                                     |
|                                                    |
| You: この経費精算書を確認してください                   |
|                                                    |
| Assistant: この経費精算書を確認します。                |
|   [Tool Call] check_expense_policy                 |
|     input: {"amount": 50000}                       |
|     output: {"approved": true}                     |
|   金額は上限以内です。承認可能です。                    |
|                                                    |
| [Waiting Approval]                                 |
|   execute_transfer: 高額送金のため承認が必要           |
|   [承認] [拒否]                                     |
|                                                    |
+--------------------------------------------------+
| [入力欄]                            [送信]          |
+--------------------------------------------------+
| trace: trace_xyz (→ App Insights)                  |
+--------------------------------------------------+
```

**機能:**
- Agent 選択 (dropdown: active agents)
- Session 選択 / 新規作成
- テキスト入力 → 同期レスポンスで結果表示 (送信中はローディング)
- Tool call の引数 / 結果をインライン表示
- `waiting_approval` 時の承認/拒否ボタン → input-response POST
- Trace ID + deep link 表示

### 4.2 Workflow 実行コンソール (U5)

**レイアウト:**

```
+--------------------------------------------------+
| Workflow: approval-workflow (v1)                   |
+--------------------------------------------------+
| [入力パネル]                                        |
| request_id: [________]                             |
| amount:     [________]                             |
|                                   [実行開始]        |
+--------------------------------------------------+
| [Step Timeline]                                    |
|                                                    |
| 1. 入力検証 (logic)     [completed]  45ms          |
| 2. 分類 (agent)         [running]    ...           |
| 3. 承認 (human)         [idle]                     |
| 4. 通知 (logic)         [idle]                     |
+--------------------------------------------------+
| [Current Step Detail]                              |
| Step: 分類                                         |
| Agent: document-classifier                         |
| Status: running                                    |
| Attempt: 1                                         |
+--------------------------------------------------+
| [HITL Panel] (Step 3 が waiting になったら表示)       |
| 承認者: manager@example.com                         |
| 依頼者: user_001                                    |
| コメント: [________]                                |
|                          [承認] [差戻し]             |
+--------------------------------------------------+
```

**機能:**
- Workflow 選択 → variables 入力フォーム (WorkflowSpec.steps から動的生成)
- Step timeline: 全 step の status / duration 表示
- Current step detail: attempt_count, checkpoint_id
- HITL panel: human step が waiting になったら入力フォーム表示
- ポーリングで数秒間隔更新

### 4.3 実行ログ一覧 (A10)

管理者が全実行を横断的に確認する画面。

**レイアウト:**

```
+--------------------------------------------------+
| 実行ログ                                           |
+--------------------------------------------------+
| フィルタ: [Type ▼] [Status ▼] [Agent/WF ▼] [検索]  |
+--------------------------------------------------+
| ID       | Type     | Target        | Status     |
|----------|----------|---------------|------------|
| run_001  | agent    | expense-check | completed  |
| wfe_002  | workflow | approval-wf   | waiting    |
| run_003  | agent    | doc-classify  | failed     |
+--------------------------------------------------+
| ← 1 2 3 →                                        |
+--------------------------------------------------+
```

**機能:**
- Type フィルタ: agent / workflow
- Status フィルタ: running / completed / failed / waiting
- Target フィルタ: agent / workflow 名
- 行クリック → 詳細画面 (A11) へ

### 4.4 実行ログ詳細 (A11)

**表示内容:**
- run / execution の基本情報 (ID, status, duration)
- Agent run: input / output / tool call timeline
- Workflow execution: step 一覧 + 各 step の status / attempt_count / duration
- Trace ID → Azure App Insights / Foundry Traces への deep link
- Checkpoint ID (workflow)
- 「eval case として保存」ボタン

### 4.5 Agent 作成・編集 (A3)

**フォーム構成:**

```
基本情報
  name:         [________]
  description:  [________]
  model:        [gpt-5-nano ▼]
  instructions: [textarea]

Tools
  [x] check_expense_policy
  [ ] calculate_total
  [ ] search_documents

Features
  history:           [on/off]
  compaction:        [on/off]
    strategy:        [sliding_window ▼]
    max_turns:       [20]
  tools:             [on/off]
  structured_output: [on/off]
    response_format: [JSON editor]

Foundry
  deployment_type:   [none ▼]

          [下書き保存]  [バリデーション]  [Activate]
```

---

## 5. P0 / P1 / P2

### P0 (検証 MVP)

**管理:** A1, A2, A3, A4, A5, A7, A10, A11
**利用:** U1, U2, U3, U7, U8

**受け入れ条件:**
- フォーム入力で AgentSpec draft を作成できる
- tool / middleware / features を選択・toggle できる
- validate でビジネス検証結果を確認できる
- 業務利用者として Agent を実行し結果を確認できる (同期レスポンス)
- Tool call / waiting_approval を確認・応答できる
- 実行ログから trace deep link で Azure に飛べる
- プラットフォーム管理者として全実行ログを横断確認できる

### P1

**管理:** A6, A8, A9, A12, A13, A14, A15
**利用:** U4, U5, U6

**受け入れ条件:**
- Workflow を作成し step 構成を確認できる
- Workflow を実行し step status / attempt_count / checkpoint を確認できる
- HITL の pending input を UI から応答できる
- 実行結果を eval case 化できる
- Local eval を実行し per-case 結果を確認できる

### P2 (将来)

- NL Agent Draft Generator
- Workflow Visual Builder
- Tool Preset / Marketplace
- Release Gate UI
- Feedback 管理
- Dashboard 集約 (run 件数, 成功率, 平均 duration)

---

## 6. ファイル構成

```
src/platform/static/
  index.html              # Dashboard (A1)
  admin/
    agents.html           # Agent 一覧 (A2)
    agent-form.html       # Agent 作成・編集 (A3)
    tools.html            # Tool 一覧 (A5)
    tool-console.html     # Tool 単体実行 (A7)
    workflows.html        # Workflow 一覧 (A8) [P1]
    workflow-form.html    # Workflow 作成・編集 (A9) [P1]
    runs.html             # 実行ログ一覧 (A10)
    run-detail.html       # 実行ログ詳細 (A11)
    eval.html             # Eval 管理 (A12, A13) [P1]
  user/
    agents.html           # 利用可能 Agent 一覧 (U1)
    agent-console.html    # Agent 実行コンソール (U2, U3)
    workflows.html        # 利用可能 Workflow 一覧 (U4) [P1]
    workflow-console.html # Workflow 実行コンソール (U5, U6) [P1]
    my-runs.html          # 自分の実行履歴 (U7, U8)
  shared/
    style.css
    api.js                # fetch() ラッパー + レスポンス envelope 処理
    polling.js            # Workflow execution 用ポーリング (setInterval)
```

---

## 7. 実装しないもの

- Azure Monitor / App Insights の代替 dashboard
- Foundry trace viewer の再実装
- 独自 IAM / RBAC (MVP)
- SPA フレームワーク (React 等)
- モバイル対応

**最終更新日**: 2026-04-12
