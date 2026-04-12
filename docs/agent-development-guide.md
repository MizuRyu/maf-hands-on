# Agent 開発ガイド

Microsoft Agent Framework (MAF) 1.0.0 における Agent 開発のルール。

## 1. Agent 定義

### 1.1 ディレクトリ構成

```
agents/<name>/
  agent.py       # AgentMeta + build 関数
  tools.py       # @tool 定義
  prompts.py     # system prompt
  schemas.py     # 構造化出力 (必要な場合のみ)
  evals/         # テストデータ + eval config
```

### 1.2 構築パターン

`PlatformAgentFactory.create()` で構築する。共通 Middleware / ContextProvider が自動注入される。agent.py は宣言のみ。build 関数は書かない。

```python
# agent.py — 宣言のみ
AGENT_META = AgentMeta(
    name="expense-checker-agent",
    description="経費ポリシーチェック",
    version=1,
    model_id="gpt-5-nano",
    tool_names=["check_expense_policy"],
)
TOOLS = [check_expense_policy]

# 呼び出し側
agent = factory.create(meta=AGENT_META, instructions=INSTRUCTIONS, tools=TOOLS)
```

### 1.3 命名

| 対象 | 規則 | 例 |
|------|------|-----|
| Agent 名 (`name=`) | kebab-case | `"expense-checker"` |
| 構築関数 | `build_xxx_agent()` | `build_expense_checker_agent()` |
| Agent を Tool として使う変数 | 動詞 + `_agent_tool` | `check_agent_tool` |

### 1.4 Feature Flags

`AgentFeatures` で振る舞いを制御する。

| flag | デフォルト | 説明 |
|------|-----------|------|
| `history` | `true` | 会話履歴の永続化 |
| `compaction` | `true` | 履歴の圧縮 |
| `tools` | `true` | Tool 使用 |
| `structured_output` | `false` | 構造化出力 |

### 1.5 Agent 呼出

Workflow Executor 内から Agent を呼び出す場合は `agent.run()` を使う。

```python
result = await self._agent.run(prompt)
extracted = result.value   # structured output 時
summary = result.text      # テキスト出力時
```

## 2. プロンプト管理

**左詰め** + `.strip()` で記述する。`prompts.py` に `UPPER_SNAKE_CASE` 定数で配置。

```python
INSTRUCTIONS = """
あなたは経費精算の確認エージェントです。
提出された経費明細を確認し、ポリシー違反がないかチェックしてください。
""".strip()
```

## 3. Tool 定義

`@tool` デコレータ + **snake_case・動詞始まり**。docstring 必須。`tools.py` に配置。

```python
@tool
def check_expense_policy(amount: int, category: str) -> dict[str, Any]:
    """経費ポリシーに違反していないかチェックする。"""
    ...
```

## 4. 構造化出力

`agents/<name>/schemas.py` に Pydantic model で定義し、builder に渡す。

```python
# schemas.py
class DocumentClassification(BaseModel):
    category: str = Field(description="分類カテゴリ")
    confidence: float = Field(description="確信度 (0.0-1.0)")

# agent.py
builder.build(..., features=AgentFeatures(structured_output=True), response_format=DocumentClassification)
```

MAF が JSON Schema 変換 + 自動 deserialize。`result.value` で Pydantic model が返る。schema 変更時は AgentSpec の version を上げる。

## 5. データモデル (contracts.py / schemas.py)

| 用途 | 型 | 配置 |
|------|-----|------|
| 構造化出力 | `BaseModel` (Pydantic) | `schemas.py` |
| Executor 間データ | `BaseModel` (Pydantic) | `contracts.py` |
| HITL リクエスト/レスポンス | `@dataclass` | `contracts.py` |

## 6. `from __future__ import annotations` の注意

`@handler` / `@response_handler` / `@executor` を使うファイルでは**使わない**。アノテーションが文字列化し、デコレータの型チェックが実行時に失敗する。
