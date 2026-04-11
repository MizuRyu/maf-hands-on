# catalog ボイラーテンプレート設計仕様

**ADR**: [004-catalog-boilerplate-design](../adr/004-catalog-boilerplate-design.md)
**日付**: 2026-04-10

---

## 1. 設計方針

- **コードが正**: Python 実装が source of truth。YAML は Foundry デプロイ用エクスポート成果物
- **Foundry 互換メタデータ**: `AgentMeta` / `WorkflowMeta` で Foundry agent.yaml に変換可能なフィールドを宣言
- **ローカル専用概念の分離**: `context_providers`, `middleware` は Meta に含めない（コード内で直接設定）

## 2. Agent テンプレート

### ディレクトリ構造

```
catalog/agents/<agent-name>/
├── __init__.py      # build_<name>_agent() を re-export
├── agent.py         # AgentMeta + Agent 構築関数
├── tools.py         # @tool 定義（Agent 固有）
└── prompts.py       # instructions 定数
```

### AgentMeta

```python
@dataclass(frozen=True)
class AgentMeta:
    name: str                    # kebab-case（例: "text-analyzer"）
    description: str
    version: int
    model_id: str                # 使用モデル ID
    foundry_kind: str = "hosted" # "prompt" | "hosted"
    tool_names: list[str] = field(default_factory=list)
```

### agent.py パターン

```python
from src.platform.catalog.meta import AgentMeta

AGENT_META = AgentMeta(
    name="text-analyzer",
    description="テキスト分析 Agent",
    version=1,
    model_id="gpt-4o",
    tool_names=["count_words", "summarize_text"],
)

INSTRUCTIONS = """..."""

def build_agent(client: BaseChatClient, **kwargs) -> Agent:
    return Agent(
        client=client,
        name=AGENT_META.name,
        description=AGENT_META.description,
        instructions=INSTRUCTIONS,
        tools=[count_words, summarize_text],
        context_providers=[...],  # ローカル専用
    )
```

## 3. Workflow テンプレート

### ディレクトリ構造

```
catalog/workflows/<workflow-name>/
├── __init__.py      # build_<name>_workflow() を re-export
├── workflow.py      # WorkflowMeta + WorkflowBuilder 構築
├── contracts.py     # Executor 間メッセージ型（dataclass）
└── executors/       # Executor が 3 つ以上で分離
    ├── __init__.py
    ├── validator.py
    └── processor.py
```

### WorkflowMeta

```python
@dataclass(frozen=True)
class WorkflowMeta:
    name: str                    # kebab-case
    description: str
    version: int
    foundry_kind: str = "workflow"
    max_iterations: int = 10
    executor_ids: list[str] = field(default_factory=list)
```

### workflow.py パターン

```python
from src.platform.catalog.meta import WorkflowMeta

WORKFLOW_META = WorkflowMeta(
    name="text-pipeline",
    description="テキスト分析パイプライン",
    version=1,
    executor_ids=["input-validator", "processor", "output-formatter"],
)

def build_workflow(*, checkpoint_storage=None) -> Workflow:
    validator = InputValidator("input-validator")
    processor = Processor("processor")
    formatter = OutputFormatter("output-formatter")

    return (
        WorkflowBuilder(start_executor=validator, checkpoint_storage=checkpoint_storage)
        .add_edge(validator, processor)
        .add_edge(processor, formatter)
        .build()
    )
```

### contracts.py パターン

```python
@dataclass
class UserRequest:
    text: str
    max_length: int = 500

@dataclass
class ValidatedInput:
    text: str
    char_count: int
    word_count: int

@dataclass
class ProcessedData:
    original_text: str
    normalized_text: str
    keywords: list[str]

@dataclass
class FormattedOutput:
    report: str
```

### Executor 分離ルール

- Executor 2 つ以下 → `workflow.py` に同居
- Executor 3 つ以上 → `executors/` に分離（1 Executor = 1 ファイル）
- `contracts.py` が dataclass 5 つ以上 → `contracts/` ディレクトリに分離

## 4. AgentExecutor パターン

Workflow 内で Agent を Executor として呼ぶ場合:

```python
from agent_framework import AgentExecutor

agent = build_my_agent(client)
agent_executor = AgentExecutor(agent)

workflow = (
    WorkflowBuilder(start_executor=preprocessor)
    .add_edge(preprocessor, agent_executor)
    .add_edge(agent_executor, postprocessor)
    .build()
)
```

## 5. Foundry エクスポート（後続フェーズ）

```
infrastructure/foundry/
└── exporter.py      # AgentMeta + tools → agent.yaml 生成
```

```python
def export_foundry_yaml(meta: AgentMeta, tools: list[Callable]) -> str:
    """AgentMeta と tool 関数から Foundry agent.yaml を生成する。"""
    ...
```

## 6. domain AgentSpec との関係

| | AgentMeta（コード側） | AgentSpec（DB 側） |
|---|---|---|
| 用途 | カタログ定義・Foundry エクスポート | Cosmos DB 永続化 |
| 配置 | `catalog/meta.py` | `domain/specs/agent_spec.py` |
| フィールド数 | 少（6） | 多（18） |
| 変換 | application 層で AgentMeta → AgentSpec |  |

## 7. 移行計画

1. `catalog/meta.py` に `AgentMeta`, `WorkflowMeta` を作成
2. 既存 `my_agent.py` → `catalog/agents/text_analyzer/` に移行
3. 既存 `my_workflow.py` → `catalog/workflows/text_pipeline/` に移行
4. DevUI / テストを新構造に追従
