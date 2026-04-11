# 永続化層の実装

## 概要

Cosmos DB データ定義書（`docs/specs/cosmos-db-design.md`）に基づき、永続化層を構築する。
対象は 9 コンテナ中 8 コンテナ（`messages` は MAF `CosmosHistoryProvider` 管理のため対象外）。

加えて、永続化層を活用するサンプル Agent / Workflow を `catalog/` に作成し、
仕様登録 → Agent 構築 → Workflow 実行の一連の流れを検証可能にする。

## 前提

- レイヤードアーキテクチャ（ADR-002）に準拠
- ABC は `domain/repository/`、実装は `infrastructure/db/cosmos/repositories/`
- I/O は async/await 必須
- 外部依存（Cosmos SDK）は infrastructure 層に閉じる
- ADR-003 を作成し、リポジトリ拡張の意思決定を記録する

## 設計判断

### 1. ETag と frozen dataclass の共存

ETag はインフラ関心事。ドメインモデルに含めない。
Repository 実装内で `(entity, etag)` タプルとして扱い、更新系メソッドは ETag を引数で受け取る。

```python
# ABC 側（domain/repository）
async def update(self, entity: WorkflowExecution, *, etag: str | None = None) -> WorkflowExecution: ...
```

### 2. SpecRepository の分割（ISP 準拠）

1 つの god-interface にせず、3 つに分割する。

- `AgentSpecRepository`
- `ToolSpecRepository`
- `WorkflowSpecRepository`

### 3. シリアライゼーションの配置

`to_dict()` / `from_dict()` はドメインモデルに持たせない（ストレージスキーマへの結合を避ける）。
Cosmos リポジトリ実装内に `_to_document()` / `_from_document()` として配置する。

### 4. `id` フィールドのシャドーイング回避

ドメインモデルではドメイン固有名（`spec_id`, `execution_id`, `session_id` 等）を使用。
Cosmos シリアライザで `id` フィールドへマッピングする。

### 5. BaseCosmosRepository は作らない（ただし共通ヘルパーは用意する）

PK 戦略（単一 / 階層 / 非 id）、ETag 要否、TTL 有無がコンテナごとに異なる。
各リポジトリが直接 CRUD を実装する。ただし以下の共通処理はヘルパーとして `cosmos_helpers.py` に抽出する:

- `cosmos_error_handler()`: `CosmosHttpResponseError` → ドメイン例外変換のコンテキストマネージャ
- `paginate()`: continuation token ベースのページネーションヘルパー

### 6. ページネーション

list 系メソッドは continuation token ベースのページネーションを提供する。

```python
async def list_agents(
    self, *, status: SpecStatus | None = None,
    max_items: int = 50,
    continuation_token: str | None = None,
) -> tuple[list[AgentSpec], str | None]: ...
```

### 7. ドメイン例外

`domain/common/exceptions.py` にドメイン例外を定義。
Cosmos 実装で `CosmosHttpResponseError` をキャッチしドメイン例外に変換する。

### 8. schemaVersion マイグレーション

初期は **lazy migrate-on-read** 方式を採用。
`_from_document()` 内で `schemaVersion` を確認し、古いバージョンはメモリ上で変換する。
**書き戻しは行わない** — ドキュメントは次の明示的なビジネス更新時まで旧スキーマのまま保持される。
（ETag との false conflict を回避するため。）

### 9. リポジトリ命名と分割

- `run_repository` → `workflow_execution_repository` に改名（ドメイン用語に合わせる）
- **workflow_execution と workflow_execution_step は別リポジトリに分割する**
  - 理由: 異なるコンテナ・異なる PK を 1 ABC で管理すると SRP 違反になる
  - Cosmos DB はクロスコンテナのトランザクションをサポートしないため、分離が自然
  - application 層で両リポジトリを協調させる
- `checkpoint_storage` は MAF Protocol 実装であり Repository ではない → `repositories/` の外に配置

### 10. CRUD メソッド命名の統一

`save` / `update` の曖昧さを排除し、Cosmos 操作に直接マッピングする:
- `create`: 新規作成。重複時は `ConflictError`（→ `create_item`）
- `update`: 既存更新。ETag 不一致時は `ConcurrencyError`（→ `replace_item`）
- `delete`: 削除。存在しない場合は `NotFoundError`（→ `delete_item`）
- `get`: 単一取得。存在しない場合は `NotFoundError`（→ `read_item`）

### 11. frozen dataclass の状態遷移パターン

頻繁にステータスが変わるモデル（WorkflowExecution, WorkflowExecutionStep）には
`with_status()` 等の便利メソッドを用意し、`dataclasses.replace()` を隠蔽する:

```python
@dataclass(frozen=True)
class WorkflowExecution:
    ...
    def with_status(self, status: RunStatus, updated_at: datetime) -> WorkflowExecution:
        return dataclasses.replace(self, status=status, updated_at=updated_at)
```

