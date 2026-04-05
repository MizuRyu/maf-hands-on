---
name: code-review
description: "コード変更に対してプロジェクト固有ルール・一般的ソフトウェアエンジニアリング知識に基づいた構造化レビューを実行するスキル"
when-to-use: "ユーザーが「コードレビューして」「レビューして」「実装をチェックして」「PRを確認して」などコードレビューや品質チェックを依頼したとき"
allowed-tools: ["Read", "Grep", "Glob", "Bash(git:*)", "Bash(make:*)", "Bash(uv:*)", "Agent"]
context: fork
argument-hint: "<branch-or-commit-range>"
---

# Code Review: 構造化レビュースキル

git diff で変更を検出し、4並列エージェントで多角的に分析、重要度分類してレポート生成・修正を実行する。

## Phase 1: 変更検出

1. `git diff --name-only HEAD~1`（または指定範囲）で変更ファイルを特定
2. `git diff HEAD~1` で差分全体を取得
3. 20ファイル超の場合はカテゴリ分け（新規/修正/削除、テスト/プロダクション/設定）
4. 各変更ファイルの全文も読み込む — diff だけでは見落とす問題がある

## Phase 2: 4並列レビューエージェント

4エージェントを **同時に** 起動。各エージェントに diff 全文とファイルコンテキストを渡す。

### Agent 1: code-reuse-reviewer
- 既存ユーティリティとの重複を検出

### Agent 2: code-quality-reviewer
- 冗長性・命名・抽象化・コメントの品質を検証

### Agent 3: code-efficiency-reviewer
- 不要な処理・並行性・メモリ効率を検証

### Agent 4: セキュリティ・堅牢性レビュー（インライン）

**姿勢**: 「このコードを壊すにはどうすればよいか」を常に考える。

- 境界値・並行性・入力検証・エラー処理・リソース管理を検証
- MAF 固有: Agent の instructions 漏洩、Tool の入力検証、Cosmos credential の扱い

### 各エージェント共通の出力形式
```
### [カテゴリ]: [問題の要約]
**場所:** [ファイル:行番号]
**問題:** [具体的な説明]
**改善案:** [コード例を含む提案]
**重要度:** Critical | Warning | Info
```

## Phase 3: 結果集約と修正

**Critical**: セキュリティ脆弱性、データ破損リスク、MAF アンチパターン
**Warning**: パフォーマンス劣化、設計品質低下
**Info**: 命名改善、リファクタリング候補

1. 4エージェントの結果を収集し、同一箇所への重複指摘をマージ
2. Critical → Warning → Info でソートしたレビューレポートを出力
3. Critical と Warning を自動修正し、`git diff` で検証

## Phase 4: 修正後の検証

1. `make ci`（lint + typecheck + test）を実行
2. 修正不可能・判断が必要な項目はレポートに明記
3. 最終出力: 自動修正済みリスト / 要判断リスト / テスト結果サマリー
