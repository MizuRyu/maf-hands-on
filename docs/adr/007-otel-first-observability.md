# 007: OTel-first Observability

- Status: Accepted
- Date: 2026-04-12

## Context

MAF は OpenTelemetry 統合を持ち、Foundry は App Insights + Foundry Traces で 90 日の trace を提供する。監査ログを自前で二重実装すると、OTel との重複・スキーマ乖離・保守コストが発生する。

## Decision

**OTel / Foundry Traces を主系にする。自前 DB には相関 ID のみ保存する。**

### ログの 2種類

1. OTel Trace（主系）: Agent invoke / Tool call / LLM chat の Span。送信先は Aspire (dev) / App Insights + Foundry Traces (prod)。
2. App Log（補助）: get_logger() 経由の構造化ログ。stderr / Log Analytics。

### sensitive_data の環境別制御

| 環境 | sensitive_data | 入出力記録 |
|------|---------------|-----------|
| dev / test | true | Trace に全メッセージ記録 |
| staging | true | 品質検証用 |
| production | false | PII 保護のため記録しない |

### AuditMiddleware

- OTel Span に属性を付与する（agent_name, execution_id 等）
- 自前 DB には execution_id と trace_id の相関のみ保存

### コスト追跡

OTel メトリクス gen_ai.client.token.usage で自動収集。dashboard は Foundry / App Insights。

## Consequences

- prompt 内容の保存可否は sensitive_data 設定と privacy policy で制御する。
- OTel exporter の設定が環境ごとに必要。
- Foundry Traces の 90 日保持期間を超える監査要件がある場合は App Insights の retention 設定で対応する。
