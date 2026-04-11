# maf-hands-on

Microsoft Agent Framework (MAF) を広く検証しながら、将来のエージェントプラットフォームの管理構造を育てるリポジトリ。

## 目的

MAF をフル活用し、Agent / Workflow / Tool / Context Provider を扱える再利用性の高いエージェントプラットフォームを目指す。

### 最終的な理想像

- GUI から Agent / Workflow の定義・実行・評価ができる
- 自然言語から Agent / Workflow を自動作成できる
- 実行状態やログ、監視情報を一元管理できる
- 定義やテンプレートをもとに新しい機能を追加できる

### 初期フェーズ（現在）

- MAF の主要機能を広く試せる検証基盤を作る
- Agent / Workflow を platform としてどう管理すべきか整理する
- 再利用しやすい実装パターンを見つける
- Cosmos DB と OpenTelemetry を前提にした管理方針を固める
- Microsoft Foundry（エージェント管理）+ MAF（エージェント構築）のエンタープライズ適用を検証する
- 認証・認可、マルチテナント、監査ログなどエンタープライズ要件の実現可能性を把握する

`playground` で MAF の機能を試し、得た知見を `platform` 側へ寄せていく。

## 技術スタック

| 要素 | 技術 |
|------|------|
| 言語 | Python 3.12+ |
| フレームワーク | Microsoft Agent Framework (MAF) 1.0.0 |
| パッケージ管理 | uv |
| DB | Azure Cosmos DB |
| 可観測性 | OpenTelemetry → Aspire Dashboard |
| API | FastAPI |
| コンテナ | Docker Compose |

## クイックスタート

```bash
make init     # Docker ビルド + 起動
make devui    # DevUI 起動（ローカル）
```

| サービス | URL | 用途 |
|---------|-----|------|
| backend | http://localhost:8000 | API |
| devui | http://localhost:8090 | Agent/Workflow 実行 UI |
| cosmos explorer | http://localhost:1234 | Cosmos DB 管理 |
| aspire dashboard | http://localhost:18888 | OTel トレース |

## ディレクトリ構成

```
src/
├─ playground/     # MAF 機能検証の場
└─ platform/       # エージェントプラットフォーム本体
   ├─ domain/      # コアモデル・リポジトリ ABC
   ├─ application/ # ユースケース
   ├─ infrastructure/ # Cosmos DB・OTel・設定
   ├─ api/         # FastAPI
   └─ catalog/     # 共通 Agent/Workflow 定義
```

詳細: [ARCHITECTURE.md](ARCHITECTURE.md)

## 主要コマンド

```bash
make up         # Docker 起動
make down       # Docker 停止
make reload     # 再起動
make test       # テスト実行
make ci         # lint + type + test + dead + deps + security
make playground m=<module>  # サンプル実行（Mock）
```

## ドキュメント

- [ARCHITECTURE.md](ARCHITECTURE.md) — アーキテクチャ詳細
- [CONVENTIONS.md](CONVENTIONS.md) — コーディング規約
- [docs/specs/](docs/specs/) — 設計仕様
- [docs/adr/](docs/adr/) — アーキテクチャ意思決定記録
