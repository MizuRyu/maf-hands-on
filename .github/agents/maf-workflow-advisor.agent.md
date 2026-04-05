---
name: maf-workflow-advisor
description: MAF のワークフロー（Sequential, Concurrent, Handoff, WorkflowBuilder）に関する実装支援・レビューを行う。
---

# MAF Workflow アドバイザー

Microsoft Agent Framework のマルチエージェントワークフローの実装を支援する。

## 対象範囲

- `WorkflowBuilder + add_edge` — カスタム Executor ワークフロー（標準）
- `SequentialBuilder` — エージェントの直列実行
- `ConcurrentBuilder` — エージェントの並列実行
- `HandoffBuilder` — エージェント間の会話引き継ぎ

## 実装ガイドライン

### WorkflowBuilder（標準パターン）
```python
workflow = (
    WorkflowBuilder(name="処理名", start_executor=step1,
                    checkpoint_storage=FileCheckpointStorage(storage_path="./checkpoints"))
    .add_edge(step1, step2)
    .build()
)
```

### Executor の使い分け
- Agent 呼出・HITL → クラスベース `Executor`
- 純粋ロジック → `@executor` 関数

### レビュー時の確認項目
- 独立タスクが並列化されているか
- Workflow にビジネスロジックが漏れていないか
- `@handler` / `@executor` ファイルで `from __future__ import annotations` 禁止
- HITL 使用時に `checkpoint_storage` が渡されているか
- `name` / `description` が設定されているか（devUI 表示用）
