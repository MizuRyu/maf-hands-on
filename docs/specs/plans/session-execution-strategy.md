# Session・実行モデル実装戦略

**作成日**: 2026-04-12
**ステータス**: Draft

---

## 1. 現状の課題

| 項目 | 状態 | 問題 |
|------|------|------|
| `agent_runs` | 実装済み（mock） | Session + OTel と役割が重複 |
| Session API | モデル/Repo のみ | エンドポイントなし。自動作成なし |
| Message | 未実装 | MAF HistoryProvider に任せるべき |
| Workflow 実行 | CRUD のみ | オーケストレーションエンジンなし |
| `agent.run()` 統合 | mock | MAF Agent 未呼び出し |

---

## 2. 実行パターンの整理

### 2.1 Agent 直接呼び出し（チャットモード）

```
User → POST /sessions/{session_id}/messages
     → Platform が AgentSession を取得/作成
     → PlatformAgentFactory.build() で Agent 構築
     → agent.run(input, session=agent_session)
     → MAF が CosmosHistoryProvider 経由で会話履歴を保存
     → レスポンス返却
```

- **Session が作られる**
- MAF の `AgentSession` がセッション管理の主体
- Platform の `Session` は AgentSession のメタデータラッパー（user_id, status, title 等）
- 会話履歴は MAF `CosmosHistoryProvider` が管理 → **Message モデル不要**
- OTel トレースは MAF SDK が自動生成

### 2.2 Workflow からの Agent 呼び出し

```
WorkflowOrchestrator → Agent ステップ検出
                     → PlatformAgentFactory.build() で Agent 構築
                     → agent.run(input)  ← Session なし
                     → 結果を WorkflowContext 経由で次ステップへ
```

- **Session 不要**
- Agent は Workflow の「部品」として呼ばれる
- 会話の文脈は不要（単発実行）
- 入出力は WorkflowExecution / Step に記録
- OTel トレースは Workflow の Span の子 Span として記録

---

## 3. `agent_runs` の判断

### 削除する

**理由:**

1. **チャットモード**: Session + MAF HistoryProvider が入出力・履歴を管理。`agent_runs` は重複
2. **実行追跡**: OTel トレース（trace_id, span）が Agent 呼び出し回数・レイテンシ・tool_calls を記録
3. **Workflow モード**: WorkflowExecution + Step が実行状態を管理。`agent_runs` の出番なし
4. **tool approval**: Session 内の会話フローで処理。専用テーブル不要

### 移行

| `agent_runs` の機能 | 移行先 |
|---------------------|--------|
| 入出力記録 | MAF CosmosHistoryProvider（会話履歴） |
| tool_calls 記録 | OTel Span attributes |
| 実行回数 | OTel metrics `gen_ai.client.token.usage` |
| tool approval | Session 会話フロー内で処理 |
| trace_id | OTel 自動付与 |

### 削除対象ファイル

```
src/platform/domain/agent_runs/           # モデル + Repository
src/platform/infrastructure/db/cosmos/repositories/cosmos_agent_run_repository.py
src/platform/application/run_management/agent_run_service.py
src/platform/api/schemas/agent_run.py
Cosmos コンテナ: agent_runs（削除）
```

### コンテナ名リネーム

```
agent_specs → agents
tool_specs  → tools
workflows   → workflows（変更なし）
```

### API 変更

```
# 削除
POST   /api/agents/{agent_id}/runs
GET    /api/agents/{agent_id}/runs
GET    /api/agents/{agent_id}/runs/{run_id}
POST   /api/agents/{agent_id}/runs/{run_id}/input-response

# 追加（Session ベース）
POST   /api/sessions                                    # セッション作成
GET    /api/sessions                                    # 一覧
GET    /api/sessions/{session_id}                       # 詳細
POST   /api/sessions/{session_id}/messages              # メッセージ送信（= Agent 実行）
GET    /api/sessions/{session_id}/messages              # 会話履歴取得
PATCH  /api/sessions/{session_id}                       # タイトル変更等
DELETE /api/sessions/{session_id}                       # セッション終了
```

---

## 4. Session 設計

### 4.1 Platform Session と MAF AgentSession の関係

```
Platform Session (Cosmos: sessions)
  ├── session_id          ← Platform が生成。MAF AgentSession と共有
  ├── user_id             ← 認証から取得
  ├── agent_id            ← どの Agent と会話しているか
  ├── status              ← active / closed / expired
  ├── title               ← UI 表示用
  ├── created_at / updated_at
  └── ttl                 ← 自動削除用

MAF AgentSession
  ├── session_id          ← Platform Session.session_id と同値
  ├── service_session_id  ← Foundry連携時のみ（MAF側で管理）
  ├── state               ← ContextProvider 用の状態 dict（MAF側で管理）
  └── (会話履歴は CosmosHistoryProvider が messages コンテナに保存)
```

