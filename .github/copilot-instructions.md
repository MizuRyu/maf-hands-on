# Copilot 固有ルール

- アーキテクチャの変更や全般的に関わる変更を行った場合は、`copilot-instructions.md` および `.github/` 配下の関連ファイルを必ず最新状態に更新する

## サブエージェント（`.github/agents/`）

| エージェント | 用途 |
|------------|------|
| `test-runner` | テスト実行・結果報告 |
| `test-fixer` | 失敗テスト1件の修正（並行起動） |
| `test-verifier` | テスト網羅性・品質の検証 |
| `maf-reviewer` | MAF ベストプラクティスに基づくコードレビュー |
| `maf-agent-advisor` | MAF Agent 定義の実装支援・レビュー |
| `maf-workflow-advisor` | MAF Workflow の実装支援・レビュー |
| `maf-infra-advisor` | Cosmos DB・OpenTelemetry の実装支援・レビュー |
| `code-quality-reviewer` | コード品質（冗長性・命名・抽象化）レビュー |
| `code-efficiency-reviewer` | 効率性（不要な処理・並行性・メモリ）レビュー |
| `code-reuse-reviewer` | 既存ユーティリティとの重複・再利用性レビュー |

## エージェントスキル（`.github/skills/`）

| スキル | 用途 |
|-------|------|
| `code-review` | 構造化コードレビュー（3並列サブエージェント） |
| `adversarial-review` | 敵対的検証（境界値・並行性・セキュリティの穴を突く） |
| `skillify` | セッション中の作業を再利用可能なスキルとして保存 |

## カスタムコマンド　（`.github/instructions/`）

| ファイル | スコープ |
|---------|---------|
| `api.instructions.md` | API 実装規約 |
| `maf.instructions.md` | MAF コーディング規約 |
| `test.instructions.md` | テスト規約 |
