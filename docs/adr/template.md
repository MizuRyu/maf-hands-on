# ADR Template

## ルール

- 1 ファイル 1 判断にする
- ファイル名は `NNN-short-title.md` とする
- タイトルは `# NNN: 判断内容` とする
- `Status` は `Proposed` / `Accepted` / `Deprecated` / `Superseded` を使う
- `Context` には背景と課題を書く
- `Decision` には採用内容を具体的に書く
- `Consequences` には良い影響と注意点を書く
- 長い設計議論は書かず、判断理由が追える最小限に絞る

## テンプレート

```md
# 000: タイトル

- Status: Proposed
- Date: YYYY-MM-DD

## Context

背景、課題、前提を書く。

## Decision

採用する方針を簡潔に書く。

## Consequences

- 得られる効果
- 受け入れる制約
- 次に必要な対応
```
