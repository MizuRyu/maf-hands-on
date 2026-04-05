## MAF コーディング規約

詳細は以下を参照:
- [docs/agent-development-guide.md](/docs/agent-development-guide.md) — Agent・Tool・プロンプト
- [docs/workflow-development-guide.md](/docs/workflow-development-guide.md) — Workflow・Executor・HITL

### 要点
- Agent は `Agent(client=..., name=..., instructions=...)` で構築
- クライアントは `OpenAIChatClient`（`from agent_framework.openai`）
- Tool は `@tool` デコレータ + docstring 必須
- Workflow は `WorkflowBuilder + add_edge` が標準パターン
- `@handler` / `@executor` 使用ファイルでは `from __future__ import annotations` 禁止

### Cosmos DB
- `CosmosHistoryProvider` で会話履歴を永続化
- credential は `DefaultAzureCredential` 推奨（キー直書き禁止）
- infrastructure 層に閉じて実装

### OpenTelemetry
- `Agent` は テレメトリ内蔵（追加設定不要）
- アプリ起動時に `configure_otel_providers` を呼ぶ
- カスタムスパンは `get_tracer` で取得

### MCP ツール

以下の MCP が利用可能。関連タスクでは積極的に使用すること。

- `agent-framework-docs`: MAF の API・クラス・実装パターンの参照・コード検索
- `msdocs-microsoft-docs-mcp`: Microsoft Learn / Azure 公式ドキュメント参照
- `deepwiki`: GitHub リポジトリの知識検索
- `serena`: コードベースの構造的分析

### MCP 利用ポリシー

- MAF に関する質問・実装相談では、**必ず `agent-framework-docs` で確認**してから回答すること
- MAF のみの質問は `agent-framework-docs` のみを根拠とする
- Azure サービス連携・周辺 SDK 等が含まれる場合は `msdocs-microsoft-docs-mcp` を併用
- 回答時は、質問範囲に対して必要最小限のデータソースを選ぶこと
