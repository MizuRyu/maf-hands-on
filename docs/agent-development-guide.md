# Agent 開発ガイド

Microsoft Agent Framework (MAF) 1.0.0 における Agent 開発のルール。

## 1. Agent 定義

### 1.1 構築パターン

Agent は `client.as_agent()` で構築する。system prompt が短ければ関数内に直接書く。長ければ `prompts.py` に分離する。

```python
def get_summary_agent(client: OpenAIChatClient) -> Agent:
    return client.as_agent(
        name="summary-agent",
        instructions=SUMMARY_INSTRUCTIONS,  # prompts.py から
        tools=[search_documents, format_output],
    )
```

### 1.2 命名

| 対象 | 規則 | 例 |
|------|------|-----|
| Agent 名 (`name=`) | kebab-case | `"summary-agent"` |
| Agent 構築関数 | `get_xxx_agent()` | `get_summary_agent()` |
| Agent を Tool として使う変数 | 動詞 + `_agent_tool` | `check_agent_tool` |

### 1.3 Agent 呼出

Workflow Executor 内から Agent を呼び出す場合は `agent.run()` を使う。

```python
result = await self._agent.run(prompt)
extracted = result.value   # response_format 指定時（構造化データ）
summary = result.text      # テキスト出力時
```

## 2. プロンプト管理

### 2.1 スタイル

**左詰め** + `.strip()` で記述する。インデントが混入すると LLM に不要な空白が渡される。

```python
# Good: prompts.py に定数として定義
SUMMARY_INSTRUCTIONS = """
あなたは要約の専門家です。
入力テキストを簡潔にまとめてください。
""".strip()
```

```python
# Bad: インデントが混入
system_prompt = """
    あなたは技術アシスタントです。
""".strip()
```

動的プロンプトは f-string を使う。

### 2.2 配置

| 種別 | 配置 | 理由 |
|------|------|------|
| system prompt（静的） | `prompts.py` に `UPPER_SNAKE_CASE` 定数 | 役割・ルールを一元管理 |
| user prompt（動的） | Executor 内にインライン f-string | 入力データを渡すだけ |

system prompt に定義した内容を user prompt で繰り返さない。

## 3. Tool 定義

`@tool` デコレータ + **snake_case・動詞始まり** で命名する。docstring 必須（LLM が Tool 選択の判断材料にする）。Tool は `tools.py` に配置する。

```python
@tool
def search_documents(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """クエリに一致するドキュメントを検索して返す。"""
    ...
```

## 4. データモデル（schemas.py）

各ドメインのデータモデルは `schemas.py` にまとめる。

| 用途 | 型 | 理由 |
|------|-----|------|
| Agent の `response_format` | `BaseModel` (Pydantic) | JSON Schema 生成が必要 |
| Executor 間データ | `BaseModel` (Pydantic) | `model_dump()` / `model_validate()` で State とやり取り |
| HITL リクエスト/レスポンス | `@dataclass` | devUI のシリアライズとの互換性 |

### 命名パターン

| 用途 | パターン |
|------|---------|
| ワークフロー入出力 | `{Domain}WorkflowInput` / `{Domain}WorkflowOutput` |
| 中間データ | `{Domain}Result` |
| HITL | `{Domain}Request` / `{Domain}Response` |
