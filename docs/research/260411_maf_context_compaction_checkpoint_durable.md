# MAF 1.0.0 ContextProvider / Compaction / History / Checkpoint / Durable 調査

> 調査日: 2026-04-11
> 最終更新日: 2026-04-11
> ソース: microsoft/agent-framework main ブランチ (commit 3e864cd), Microsoft Learn 公式ドキュメント

---

## 1. ContextProvider

### 概要

`ContextProvider` はエージェントのコンテキストエンジニアリングパイプラインの基本抽象クラス。`before_run` / `after_run` のフックパターンで、モデル呼び出し前後にコンテキスト（メッセージ、インストラクション、ツール、ミドルウェア）を注入・処理する。

### クラス階層

```
ContextProvider (ABC)
├── HistoryProvider (ABC)
│   ├── InMemoryHistoryProvider
│   ├── CosmosHistoryProvider       (agent-framework-azure-cosmos)
│   ├── RedisHistoryProvider        (agent-framework-redis)
│   └── カスタム実装
├── CompactionProvider
├── AzureAISearchContextProvider    (agent-framework-foundry)
├── Mem0ContextProvider             (agent-framework-mem0)
├── RedisContextProvider            (agent-framework-redis)
└── カスタム実装
```

### API

```python
class ContextProvider:
    source_id: str  # 必須。メッセージ/ツール帰属識別子

    async def before_run(
        self, *, agent, session, context: SessionContext, state: dict[str, Any]
    ) -> None: ...

    async def after_run(
        self, *, agent, session, context: SessionContext, state: dict[str, Any]
    ) -> None: ...
```

**引数の意味:**

| 引数 | 型 | 説明 |
|------|-----|------|
| `agent` | `SupportsAgentRun` | 実行中のエージェント（agent-agnostic） |
| `session` | `AgentSession` | セッション状態コンテナ |
| `context` | `SessionContext` | 今回の呼び出し専用の可変コンテキスト |
| `state` | `dict[str, Any]` | プロバイダスコープの可変 state dict |

### before_run / after_run の実行順序

```python
# agent.run() 内部
for provider in self._context_providers:
    await provider.before_run(agent=self, session=session, context=context, state=...)

# モデル呼び出し

for provider in reversed(self._context_providers):
    await provider.after_run(agent=self, session=session, context=context, state=...)
```

- `before_run`: 登録順（先頭→末尾）
- `after_run`: **逆順**（末尾→先頭）

### SessionContext の主要メソッド

```python
context.extend_messages(source_id, messages)      # コンテキストメッセージ追加
context.extend_instructions(source_id, instructions)  # インストラクション追加
context.extend_tools(source_id, tools)              # ツール追加
context.extend_middleware(source_id, middleware)     # ミドルウェア追加
context.get_messages(sources=..., exclude_sources=..., include_input=..., include_response=...)
```

### カスタム ContextProvider の作り方

#### クラスベース

```python
from agent_framework import ContextProvider, SessionContext, AgentSession, Message

class RAGContextProvider(ContextProvider):
    def __init__(self):
        super().__init__(source_id="rag")

    async def before_run(self, *, agent, session, context, state):
        # 最新ユーザーメッセージからRAG検索
        docs = await self.retrieve(context.input_messages[-1].text)
        context.extend_messages(self, [Message(role="system", contents=[f"Context: {docs}"])])

    async def after_run(self, *, agent, session, context, state):
        # レスポンスを保存等
        await self.store(context.input_messages, context.response.messages)
```

#### デコレータベース

```python
from agent_framework import Agent, before_run, after_run

agent = Agent(client=client)

@before_run(agent)
async def inject_system(agent, session, context, state):
    context.extend_messages("system", [Message(role="system", contents=["You are helpful."])])

@after_run(agent)
async def log_response(agent, session, context, state):
    print(f"Response: {context.response.text}")
```

### 既存 ContextProvider 一覧

