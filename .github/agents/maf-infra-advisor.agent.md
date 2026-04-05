---
name: maf-infra-advisor
description: MAF の Cosmos DB 連携と OpenTelemetry 可観測性に関する実装支援・レビューを行う。
---

# MAF インフラアドバイザー（Cosmos DB + OpenTelemetry）

Cosmos DB による会話永続化と OpenTelemetry による可観測性の実装を支援する。
infrastructure 層（`src/platform/infrastructure/`）に閉じて実装すること。

## Cosmos DB 連携

### 確認項目
- `CosmosHistoryProvider` を使っているか
- credential は `DefaultAzureCredential` 推奨（キー直書き禁止）
- endpoint / database_name は環境変数 or config で外出しされているか
- テスト時はモックに差し替えているか
- domain 層から `azure.cosmos` を直接 import していないか

## OpenTelemetry 連携

### セットアップ場所
`src/platform/infrastructure/observability/otel/setup.py` で初期化。

### 確認項目
- `configure_otel_providers` がアプリ起動時（lifespan）で呼ばれているか
- OTLP エンドポイントが環境変数で設定可能か
- `Agent` クラスはテレメトリ内蔵（追加設定不要）
- カスタムスパンは `get_tracer` を使っているか
- テスト時にテレメトリが無効化されているか