### 12. Checkpoint コンテナの PK 戦略

DB 設計書では階層 PK (`/workflowName, /checkpointId`) だが、MAF の `CheckpointStorage.load(checkpoint_id)` は
`checkpoint_id` のみを受け取る。階層 PK だとポイントリードに `workflowName` も必要になり、
`load()` の実装がクロスパーティションクエリに堕ちる。

**対応:** PK を `/checkpointId`（フラット）に変更。`workflowName` はインデックス付きフィールドとして
`list_checkpoints(workflow_name)` のクエリに使用する。
（DB 設計書の修正が必要 — Phase 9 で対応）

### 13. Cosmos 実装のディレクトリ構成

```
infrastructure/db/cosmos/
├── client.py                 # CosmosClientManager
├── create_containers.py      # コンテナ作成スクリプト（冪等: create_container_if_not_exists 使用）
├── cosmos_helpers.py          # 共通ヘルパー（エラーハンドラ、ページネーション）
├── checkpoint_storage.py     # MAF CheckpointStorage Protocol 実装（リポジトリではない）
└── repositories/             # リポジトリ実装
    ├── __init__.py
    ├── cosmos_agent_spec_repository.py
    ├── cosmos_tool_spec_repository.py
    ├── cosmos_workflow_spec_repository.py
    ├── cosmos_workflow_execution_repository.py
    ├── cosmos_workflow_execution_step_repository.py
    ├── cosmos_session_repository.py
    └── cosmos_user_repository.py
```

---

## Phase 1: ドメイン共通型

| ファイル | 内容 |
|---------|------|
| `domain/common/types.py` | 値型: SpecId, RunId, SessionId, UserId, StepId, CheckpointId (NewType) |
| `domain/common/enums.py` | SpecStatus, RunStatus, StepStatus, StepType, SessionStatus, UserRole, UserStatus, ToolType |
| `domain/common/exceptions.py` | NotFoundError, ConflictError, ConcurrencyError, ValidationError |

## Phase 2: ドメインモデル

| ファイル | 内容 |
|---------|------|
| `domain/specs/agent_spec.py` | AgentSpec @dataclass(frozen=True) — 19 フィールド |
| `domain/specs/tool_spec.py` | ToolSpec @dataclass(frozen=True) — 12 フィールド |
| `domain/specs/workflow_spec.py` | WorkflowSpec @dataclass(frozen=True) — 8 フィールド |
| `domain/runs/workflow_execution.py` | WorkflowExecution @dataclass(frozen=True) — 14 フィールド |
| `domain/runs/workflow_execution_step.py` | WorkflowExecutionStep @dataclass(frozen=True) — 18 フィールド |
| `domain/sessions/session.py` | Session @dataclass(frozen=True) — 12 フィールド (**新規ディレクトリ**) |
| `domain/users/user.py` | User @dataclass(frozen=True) — 10 フィールド (**新規ディレクトリ**) |

## Phase 3: リポジトリ ABC

| ファイル | 内容 |
|---------|------|
| `domain/repository/agent_spec_repository.py` | get, list, create, update, delete |
| `domain/repository/tool_spec_repository.py` | get, list, create, update, delete |
| `domain/repository/workflow_spec_repository.py` | get, list, create, update, delete |
| `domain/repository/workflow_execution_repository.py` | Execution の get, list, create, update, delete |
| `domain/repository/workflow_execution_step_repository.py` | Step の get, list_by_execution, create, update |
| `domain/repository/session_repository.py` | get, list_by_user, create, update, delete |
| `domain/repository/user_repository.py` | get, get_by_email, create, update, delete |

## Phase 4: Cosmos DB インフラ基盤

| ファイル | 内容 |
|---------|------|
| `infrastructure/db/cosmos/client.py` | CosmosClientManager: シングルトン管理、get_container() |
| `infrastructure/db/cosmos/create_containers.py` | コンテナ作成（冪等: `create_container_if_not_exists`）・インデキシングポリシー適用（make init-db 用） |
| `infrastructure/db/cosmos/cosmos_helpers.py` | `cosmos_error_handler()` コンテキストマネージャ、`paginate()` ヘルパー |

## Phase 5: Cosmos DB リポジトリ実装

`infrastructure/db/cosmos/repositories/` 配下に配置する。

| ファイル | 対象コンテナ | PK | ETag |
|---------|------------|-----|------|
| `cosmos_agent_spec_repository.py` | agent_specs | /id | 推奨 |
| `cosmos_tool_spec_repository.py` | tool_specs | /id | 推奨 |
| `cosmos_workflow_spec_repository.py` | workflows | /id | — |
| `cosmos_workflow_execution_repository.py` | workflow_executions | /id | **必須** |
| `cosmos_workflow_execution_step_repository.py` | workflow_execution_steps | /workflowExecutionId | **必須** |
| `cosmos_session_repository.py` | sessions | /sessionId | **必須** |
| `cosmos_user_repository.py` | users | /id | 任意 |