| クラス | パッケージ | 用途 |
|--------|-----------|------|
| `InMemoryHistoryProvider` | `agent-framework` | セッション state にメモリ保存 |
| `CosmosHistoryProvider` | `agent-framework-azure-cosmos` | Cosmos DB に永続化 |
| `RedisHistoryProvider` | `agent-framework-redis` | Redis に永続化 |
| `CompactionProvider` | `agent-framework` | before/after でメッセージ圧縮 |
| `AzureAISearchContextProvider` | `agent-framework-foundry` | Azure AI Search RAG |
| `Mem0ContextProvider` | `agent-framework-mem0` | Mem0 メモリ統合 |
| `RedisContextProvider` | `agent-framework-redis` | Redis ベースのコンテキスト |

### 制約

- `state` に書く値は JSON シリアライズ可能でなければならない
- `agent` は `SupportsAgentRun` プロトコル型。特定の Agent 実装に依存しない
- ContextProvider からは chat/function ミドルウェアのみ追加可能（agent ミドルウェアは不可）

---

## 2. CompactionProvider / CompactionStrategy

### 概要

長時間実行エージェントがトークン上限に近づいたとき、コンテキストを自動的に要約・切り詰めする仕組み。ADR-0019 で設計、`_compaction.py` に実装。

### アーキテクチャ

Compaction は 3 つのポイントで適用可能:

| ポイント | タイミング | 目的 |
|---------|-----------|------|
| **Pre-run** (before_run) | HistoryProvider がロードした後 | モデルに送るコンテキスト量を削減 |
| **Post-run** (after_run) | HistoryProvider が保存する前 | ストレージサイズの削減 |
| **In-run** | FIC ループ内の各 get_response 前 | ツール呼び出し蓄積によるトークン超過を防止 |

### CompactionStrategy プロトコル

```python
@runtime_checkable
class CompactionStrategy(Protocol):
    async def __call__(self, messages: list[Message]) -> bool:
        """メッセージアノテーションを変更し、圧縮が発生したら True を返す"""
        ...
```

戦略はメッセージリストを **in-place で変更**する（`_excluded` フラグを設定）。

### 組み込み Strategy 一覧

| Strategy | 概要 | 主要パラメータ |
|----------|------|---------------|
| `TruncationStrategy` | 閾値超過時に最古グループから除外 | `max_n`, `compact_to`, `tokenizer`, `preserve_system` |
| `SlidingWindowStrategy` | 最新 N グループのみ保持 | `keep_last_groups`, `preserve_system` |
| `SelectiveToolCallCompactionStrategy` | tool_call グループのみ除外 | `keep_last_tool_call_groups` |
| `ToolResultCompactionStrategy` | 古い tool_call を要約メッセージに置換 | `keep_last_tool_call_groups` |
| `SummarizationStrategy` | LLM で古いメッセージを要約して置換 | `client`, `target_count`, `threshold`, `prompt` |
| `TokenBudgetComposedStrategy` | 複数 Strategy を組み合わせてトークン予算内に収める | `token_budget`, `tokenizer`, `strategies`, `early_stop` |

### CompactionProvider

`ContextProvider` のサブクラスで、`before_strategy` と `after_strategy` を別々に設定可能。

```python
from agent_framework import (
    Agent, CompactionProvider, InMemoryHistoryProvider,
    SlidingWindowStrategy, ToolResultCompactionStrategy,
)

history = InMemoryHistoryProvider()
compaction = CompactionProvider(
    before_strategy=SlidingWindowStrategy(keep_last_groups=20),
    after_strategy=ToolResultCompactionStrategy(keep_last_tool_call_groups=1),
    history_source_id=history.source_id,
)
agent = Agent(
    client=client,
    name="assistant",
    context_providers=[history, compaction],
)
```

### トークン予算による複合戦略

```python
from agent_framework import (
    CharacterEstimatorTokenizer, TokenBudgetComposedStrategy,
    SelectiveToolCallCompactionStrategy, SlidingWindowStrategy,
)

tokenizer = CharacterEstimatorTokenizer()  # 4文字 = 1トークンのヒューリスティック

strategy = TokenBudgetComposedStrategy(
    token_budget=4000,
    tokenizer=tokenizer,
    strategies=[
        SelectiveToolCallCompactionStrategy(keep_last_tool_call_groups=0),
        SlidingWindowStrategy(keep_last_groups=5),
    ],
    early_stop=True,  # 予算内に収まったら即停止
)
```