### 4.2 Session ライフサイクル

```
POST /sessions (agent_id 指定)
  → Platform Session 作成 (status: active)
  → MAF AgentSession 生成（session_id を共有）

POST /sessions/{id}/messages
  → MAF AgentSession を復元（from_dict or session_id で CosmosHistoryProvider がロード）
  → agent.run(input, session=agent_session)
  → MAF が履歴保存
  → レスポンス返却

DELETE /sessions/{id}
  → Platform Session.status = closed
```

### 4.3 Session モデル変更

```python
@dataclass(frozen=True)
class Session:
    session_id: SessionId
    user_id: UserId
    agent_id: SpecId              # 追加: どの Agent のセッションか
    status: SessionStatus
    schema_version: int
    created_at: datetime
    updated_at: datetime
    title: str | None = None
    ttl: int | None = None
    # service_session_id 削除 → session_id を MAF と共有
    # state 削除 → MAF AgentSession.state が管理
```

---

## 5. Workflow 実行エンジン

### 5.1 アーキテクチャ

```
POST /workflows/{id}/executions
  → WorkflowExecutionService.start()
  → WorkflowOrchestrator.execute(spec, execution)   # ← 新規
      ├── WorkflowSpec をロード
      ├── MAF WorkflowBuilder で Workflow 構築
      ├── workflow.run(input)
      │     ├── Step(logic): executor.handle(ctx)
      │     ├── Step(agent): agent.run(input)  ← Session なし
      │     ├── Step(human): ctx.request_info() → 待機
      │     └── Checkpoint 自動保存
      └── WorkflowExecution / Step を更新
  → 202 Accepted 返却（非同期）
```

### 5.2 WorkflowOrchestrator（新規）

```
src/platform/application/run_management/workflow_orchestrator.py
```

責務:
- WorkflowSpec → MAF WorkflowBuilder 変換
- 非同期実行（BackgroundTask or asyncio.create_task）
- Step 状態を WorkflowExecutionStep に同期
- Checkpoint 保存（MAF CheckpointStorage 経由）
- HITL 待機 → execution.status = waiting
- エラー → リトライ（最大3回、指数バックオフ）

### 5.3 Platform 定義済み Workflow の実行

```
src/platform/workflows/
  text_pipeline/        # 3ステージ: validate → process → format
  approval_workflow/    # 4ステージ HITL: validate → classify(agent) → approve(human) → notify
```

これらは MAF WorkflowBuilder で構築済み。Orchestrator が spec_id → build関数のマッピングを持つ。

---

## 6. 実装フェーズ

### Phase A: agent_runs 削除 + Session API

1. Session モデルに `agent_id` 追加
2. Session API ルーター作成（CRUD + messages）
3. `POST /sessions/{id}/messages` で `agent.run()` 呼び出し（mock → 実統合）
4. agent_runs 関連コード削除
5. API 設計書更新
6. UI 更新（Agent コンソール → Session ベースに）

### Phase B: agent.run() 実統合

1. `POST /sessions/{id}/messages` 内で PlatformAgentFactory.build() → agent.run()
2. CosmosHistoryProvider による履歴永続化確認
3. OTel トレース確認（Aspire Dashboard）
4. tool approval フロー実装（waiting_approval → input-response）

### Phase C: Workflow オーケストレーション

1. WorkflowOrchestrator 実装
2. text-pipeline を API 経由で実行可能に
3. approval-workflow（HITL）を API + UI 経由で実行可能に
4. Checkpoint からの再開確認

---

## 7. 判断ログ

| 判断 | 理由 |
|------|------|
| `agent_runs` 削除 | Session + OTel で代替。重複排除 |
| Platform 独自の Message モデル不作成 | 会話メッセージは MAF CosmosHistoryProvider が Cosmos に永続化。Platform 側で二重管理しない |
| Session.session_id を MAF と共有 | service_session_id を別管理する理由がない |
| Workflow 内 Agent に Session なし | Workflow のコンテキスト ≠ 会話のコンテキスト |
| Session と Workflow は独立 | スコープ外。混ぜると複雑になるため分離 |
| Workflow は非同期 (202) | ステップ実行に時間がかかるため |
| Agent 直接呼び出しは同期 | 単一ターンのレスポンスを即座に返す |

---

**最終更新日**: 2026-04-12
