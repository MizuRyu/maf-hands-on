# MAF Evaluation 深掘り調査

**調査日:** 2026-04-05

---

## 概要

MAF の Evaluation は「エージェントの出力品質を検証する」ためのビルトイン機能。決定論的チェックからLLM-as-judge まで対応。テストフレームワーク (pytest等) と組み合わせて CI に組み込める。

---

## 評価の流れ

```
queries → agent.run() → AgentResponse → EvalItem に変換 → Evaluator で検査 → EvalResults
```

1. `evaluate_agent()` がクエリごとにエージェントを実行
2. レスポンスを `EvalItem` に変換 (会話メッセージ列 + メタデータ)
3. 各 `Evaluator` がアイテムごとにチェック実行
4. 結果を `EvalResults` に集約

---

## evaluate_agent() パラメータ

```python
results = await evaluate_agent(
    agent=my_agent,                          # 評価対象エージェント
    queries=["質問1", "質問2"],                # テストクエリ
    expected_output=["期待出力1", "期待出力2"], # 正解出力 (オプション)
    expected_tool_calls=[                     # 期待ツール呼び出し (オプション)
        ExpectedToolCall(name="get_weather", arguments={"city": "Tokyo"}),
    ],
    responses=None,                           # 事前生成レスポンス (エージェント実行スキップ)
    evaluators=[check1, check2],              # 評価関数リスト
    eval_name="my-eval",                      # 表示名
    context="参考文書テキスト...",               # groundedness 評価用コンテキスト
    conversation_split=ConversationSplit.LAST_TURN,  # 会話分割戦略
    num_repetitions=3,                        # 各クエリの実行回数
)
```

### 2つのモード

| モード | 条件 | 動作 |
|--------|------|------|
| **Run+Evaluate** | `queries` を指定 | エージェント実行 → 評価 |
| **Post-hoc** | `responses` を指定 | 実行スキップ、既存レスポンスを評価 |

---

## @evaluator デコレータ

任意の Python 関数を評価関数に変換。引数名で値が自動注入される。

### 注入可能なパラメータ

| 引数名 | 型 | 内容 |
|--------|---|------|
| `query` | `str` | ユーザーのクエリテキスト |
| `response` | `str` | エージェントのレスポンステキスト |
| `expected_output` | `str` | 正解出力 |
| `expected_tool_calls` | `list[ExpectedToolCall]` | 期待ツール呼び出し |
| `conversation` | `list[Message]` | 全会話メッセージ列 |
| `tools` | `list[FunctionTool] \| None` | 利用可能ツール定義 |
| `context` | `str \| None` | groundedness コンテキスト |

### 戻り値の型

| 戻り値型 | 解釈 |
|----------|------|
| `bool` | `True` → pass, `False` → fail |
| `float` | `>= 0.5` → pass, `< 0.5` → fail |
| `CheckResult` | `passed`, `reason`, `check_name` を明示 |
| `dict` | `{"passed": bool}` or `{"score": float}` |

### 決定論的チェックの例

```python
@evaluator
def is_japanese(response: str) -> bool:
    """レスポンスに日本語が含まれているか。"""
    return any("\u3040" <= c <= "\u9fff" for c in response)

@evaluator
def max_length(response: str) -> bool:
    return len(response) <= 1000

@evaluator
def no_hallucination_keywords(response: str) -> bool:
    banned = ["わかりません", "情報がありません"]
    return not any(kw in response for kw in banned)
```

### LLM-as-judge の例

```python
@evaluator
async def llm_relevance_judge(query: str, response: str, context: str) -> float:
    """LLM でレスポンスの関連性を0-1でスコアリング。"""
    judge_client = OpenAIChatClient(model="gpt-4o", ...)
    judge_agent = Agent(
        client=judge_client,
        instructions="与えられたクエリとコンテキストに対するレスポンスの関連性を0-1で評価してください。",
        response_format=RelevanceScore,  # Pydantic model
    )
    result = await judge_agent.run(
        f"Query: {query}\nContext: {context}\nResponse: {response}"
    )
    return result.structured_output.score  # float
```

**async 対応**: `@evaluator` は sync/async 両方の関数を受け付ける。

---

## ビルトインチェック関数

### keyword_check

```python
keyword_check("キーワード1", "キーワード2", case_sensitive=False)
```

レスポンスに**全キーワード**が含まれるか検査。

### tool_called_check