### グループ (MessageGroups) の概念

メッセージは atomic なグループに分類される:

| GroupKind | 内容 |
|-----------|------|
| `system` | システムメッセージ |
| `user` | ユーザーメッセージ |
| `assistant_text` | ツール呼び出しを含まないアシスタントメッセージ |
| `tool_call` | アシスタントの function_call + 対応する tool result（分割不可） |

### 補助クラス/関数

| 名前 | 用途 |
|------|------|
| `TokenizerProtocol` | `count_tokens(text) -> int` を実装するプロトコル |
| `CharacterEstimatorTokenizer` | 4文字/トークンの高速ヒューリスティック |
| `annotate_message_groups()` | メッセージにグループアノテーションを付与 |
| `annotate_token_counts()` | トークンカウントをアノテーション |
| `apply_compaction()` | Strategy 適用 + included メッセージ射影 |
| `included_messages()` | `_excluded=False` のメッセージを抽出 |
| `project_included_messages()` | `included_messages()` のエイリアス |

### 制約

- service-managed storage (`service_session_id` あり) の場合、in-run compaction は**不要**（サービス側が管理）
- `SummarizationStrategy` は LLM 呼び出しが必要（`SupportsChatGetResponse` 互換クライアント）
- カスタム Strategy は `CompactionStrategy` プロトコルに準拠すれば任意のロジックを実装可能

---

## 3. HistoryProvider

### 概要

`HistoryProvider` は `ContextProvider` のサブクラスで、会話履歴の永続化を担当する。`get_messages()` と `save_messages()` を実装するだけでカスタムプロバイダを作れる。

### API

```python
class HistoryProvider(ContextProvider):
    def __init__(
        self,
        source_id: str,
        *,
        load_messages: bool = True,       # before_run でロードするか
        store_inputs: bool = True,         # ユーザー入力を保存するか
        store_context_messages: bool = False,  # 他プロバイダのコンテキストも保存するか
        store_context_from: set[str] | None = None,  # 特定 source_id のみ保存
        store_outputs: bool = True,        # レスポンスを保存するか
    ): ...

    @abstractmethod
    async def get_messages(self, session_id, *, state=None) -> list[Message]: ...

    @abstractmethod
    async def save_messages(self, session_id, messages, *, state=None) -> None: ...
```

### source_id の役割

- メッセージ帰属 (attribution) の識別子: どのプロバイダがどのメッセージを追加したかを追跡
- `context.get_messages(sources={"rag"})` のようにフィルタリングに使用
- 複数インスタンスの識別: 同じクラスを異なる `source_id` で複数登録可能
- CompactionProvider の `history_source_id` で対象 HistoryProvider を指定

### InMemoryHistoryProvider

```python
from agent_framework import InMemoryHistoryProvider

history = InMemoryHistoryProvider(
    source_id="memory",     # デフォルト: "in_memory"
    skip_excluded=False,    # True にすると _excluded=True のメッセージをスキップ
)
```

- `session.state["in_memory"]["messages"]` にメッセージを保存
- インスタンスは状態を持たない。全データは session state に格納
- エージェントに ContextProvider が未設定の場合、自動追加される

### CosmosHistoryProvider

```python
from agent_framework_azure_cosmos import CosmosHistoryProvider

# 主メモリ + 監査用の組み合わせ
agent = Agent(
    client=client,
    context_providers=[
        InMemoryHistoryProvider("memory"),
        CosmosHistoryProvider(
            "audit",
            load_messages=False,              # ロードしない（メモリ側が担当）
            store_context_messages=True,       # RAG コンテキストも保存
        ),
    ],
)
```

### RedisHistoryProvider

```python
from agent_framework_redis import RedisHistoryProvider

memory = RedisHistoryProvider(
    source_id="memory",
    redis_url="redis://...",
)
```

### カスタム HistoryProvider の作り方

