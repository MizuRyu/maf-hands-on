# Workflow 開発ガイド

Microsoft Agent Framework (MAF) 1.0.0 における Workflow 開発のルール。

## 1. ディレクトリ構成

```
workflows/<name>/
  workflow.py      # WorkflowMeta + build 関数
  contracts.py     # Executor 間データ, HITL リクエスト/レスポンス
  executors/       # Executor 定義
  tools/           # Workflow 固有 Tool (必要な場合のみ)
```

## 2. 構築パターン

`WorkflowBuilder + add_edge` で構築する。`WorkflowMeta` でメタデータを宣言。

```python
WORKFLOW_META = WorkflowMeta(
    name="approval-workflow",
    description="申請承認ワークフロー",
    version=1,
    executor_ids=["request-validator", "risk-classifier", "approver", "notifier"],
)

def build_approval_workflow(*, checkpoint_storage=None) -> Workflow:
    validator = RequestValidator("request-validator")
    classifier = RiskClassifier("risk-classifier")
    approver = Approver("approver")
    notifier = Notifier("notifier")

    return (
        WorkflowBuilder(start_executor=validator, checkpoint_storage=checkpoint_storage)
        .add_edge(validator, classifier)
        .add_edge(classifier, approver)
        .add_edge(approver, notifier)
        .build()
    )
```

### 並列実行 (fan-out / fan-in)

```python
# fan-out: 1 → 多
builder.add_fan_out_edges(dispatcher, [agent_a, agent_b])

# fan-in: 多 → 1 (全完了でバリア)
builder.add_fan_in_edges([agent_a, agent_b], aggregator)
```

## 3. 命名

| 対象 | 規則 | 例 |
|------|------|-----|
| 構築関数 | `build_xxx_workflow()` | `build_approval_workflow()` |
| Executor クラス | 役割を直接表す名前 | `RiskClassifier`, `Approver` |
| Executor `id` | kebab-case | `"risk-classifier"` |

## 4. Executor 3 類型

| 類型 | 責務 | ルール |
|------|------|--------|
| **agent** | LLM 判断 | `agents/` の定義を使う。Executor 内で Agent を直接生成しない |
| **human** | HITL 承認・入力 | `ctx.request_info()` + `@response_handler` |
| **logic** | 変換・バリデーション | LLM 不使用 |

### クラスベース vs 関数ベース

| 条件 | 種別 |
|------|------|
| Agent 呼出・HITL がある | クラスベース `Executor` |
| 純粋なデータ変換 | `@executor` 関数 |

## 5. Human-in-the-Loop (HITL)

`@dataclass` で `{Domain}Request` / `{Domain}Response` を定義。`checkpoint_storage` 必須。

```python
@dataclass
class ReviewRequest:
    summary: str

@dataclass
class ReviewResponse:
    approved: bool
    comments: str
```

## 6. 条件分岐

```python
from agent_framework import Case, Default

.add_switch_case_edge_group(
    validator,
    [
        Case(condition=lambda r: r.is_valid, target=next_step),
        Default(target=error_handler),
    ],
)
```

## 7. `from __future__ import annotations` の注意

`@handler` / `@response_handler` / `@executor` を使うファイルでは**使わない**。それ以外 (`contracts.py` 等) では使用可。
