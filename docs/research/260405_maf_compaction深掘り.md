# MAF Compaction 深掘り調査

**調査日:** 2026-04-05

---

## 概要

Compaction はマルチターン会話でコンテキストウィンドウを超えないための仕組み。メッセージを「グループ」単位で管理し、戦略に応じて古いグループを除外・要約・圧縮する。

---

## メッセージグループの概念

`annotate_message_groups()` がメッセージをグループに分類。各グループには kind が付く:

| kind | 対象 |
|------|------|
| `system` | system メッセージ (1メッセージ=1グループ) |
| `user` | user メッセージ (1メッセージ=1グループ) |
| `assistant_text` | テキストのみの assistant |
| `tool_call` | function_call を含む assistant + 後続 tool レスポンス群をまとめて1グループ |

**重要**: `tool_call` グループはリクエスト (assistant) + レスポンス (tool) を一体として扱う。ツール呼び出しが多いと1グループが巨大になる。

---

## 6つの戦略

### 1. SlidingWindowStrategy

```python
SlidingWindowStrategy(keep_last_groups=10, preserve_system=True)
```

最もシンプル。直近 N グループのみ保持し、古いものを丸ごと除外。

- `keep_last_groups`: 保持する非 system グループ数
- `preserve_system`: system グループを除外対象から保護

**適用場面**: コンテキストの正確性より最新性が重要な場合。FAQ ボット等。

### 2. SummarizationStrategy

```python
SummarizationStrategy(client=llm_client, target_count=4, threshold=2, prompt=None)
```

古い会話を LLM で要約して1メッセージに圧縮。コンテキストを損失せず圧縮できる。

- `client`: 要約生成に使う LLM クライアント (`SupportsChatGetResponse` 準拠)
- `target_count`: 要約後に残す非 system メッセージ数
- `threshold`: `target_count + threshold` を超えたらトリガー
- `prompt`: カスタム要約プロンプト (省略時はビルトインの英語プロンプト)

**トリガー条件**: included 非 system メッセージ数 > `target_count + threshold`

**処理フロー**:
1. 末尾から `target_count` 分のグループを保持
2. 残りを LLM に渡して要約
3. 要約結果を `role="assistant"` メッセージとして挿入
4. 元メッセージは `excluded=True` にマーク

**コスト**: 要約のたびに LLM 呼び出しが発生。頻度は `threshold` で制御。

**適用場面**: 長い対話で文脈の喪失を最小化したい場合。カスタマーサポート等。

### 3. TruncationStrategy

```python
TruncationStrategy(max_n=100, compact_to=80, tokenizer=None, preserve_system=True)
```

メッセージ数またはトークン数で上限を設定。超えたら古いグループから除外。

- `max_n`: トリガー閾値
- `compact_to`: 目標値 (max_n 以下)
- `tokenizer`: 指定時はトークンベース計測。なしならメッセージ数ベース
- `preserve_system`: system 保護

**適用場面**: 予測可能なサイズ制御が必要な場合。

### 4. TokenBudgetComposedStrategy

```python
TokenBudgetComposedStrategy(
    token_budget=8000,
    tokenizer=CharacterEstimatorTokenizer(),
    strategies=[SlidingWindowStrategy(keep_last_groups=20), ToolResultCompactionStrategy()],
    early_stop=True,
)
```

複数戦略を **順番に** 実行し、トークン予算内に収める。

- `early_stop=True`: 予算達成時点で残りの戦略をスキップ
- **フォールバック**: 全戦略実行後もオーバーなら、古い非 system グループから強制除外

**適用場面**: 複数戦略を段階的に適用したい場合。本番向け。

### 5. SelectiveToolCallCompactionStrategy

```python
SelectiveToolCallCompactionStrategy(keep_last_tool_call_groups=1)
```

`tool_call` グループのみ対象。古い tool_call グループを **完全除外**。

**適用場面**: ツール呼び出し結果が一時的で再利用不要な場合。

### 6. ToolResultCompactionStrategy

```python
ToolResultCompactionStrategy(keep_last_tool_call_groups=1)
```

古い tool_call グループを **要約メッセージで置換** (LLM 不要)。

要約形式: `[Tool results: get_weather: sunny, 18°C; calculate: 42]`

**SelectiveToolCallCompactionStrategy との違い**:
- Selective: 丸ごと削除 → コンテキスト完全喪失
- ToolResult: 要約で置換 → ツール結果のエッセンスは残る

**適用場面**: ツール結果を参照する可能性があるが、フル結果は不要な場合。

---

## CompactionProvider (ContextProvider として使う)

```python
from agent_framework import CompactionProvider, InMemoryHistoryProvider

history = InMemoryHistoryProvider()
compaction = CompactionProvider(
    before_strategy=SlidingWindowStrategy(keep_last_groups=20),
    after_strategy=ToolResultCompactionStrategy(keep_last_tool_call_groups=1),
    history_source_id=history.source_id,
)

agent = Agent(client=client, context_providers=[history, compaction])
```

- `before_strategy`: `before_run` で実行。モデルに送る直前のメッセージを圧縮
- `after_strategy`: `after_run` で実行。セッション state 内の履歴を圧縮 (次ターン開始サイズ削減)

**Agent コンストラクタの `compaction_strategy` vs `CompactionProvider`**:
- `compaction_strategy`: `before_run` 相当。シンプルに1戦略指定
- `CompactionProvider`: before/after 両方制御可能。より細かい制御

---

## Tokenizer

```python
from agent_framework import CharacterEstimatorTokenizer

tokenizer = CharacterEstimatorTokenizer()  # 4文字 = 1トークンのヒューリスティック
```

`TokenizerProtocol` を実装すれば tiktoken 等も使える:

```python
class TiktokenTokenizer:
    def __init__(self, model: str = "gpt-4o"):
        import tiktoken
        self.enc = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        return len(self.enc.encode(text))
```

---

## 実践的な組み合わせ例

```python
# 本番推奨: トークン予算制御 + 段階的圧縮
strategy = TokenBudgetComposedStrategy(
    token_budget=16000,
    tokenizer=CharacterEstimatorTokenizer(),
    strategies=[
        ToolResultCompactionStrategy(keep_last_tool_call_groups=2),  # まずツール結果を圧縮
        SlidingWindowStrategy(keep_last_groups=30),                   # それでも超えたらウィンドウ縮小
    ],
    early_stop=True,
)
```

---

## 注意点

- Compaction はメッセージリストを **in-place で変更** する (アノテーション追加・excluded フラグ設定)
- `SummarizationStrategy` は LLM 呼び出しのコスト・レイテンシが発生する
- `preserve_system=True` でも `TokenBudgetComposedStrategy` のフォールバックでは system も除外される可能性がある
- グループ単位の操作なので、1メッセージだけ除外ということはできない

**最終更新日:** 2026-04-05