```python
from agent_framework import HistoryProvider, Message

class PostgresHistoryProvider(HistoryProvider):
    def __init__(self, connection_string: str, **kwargs):
        super().__init__(source_id="postgres", **kwargs)
        self.conn = connection_string

    async def get_messages(self, session_id, *, state=None, **kwargs):
        # DB からメッセージを取得
        rows = await self.db.fetch(session_id)
        return [Message.from_dict(row) for row in rows]

    async def save_messages(self, session_id, messages, *, state=None, **kwargs):
        # DB にメッセージを保存
        for msg in messages:
            await self.db.insert(session_id, msg.to_dict())
```

### 設定パターン

| パターン | load_messages | store_inputs | store_outputs | store_context_messages |
|---------|:---:|:---:|:---:|:---:|
| 主メモリ | True | True | True | False |
| 監査ログ | False | True | True | True |
| 評価用 | False | True | True | False |

### 制約

- `load_messages=True` のプロバイダが複数あると重複メッセージ警告が出る
- `load_messages=True` が 0 個だと「履歴がロードされない」警告が出る
- `save_messages()` は append 操作。既存履歴の置換には `replace_messages()` か `overwrite=True` が必要（Compaction 用）

---

## 4. CheckpointStorage

### 概要

Workflow のチェックポイント機能。superstep 完了ごとにワークフロー全体の状態を保存し、任意の時点から再開（resume）または別インスタンスへの復元（rehydrate）が可能。

### チェックポイントに含まれるもの

1. 全 Executor の状態
2. 次の superstep のための保留メッセージ
3. 保留中の request/response
4. 共有 state
5. イテレーションカウント

### CheckpointStorage プロトコル

```python
class CheckpointStorage(Protocol):
    async def save(self, checkpoint: WorkflowCheckpoint) -> CheckpointID: ...
    async def load(self, checkpoint_id: CheckpointID) -> WorkflowCheckpoint: ...
    async def list_checkpoints(self, *, workflow_name: str) -> list[WorkflowCheckpoint]: ...
    async def delete(self, checkpoint_id: CheckpointID) -> bool: ...
    async def get_latest(self, *, workflow_name: str) -> WorkflowCheckpoint | None: ...
    async def list_checkpoint_ids(self, *, workflow_name: str) -> list[CheckpointID]: ...
```

### 組み込み実装

| Provider | パッケージ | 永続性 | 用途 |
|----------|-----------|--------|------|
| `InMemoryCheckpointStorage` | `agent-framework` | プロセス内のみ | テスト、デモ |
| `FileCheckpointStorage` | `agent-framework` | ローカルディスク | ローカル開発 |
| `CosmosCheckpointStorage` | `agent-framework-azure-cosmos` | Azure Cosmos DB | 本番、分散 |

### 使い方

```python
from agent_framework import WorkflowBuilder, FileCheckpointStorage

checkpoint_storage = FileCheckpointStorage("/var/lib/checkpoints")

builder = WorkflowBuilder(
    start_executor=start_executor,
    checkpoint_storage=checkpoint_storage,
)
builder.add_edge(start_executor, executor_b)
builder.add_edge(executor_b, end_executor)
workflow = builder.build()

# 実行
async for event in workflow.run(input, stream=True):
    ...

# チェックポイント一覧
checkpoints = await checkpoint_storage.list_checkpoints(workflow_name=workflow.name)
```

### Resume (同一インスタンスから再開)

```python
saved = checkpoints[5]
async for event in workflow.run(checkpoint_id=saved.checkpoint_id, stream=True):
    ...
```

### Rehydrate (新しいインスタンスで復元)

```python
new_workflow = WorkflowBuilder(start_executor=start_executor).build()
async for event in new_workflow.run(
    checkpoint_id=saved.checkpoint_id,
    checkpoint_storage=checkpoint_storage,
    stream=True,
):
    ...
```

### CosmosCheckpointStorage の設定

```python
from azure.identity.aio import DefaultAzureCredential
from agent_framework_azure_cosmos import CosmosCheckpointStorage

async with (
    DefaultAzureCredential() as credential,
    CosmosCheckpointStorage(
        endpoint="https://<account>.documents.azure.com:443/",
        credential=credential,
        database_name="agent-framework",
        container_name="workflow-checkpoints",
        allowed_checkpoint_types=["my_app.models:SafeState"],  # カスタム型を許可
    ) as storage,
):
    builder = WorkflowBuilder(start_executor=start, checkpoint_storage=storage)
    workflow = builder.build()
```