## Phase 6: CheckpointStorage 実装

`infrastructure/db/cosmos/checkpoint_storage.py` に配置する（Repository ではなく MAF Protocol 実装）。

| ファイル | 対象コンテナ | PK | 備考 |
|---------|------------|-----|------|
| `checkpoint_storage.py` | checkpoints | /checkpointId（フラット） | MAF `CheckpointStorage` Protocol 準拠 |

`workflowName` はインデックス付きフィールドとし、`list_checkpoints(workflow_name)` でクエリに使用する。
（DB 設計書の階層 PK からの変更 — 設計判断 §12 参照）

## Phase 7: テスト

| テスト | 内容 |
|-------|------|
| `tests/platform/domain/common/` | types, enums, exceptions のテスト |
| `tests/platform/domain/specs/` | AgentSpec, ToolSpec, WorkflowSpec の生成テスト |
| `tests/platform/domain/runs/` | WorkflowExecution, Step の生成テスト |
| `tests/platform/infrastructure/db/cosmos/repositories/` | ContainerProxy モックによるリポジトリテスト |
| `tests/platform/infrastructure/db/cosmos/` | CheckpointStorage テスト |

## Phase 8: サンプル Agent / Workflow（catalog）

`catalog/` にプロダクション品質のサンプル実装を作成する。
永続化層の仕様登録対象として、また開発者リファレンスとして機能する。

> ⚠️ 永続化層の動作検証（CRUD テスト）は Phase 7 のユニットテストで行う。
> ここでのサンプルは「登録されたスペックから Agent/Workflow を構築して実行する」一連のフローの具体例。

### 8.1 myAgent — サンプルエージェント

| ファイル | 内容 |
|---------|------|
| `catalog/agents/my_agent.py` | `get_my_agent(client)` — ツール付きの汎用アシスタント Agent |
| `catalog/prompts/my_agent_prompts.py` | `MY_AGENT_INSTRUCTIONS` — system prompt 定数 |
| `catalog/tools/my_tools.py` | `@tool` 定義 — Agent が使用するサンプルツール |

```python
# catalog/agents/my_agent.py のイメージ
def get_my_agent(client: BaseChatClient) -> Agent:
    return client.as_agent(
        name="my-agent",
        instructions=MY_AGENT_INSTRUCTIONS,
        tools=[search_knowledge, summarize_text],
    )
```

### 8.2 myWorkflow — サンプルワークフロー

| ファイル | 内容 |
|---------|------|
| `catalog/workflows/my_workflow.py` | `build_my_workflow(client)` — 2 ステップの処理パイプライン |

```python
# catalog/workflows/my_workflow.py のイメージ
class Extractor(Executor):
    """Agent を使ってデータを抽出する。"""
    @handler
    async def handle(self, message: InputData, ctx: WorkflowContext) -> None:
        result = await self._agent.run(prompt)
        await ctx.send_message(ExtractedData(...))

class Formatter(Executor):
    """抽出結果を整形して出力する。"""
    @handler
    async def handle(self, message: ExtractedData, ctx: WorkflowContext) -> None:
        await ctx.yield_output(FormattedResult(...))

def build_my_workflow(client: BaseChatClient) -> Workflow:
    extractor = Extractor(client)
    formatter = Formatter("formatter")
    return (
        WorkflowBuilder(start_executor=extractor)
        .add_edge(extractor, formatter)
        .build()
    )
```

### 8.3 検証目的

- AgentSpec → `agent_specs` コンテナへの永続化・読み出しの動作確認
- ToolSpec → `tool_specs` コンテナへの永続化・読み出しの動作確認
- WorkflowSpec → `workflows` コンテナの定義登録確認
- Workflow 実行 → `workflow_executions` / `workflow_execution_steps` への状態記録確認

## Phase 9: ADR・ドキュメント更新

| ファイル | 内容 |
|---------|------|
| `docs/adr/003-persistence-layer-ports.md` | SessionRepository / UserRepository 追加、SpecRepository 3 分割、run → workflow_execution 改名、Step 分離、checkpoint PK 変更の意思決定記録 |
| `ARCHITECTURE.md` | domain/ 配下に sessions/, users/ を反映。infrastructure/db/cosmos の構成更新 |
| `docs/specs/cosmos-db-design.md` | checkpoints コンテナの PK を階層 → フラットに修正（設計判断 §12） |

---

## 備考

- `messages` コンテナは MAF `CosmosHistoryProvider` に委譲。自前実装なし
- `checkpoints` は MAF `CheckpointStorage` Protocol 実装。PK はフラット `/checkpointId`（DB 設計書から変更）
- Cosmos エミュレータでの動作確認は別タスク
- サンプル Agent/Workflow は MockChatClient で動作可能にする（LLM 不要）
