# 008: Workflow ステップを DAG 化し並列実行を可能にする

- Status: Accepted
- Date: 2026-04-12

## Context

現在の `WorkflowStepDefinition` は `order: int` で直列順序を表現している。しかし実務のワークフローでは「複数の Agent を並列に実行し、全完了後に集約する」パターンが頻出する。

MAF は `FanOutEdgeGroup` / `FanInEdgeGroup` でエッジベースの並列実行をサポートしており、`ConcurrentBuilder` で fan-out → fan-in をワンライナーで構築できる。プラットフォームのモデリングもこれに揃える。

## Decision

### 1. ステップ定義を DAG 化する

`order: int` を廃止し、`depends_on: list[str]` で依存関係を表現する。

```python
@dataclass(frozen=True)
class WorkflowStepDefinition:
    step_id: str
    step_name: str
    step_type: StepType       # agent | human | logic
    depends_on: list[str]     # 依存する step_id。空 = 開始ステップ
```

依存なし = 実行可能。複数ステップが同時に依存なしなら並列実行。

### 2. 実行パターン

MAF のエッジモデルに対応する 3 パターン。

| パターン | DAG での表現 | MAF 対応 |
|---------|-------------|----------|
| 直列 | A → B → C (`depends_on` で線形チェーン) | `add_chain()` |
| fan-out | A → [B, C, D] (B,C,D が全て A のみに依存) | `add_fan_out_edges()` |
| fan-in | [B, C, D] → E (E が B,C,D 全てに依存) | `add_fan_in_edges()` |

```yaml
# 例: validate → [classify, check] → aggregate → notify
steps:
  validate:
    step_name: 入力検証
    step_type: logic
    depends_on: []
  classify:
    step_name: 分類
    step_type: agent
    depends_on: [validate]
  check:
    step_name: ポリシーチェック
    step_type: agent
    depends_on: [validate]
  aggregate:
    step_name: 結果集約
    step_type: logic
    depends_on: [classify, check]    # fan-in: 両方完了で実行
  notify:
    step_name: 通知
    step_type: logic
    depends_on: [aggregate]
```

### 3. Domain model 変更

#### WorkflowStepDefinition

```
- order: int                    # 削除
+ depends_on: list[str]         # 追加
```

#### WorkflowExecution

```
- current_step_id: str | None   # 削除
+ active_step_ids: list[str]    # 追加: 現在実行中のステップ群
```

#### WorkflowExecutionStep

変更なし。各ステップの実行記録はそのまま使える。

### 4. エラーポリシー

並列ブランチでエラーが発生した場合の挙動を `WorkflowSpec` で宣言する。

| ポリシー | 挙動 |
|---------|------|
| `fail_fast` (デフォルト) | 1 つ失敗で他の並列ブランチもキャンセル |
| `continue` | 他のブランチは続行。fan-in 時にエラー結果も含めて集約 |

```python
@dataclass(frozen=True)
class WorkflowSpec:
    ...
    parallel_error_policy: str = "fail_fast"  # "fail_fast" | "continue"
```

### 5. チェックポイント

MAF はスーパーステップ境界でチェックポイントを作成する。並列ステップ途中の中間状態はチェックポイントされない。プラットフォーム側の `active_step_ids` はステップ開始/完了時に更新する。

### 6. DAG 検証

`POST /api/workflows/{id}/validate` で以下を検証する。

- 循環依存がないこと (DAG であること)
- `depends_on` の参照先が存在すること
- 開始ステップ (`depends_on: []`) が 1 つ以上あること
- 到達不能なステップがないこと

### 7. API 変更

リクエスト:

```json
{
  "steps": {
    "validate": { "step_name": "入力検証", "step_type": "logic", "depends_on": [] },
    "classify": { "step_name": "分類", "step_type": "agent", "depends_on": ["validate"] },
    "check":    { "step_name": "チェック", "step_type": "agent", "depends_on": ["validate"] },
    "aggregate":{ "step_name": "集約", "step_type": "logic", "depends_on": ["classify", "check"] }
  }
}
```

レスポンス (execution):

```json
{
  "active_step_ids": ["classify", "check"],
  "steps": [
    { "step_id": "validate", "status": "completed" },
    { "step_id": "classify", "status": "running" },
    { "step_id": "check",    "status": "running" },
    { "step_id": "aggregate","status": "idle" }
  ]
}
```

## Consequences

- ステップ定義の表現力が上がる（直列・fan-out・fan-in・複合 DAG）
- `order` が消えるため、既存の WorkflowSpec データは移行が必要
- DAG 検証ロジックを validate エンドポイントに実装する必要がある
- Cosmos DB の `workflow_specs` コンテナのドキュメント構造が変わる（`order` → `dependsOn`）
- 直列ワークフローは `depends_on` を線形チェーンにするだけなので、記述が煩雑にはならない

### 修正対象ファイル

| ファイル | 変更 |
|---------|------|
| `domain/registry/models/workflow_spec.py` | `order` → `depends_on` |
| `domain/execution/models/workflow_run.py` | `current_step_id` → `active_step_ids` |
| `infrastructure/db/cosmos/repositories/cosmos_workflow_spec_repository.py` | シリアライズ変更 |
| `infrastructure/db/cosmos/repositories/cosmos_workflow_execution_repository.py` | シリアライズ変更 |
| `api/schemas/workflow.py` | `order` → `depends_on` |
| `api/schemas/execution.py` | `current_step_id` → `active_step_ids` |
| `api/routers/workflows.py` | リクエスト/レスポンス修正 |
| `api/routers/executions.py` | レスポンス修正 |
| `docs/specs/api-design.md` | ステップ定義の記述更新 |
| `docs/specs/cosmos-db-design.md` | ドキュメント構造更新 |
