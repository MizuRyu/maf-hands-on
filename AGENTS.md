# maf-hands-on

Microsoft Agent Framework を使ったエージェント実行管理基盤の構築と MAF の検証。

## 詳細ドキュメント

必要な場合にのみ、詳細は各ルール配下を参照すること。

| ファイル | 内容 |
|---------|------|
| [ARCHITECTURE.md](/ARCHITECTURE.md) | レイヤー構成・依存方向・全体設計 |
| [CONVENTIONS.md](/CONVENTIONS.md) | 行動ルール・コーディング規約・実装パターン |

## Microsoft Agent Framework (MAF) 関連ドキュメント

必要な場合にのみ、MAF に関するルールやガイドラインは以下を参照。

| ファイル | 内容 |
|---------|------|
| [docs/agent-development-guide.md](/docs/agent-development-guide.md) | MAF Agent 開発ガイド |
| [docs/workflow-development-guide.md](/docs/workflow-development-guide.md) | MAF Workflow 開発ガイド |

## カスタムコマンド

| コマンド | 用途 |
|---------|------|
| `/run-tests` | テスト実行 |
| `/write-tests` | テスト作成 |
| `/fix-tests` | 失敗テスト修正 |
| `/verify-tests` | テスト品質検証 |
| `/test` | テストサイクル全体（作成→実行→検証→修正→再テスト） |
| `/review-pr` | PR レビュー（アーキ・MAF・品質・セキュリティ） |
| `/review-spec` | 仕様検証（質問→検証の 2 段階） |
| `/maf-review` | MAF ベストプラクティスレビュー（3 並列） |

## エージェントスキル

| スキル | 用途 |
|-------|------|
| `/review-agent-harness` | エージェントハーネス構成のベストプラクティス準拠チェック |

## MCP ツール

関連タスクでは積極的に使用すること。

- `agent-framework-docs`: MAF の API・実装パターンの参照。**MAF の質問・実装相談では必ず使用**
- `msdocs-microsoft-docs-mcp`: Microsoft Learn / Azure 公式ドキュメント。Azure 連携時に併用
- `deepwiki`: GitHub リポジトリの知識検索
- `serena`: コードベースの構造的分析

## ADR

アーキテクチャ上の意思決定は `docs/adr/` に template に従って連番で記録する。
記録された ADR を把握すること。