環境変数:

| 変数 | 説明 |
|------|------|
| `AZURE_COSMOS_ENDPOINT` | Cosmos DB エンドポイント |
| `AZURE_COSMOS_DATABASE_NAME` | データベース名 |
| `AZURE_COSMOS_CONTAINER_NAME` | コンテナ名 |
| `AZURE_COSMOS_KEY` | アカウントキー（credential 使用時は不要） |

### Executor の状態保存

```python
class CustomExecutor(Executor):
    def __init__(self, id: str):
        super().__init__(id=id)
        self._messages: list[str] = []

    @handler
    async def handle(self, message: str, ctx: WorkflowContext):
        self._messages.append(message)

    async def on_checkpoint_save(self) -> dict[str, Any]:
        return {"messages": self._messages}

    async def on_checkpoint_restore(self, state: dict[str, Any]) -> None:
        self._messages = state.get("messages", [])
```

### セキュリティ

- `FileCheckpointStorage` / `CosmosCheckpointStorage` は pickle を使用。**restricted unpickler** がデフォルトで有効
- 許可された型のみデシリアライズ可能。カスタム型は `allowed_checkpoint_types` で追加
- pickle を完全に避けたい場合は `InMemoryCheckpointStorage` またはカスタム実装を使用
- ストレージは信頼境界。未信頼ソースからのチェックポイントは**絶対にロードしない**

### 制約

- チェックポイントは workflow definition（`workflow_name` + `graph_signature_hash`）に紐づく。特定のインスタンスには紐づかない
- `on_checkpoint_save` / `on_checkpoint_restore` を実装しないと Executor の内部状態は保存されない
- `FileCheckpointStorage` は `storage_path` が必須（デフォルトディレクトリなし）

---

## 5. Workflow の Durable Execution

### 概要

MAF の "Durable Execution" は 2 つの独立した仕組みで提供される:

| 仕組み | 対象 | 永続化方式 | Signal/Event |
|--------|------|-----------|:---:|
| **Workflow Checkpointing** | `Workflow` (graph-based) | `CheckpointStorage` | HITL request/response パターンのみ |
| **Durable Agents** | `DurableAIAgent` (Durable Task) | Durable Entities | 外部イベント対応 |

### Workflow Checkpointing による長時間実行

- superstep 単位でチェックポイントが自動作成される
- 障害時はチェックポイントから再開可能
- HITL (Human-in-the-Loop) は request/response パターンで実現:
  - Workflow が `request` を発行して停止
  - 外部からの応答を受けてチェックポイントから再開

```python
# HITL: チェックポイントから再開して応答を注入
async for event in workflow.run(checkpoint_id=cp_id, stream=True):
    if isinstance(event, RequestEvent):
        # 人間の承認を待つ
        approval = await get_human_approval(event)
        event.respond(approval)
```

### Durable Agents

Durable Task Framework 上に構築された永続エージェント。Durable Entities (virtual actors) パターンを使用。

**通常エージェントとの比較:**

| 機能 | 通常エージェント | Durable Agent |
|------|-----------------|---------------|
| 会話履歴 | メモリのみ | 永続化 |
| 障害復旧 | 状態喪失 | 自動再開 |
| マルチインスタンス | 非対応 | 任意のワーカーで再開可能 |
| HITL | プロセス維持必須 | 数日/数週間待機可能（compute ゼロ） |
| ホスティング | 任意のプロセス | コンソールアプリ、Azure Functions、Durable Task 互換ホスト |

**キータイプ (Python):**

| 型 | 説明 |
|-----|------|
| `DurableAIAgent` | 汎用プロキシ。`run()` から `AgentResponse` または `DurableAgentTask` を返す |
| `DurableAIAgentWorker` | `TaskHubGrpcWorker` をラップ。`add_agent()` でエンティティ登録 |
| `DurableAIAgentClient` | 外部呼び出し用クライアント |
| `DurableAIAgentOrchestrationContext` | オーケストレーション内でのエージェント取得 |
| `AgentEntity` | エージェント実行ロジック（状態管理、ストリーミング） |

