# Workflow 開発ガイド

Microsoft Agent Framework (MAF) 1.0.0 における Workflow 開発のルール。

## 1. 基本パターン

`WorkflowBuilder + add_edge` を標準パターンとして使う。

```python
def build_processing_workflow(client: OpenAIChatClient) -> Workflow:
    extractor = DataExtractor(client)
    validator = DataValidator(client)
    return (
        WorkflowBuilder(
            name="データ処理",
            description="データの抽出と検証",
            start_executor=extractor,
            checkpoint_storage=FileCheckpointStorage(storage_path="./checkpoints"),
        )
        .add_edge(extractor, validator)
        .build()
    )
```

## 2. 命名

| 対象 | 規則 | 例 |
|------|------|-----|
| Workflow 構築関数 | `build_xxx_workflow` | `build_processing_workflow()` |
| Executor クラス | 役割を直接表す名前 | `DataExtractor`, `FormatValidator` |
| Executor `id` | kebab-case | `"data-extractor"` |

Agent は `get_xxx_agent()`、Workflow は `build_xxx_workflow()` で接頭辞を区別する。

## 3. Executor

### 3.1 クラスベース vs 関数ベース

| 条件 | 種別 |
|------|------|
| Agent 呼出・HITL がある | クラスベース `Executor` |
| 純粋なデータ変換・比較ロジック | `@executor` 関数 |

```python
# クラスベース
class DataExtractor(Executor):
    def __init__(self, client: OpenAIChatClient) -> None:
        super().__init__(id="data-extractor")

# 関数ベース
@executor(id="validate-format")
async def validate_format(
    data: ExtractedData, ctx: WorkflowContext[ValidationResult]
) -> None:
    result = _check_format(data)
    await ctx.send_message(result)
```

### 3.2 `name` / `description`

devUI でのエンティティ表示・チェックポイント検索に使われるため、必ず設定する。`name` は日本語の業務名、`description` は補足説明。

## 4. 条件分岐（SwitchCase）

`add_switch_case_edge_group` + `Case` / `Default` を使う。

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

## 5. Human-in-the-Loop (HITL)

### 5.1 リクエスト/レスポンス

`@dataclass` で定義し `{Domain}Request` / `{Domain}Response` と命名する。

```python
@dataclass
class ReviewRequest:
    summary: str
    details: dict

@dataclass
class ReviewResponse:
    approved: bool
    comments: str
```

### 5.2 `checkpoint_storage` 必須

devUI 経由の HITL はリクエストと応答が別 HTTP セッションになるため、チェックポイントがないと応答を受け取れない。`WorkflowBuilder` に必ず `checkpoint_storage` を渡す。

## 6. `from __future__ import annotations` の禁止

`@handler` / `@response_handler` / `@executor` を使うファイルでは `from __future__ import annotations` を**使わない**。アノテーションが文字列化し、デコレータの型チェックが実行時に失敗する。

それ以外のファイル（`schemas.py`, `agents.py`, `prompts.py`, `tools.py`）では使用可。
