# 004: catalog ボイラーテンプレート設計（Agent + Workflow）

- Status: Superseded by ADR-005
- Date: 2026-04-10

## Context

MAF で作った Agent/Workflow を再利用可能な形で管理し、将来的に Foundry Agent Service へエクスポートしたい。現状 `catalog/` には `my_agent.py` と `my_workflow.py` が平置きされており、構造・メタデータの型が定まっていない。

要件:
- Python コードが正（truth）。YAML はデプロイ時のエクスポート成果物
- Foundry agent.yaml に変換可能なメタデータを持つ
- Foundry にない概念（context_providers, middleware）はローカル専用として分離
- 将来の Agent/Workflow 自動生成の基盤になる構造

## Decision

### Agent テンプレート構造

```
catalog/agents/<name>/
├── __init__.py      # build_<name>_agent() を公開
├── agent.py         # AgentMeta 宣言 + Agent 構築関数
├── tools.py         # @tool 定義
└── prompts.py       # instructions 定数
```

### Workflow テンプレート構造

```
catalog/workflows/<name>/
├── __init__.py      # build_<name>_workflow() を公開
├── workflow.py      # WorkflowMeta 宣言 + WorkflowBuilder 構築
├── contracts.py     # Executor 間メッセージ型（複雑なら contracts/）
└── executors/       # Executor が 3 つ以上になったら分離。少なければ workflow.py に同居
```

### メタデータ型

`AgentMeta` / `WorkflowMeta` を catalog 層に定義する。Foundry エクスポート可能なフィールドを持つ軽量 dataclass。

| フィールド | AgentMeta | WorkflowMeta |
|-----------|-----------|-------------|
| name | ○ | ○ |
| description | ○ | ○ |
| version | ○ | ○ |
| foundry_kind | `"prompt"` / `"hosted"` | `"workflow"` |
| model_id | ○ | — |
| tool_names | ○ | — |
| max_iterations | — | ○ |
| executor_ids | — | ○ |

domain の `AgentSpec` は DB 永続化用（全フィールド）。`AgentMeta` はコード側の宣言用（軽量）。両者の変換は application 層で行う。

### Foundry エクスポート

`infrastructure/foundry/exporter.py` に `export_foundry_yaml()` を配置。AgentMeta + tools から agent.yaml を生成する。実装は後続フェーズ。

### AgentExecutor パターン

Workflow 内で Agent を Executor として呼ぶパターンは初期テンプレートに含める。

## Consequences

- catalog に新しい Agent/Workflow を追加する際のディレクトリ構造が統一される
- メタデータ型があることで将来の自動生成・Foundry エクスポートの基盤になる
- 既存の `my_agent.py` / `my_workflow.py` は新構造に移行が必要
- Tool の共有化（catalog/tools/）は重複が出てから検討する
- `CatalogMeta` 基底クラスへの共通化も実需が出てから