### オーケストレーションパターン

| パターン | 説明 |
|---------|------|
| Sequential (chaining) | エージェントを順次呼び出し、出力を次に渡す |
| Parallel (fan-out/fan-in) | 複数エージェントを並行実行して集約 |
| Conditional | 構造化出力に基づく条件分岐 |
| Human-in-the-loop | 外部イベント（承認、フィードバック）で一時停止、タイムアウトあり |

### Signal / External Event

**Workflow Checkpointing**: 明示的な Signal/Event の仕組みは**ない**。HITL は request/response + checkpoint resume パターン。

**Durable Agents**: Durable Task の **external event** メカニズムをフル活用。

```python
# Python: オーケストレーション内で Human-in-the-loop
def approval_orchestration(context, _):
    agent_ctx = DurableAIAgentOrchestrationContext(context)
    agent = agent_ctx.get_agent("ReviewAgent")
    session = agent.create_session()

    result = yield agent.run("Draft a proposal", session=session)

    # 外部イベントを待機（タイムアウト付き）
    approval = yield context.wait_for_external_event("human_approval")

    if approval:
        final = yield agent.run(f"Finalize: {result.text}", session=session)
        return final.text
    return "Rejected"
```

### TTL (Time-To-Live)

Durable Agent セッションの自動クリーンアップ:

```python
# Python: AgentFunctionApp で TTL 設定
app = AgentFunctionApp(agents=[agent])
# .NET の場合:
# services.ConfigureDurableAgents(options => {
#     options.DefaultTimeToLive = TimeSpan.FromDays(14);
#     options.AddAIAgent(agent, timeToLive: TimeSpan.FromDays(7));
# });
```

- デフォルト TTL: 14 日
- メッセージ受信ごとに TTL タイマーリセット
- 期限切れでセッション state 全体を削除（会話履歴含む）

### 制約

- Durable Agents は真のエンドツーエンドストリーミング**非対応**（エンティティ操作は request/response）。Reliable Streaming（Redis Streams 等）で代替可能
- Durable Agent のエンティティアクセスはシリアライズ済み。同一セッションへの同時メッセージは順次処理
- Workflow Checkpointing と Durable Agents は**別の仕組み**。組み合わせは可能だが直接統合はされていない
- Durable Agents は `agent-framework-durabletask` + `agent-framework-azurefunctions` パッケージが必要

---

## 関連ソースコード

| ファイル | 内容 |
|---------|------|
| `python/packages/core/agent_framework/_sessions.py` | ContextProvider, HistoryProvider, InMemoryHistoryProvider, SessionContext, AgentSession |
| `python/packages/core/agent_framework/_compaction.py` | CompactionStrategy, 全 Strategy 実装, CompactionProvider |
| `python/packages/core/agent_framework/_workflows/_checkpoint.py` | CheckpointStorage, WorkflowCheckpoint, InMemoryCheckpointStorage, FileCheckpointStorage |
| `python/packages/azure-cosmos/agent_framework_azure_cosmos/_checkpoint_storage.py` | CosmosCheckpointStorage |
| `python/packages/azure-cosmos/agent_framework_azure_cosmos/_history_provider.py` | CosmosHistoryProvider |
| `python/packages/redis/agent_framework_redis/_history_provider.py` | RedisHistoryProvider |
| `docs/features/durable-agents/README.md` | Durable Agents 全体設計 |
| `docs/decisions/0016-python-context-middleware.md` | ContextProvider ADR |
| `docs/decisions/0019-python-context-compaction-strategy.md` | Compaction ADR |

## 関連ドキュメント

- [Workflows - Checkpoints (Microsoft Learn)](https://learn.microsoft.com/agent-framework/workflows/checkpoints)
- [Azure Functions (Durable)](https://learn.microsoft.com/agent-framework/integrations/azure-functions)
- [Migration Guide (AutoGen to MAF)](https://learn.microsoft.com/agent-framework/migration-guide/from-autogen/)