```python
tool_called_check("get_weather", "calculate", mode="all")  # 全ツールが呼ばれたか
tool_called_check("get_weather", "calculate", mode="any")  # いずれかが呼ばれたか
```

会話内の `function_call` content からツール名を抽出して検査。

### tool_calls_present

```python
from agent_framework import tool_calls_present
```

`expected_tool_calls` に指定した全ツール名が会話内に存在するか。引数チェックなし。

### tool_call_args_match

```python
from agent_framework import tool_call_args_match
```

`expected_tool_calls` の各ツールの名前 **+引数** を検査。引数は **サブセットマッチ** (期待する key-value が実際の引数に含まれていれば OK)。

---

## ConversationSplit (会話分割)

マルチターン会話のどこを「クエリ」「レスポンス」として評価するかを制御。

| 戦略 | クエリ側 | レスポンス側 |
|------|---------|------------|
| `LAST_TURN` | 最後の user メッセージまで | 最後の user 以降 |
| `FULL` | 最初の user メッセージまで | 残り全部 |

- `LAST_TURN`: 「最新の質問にちゃんと答えたか」の評価
- `FULL`: 「会話全体が元のリクエストに沿っているか」の評価

---

## num_repetitions

同じクエリを複数回実行して安定性を検証。

```python
results = await evaluate_agent(
    agent=agent,
    queries=["質問"],
    evaluators=[my_check],
    num_repetitions=5,  # 5回実行
)
# → items は5個。全部 pass なら安定、一部 fail なら非決定論的
```

**LLM の出力は非決定論的**なので、`num_repetitions > 1` で安定性を確認するのが重要。

---

## EvalResults の構造

```python
results[0].passed      # pass したアイテム数
results[0].failed      # fail したアイテム数
results[0].total       # 全アイテム数
results[0].all_passed  # 全部 pass か
results[0].per_evaluator  # {"check_name": {"passed": N, "failed": M}}
results[0].items       # list[EvalItemResult] — 各アイテムの詳細

# 失敗時にエラーを投げる
results[0].raise_for_status("Evaluation failed!")  # → EvalNotPassedError
```

### pytest 統合

```python
import pytest
from agent_framework import evaluate_agent

@pytest.mark.asyncio
async def test_agent_quality():
    results = await evaluate_agent(
        agent=my_agent,
        queries=["テスト質問"],
        evaluators=[is_japanese, is_concise],
    )
    for r in results:
        r.raise_for_status("Agent quality check failed")
```

---

## evaluate_workflow()

ワークフロー評価。エージェント評価に加えて **サブエージェント個別評価** もできる。

```python
results = await evaluate_workflow(
    workflow=my_workflow,
    queries=["入力"],
    evaluators=[my_check],
    include_overall=True,      # ワークフロー全体出力を評価
    include_per_agent=True,    # 各サブエージェントも個別評価
)

# サブエージェント別結果
for agent_name, sub_result in results[0].sub_results.items():
    print(f"{agent_name}: passed={sub_result.passed}")
```

---

## ExpectedToolCall

```python
from agent_framework import ExpectedToolCall

expected = [
    ExpectedToolCall(name="get_weather", arguments={"city": "Tokyo"}),
    ExpectedToolCall(name="calculate"),  # arguments=None → 引数チェックなし
]
```

`arguments` はサブセットマッチ。`{"city": "Tokyo"}` を期待 → 実際が `{"city": "Tokyo", "unit": "celsius"}` でも pass。

---

## まとめ: 評価パターンの選択

| パターン | 方法 | 適用場面 |
|----------|------|---------|
| **キーワードマッチ** | `keyword_check()` | 特定の情報が含まれるべき場合 |
| **ツール呼び出し検証** | `tool_called_check()`, `tool_call_args_match` | ツール選択の正確性 |
| **カスタム決定論的** | `@evaluator` + bool/float | 長さ制限、フォーマット検証、言語検出 |
| **LLM-as-judge** | `@evaluator` + async LLM 呼び出し | 関連性、正確性、有害性の主観評価 |
| **Foundry Evals** | `FoundryEvaluator` | Azure AI Foundry の品質・安全性メトリクス |
| **繰り返し安定性** | `num_repetitions > 1` | 非決定論的出力の安定性確認 |
| **事後評価** | `responses=` パラメータ | 実行済みレスポンスの品質検証 |

**最終更新日:** 2026-04-05
