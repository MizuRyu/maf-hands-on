## API 実装規約

### エンドポイント設計
- RESTful な URL 設計
- リクエスト/レスポンスは Pydantic モデルで型定義
- エラーレスポンスは統一フォーマット

### レイヤードアーキテクチャ
- API ハンドラは薄く保つ（`src/platform/api/routers/`）
- ビジネスロジックは application 層に委譲
- Agent の結果をレスポンス形式に変換するだけ

### 配置
- エンドポイント: `src/platform/api/routers/`
- スキーマ: `src/platform/api/schemas/`
- DI: `src/platform/api/deps/`
