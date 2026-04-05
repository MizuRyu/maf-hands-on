---
name: skillify
description: "セッション中の繰り返し可能なプロセスを再利用可能なスキル（SKILL.md）として抽出・保存するメタスキル"
when-to-use: "セッション中に行った作業をスキルとして保存したいとき。例: 'スキル化して', 'skillify', 'SKILL.md作って'"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "AskUserQuestion", "Bash(mkdir:*)"]
argument-hint: "[キャプチャしたいプロセスの説明]"
---

# Skillify — セッションプロセスのスキル化

セッション中の作業手順をインタビューで精緻化し、再利用可能な SKILL.md を生成する。

## Steps

### 1. セッション分析
セッションの会話履歴から以下を特定:
- 実行された繰り返し可能なプロセス
- 各ステップの順序と成功基準
- 使用したツール・エージェント

### 2. ユーザーインタビュー（AskUserQuestion 経由）

**Round 1**: スキル名・説明・ゴールを提案し確認
**Round 2**: ステップ詳細、引数、実行コンテキスト（inline/fork）、保存先を確認
**Round 3**: 各ステップの成功基準・制約・並列実行可否を確認
**Round 4**: 発動条件とトリガーフレーズを確認

### 3. SKILL.md 生成

```yaml
---
name: {{skill-name}}
description: {{一行の説明}}
allowed-tools: [{{ツールリスト}}]
when-to-use: {{発動条件}}
argument-hint: "{{引数ヒント}}"
context: {{inline or fork}}
---
# {{タイトル}}
## Inputs
## Goal
## Steps
### 1. ステップ名
**Success criteria**: ...
```

### 4. レビューと保存
1. 全文をコードブロックで出力しレビューさせる
2. 承認後、指定パスに書き込む
3. 起動方法（`/{{skill-name}} [args]`）を伝える
