# Jaeger vs Aspire Dashboard 比較レポート

## Executive Summary

Jaeger と .NET Aspire Dashboard は**同じ領域（OpenTelemetry 可視化）を異なるフェーズで担うツール**であり、競合というよりは補完関係にある。Aspire Dashboard はローカル開発・デバッグ向けの「開発者体験特化型」で、Traces / Metrics / Logs を 1 画面で即座に確認できる。一方 Jaeger はプロダクション向けの「分散トレーシング特化型」で、大規模環境でのトレース保存・検索・依存グラフ分析に強い。**どちらが優れているかは用途による**が、本プロジェクト（maf-hands-on）のようなローカル開発フェーズでは Aspire Dashboard が圧倒的に適している。

---

## 基本情報

| 項目 | Jaeger | Aspire Dashboard |
|------|--------|-----------------|
| **開発元** | Uber → CNCF (Graduated Project)[^1] | Microsoft (.NET Aspire)[^2] |
| **最新バージョン** | v2.17.0 (2026/03)[^3] | 9.2 (docker image)[^4] |
| **ライセンス** | Apache 2.0 | MIT |
| **主な対象** | プロダクション環境 | ローカル開発・デバッグ |
| **テレメトリ種別** | Traces のみ | Traces + Metrics + Logs |
| **OTLP 対応** | ✅ (v2 からネイティブ) | ✅ (gRPC/HTTP 両対応) |
| **言語依存** | なし（Go 製、任意言語から利用可） | なし（.NET 製だが任意言語から OTLP 送信可） |

---

## 機能比較マトリクス

### テレメトリの可視化

| 機能 | Jaeger | Aspire Dashboard | 備考 |
|------|--------|-----------------|------|
| **分散トレース表示** | ✅ ウォーターフォール・スパン詳細 | ✅ ウォーターフォール・スパン詳細 | 同等 |
| **メトリクス表示** | ❌ | ✅ チャート・ヒストグラム | **Aspire 限定** |
| **構造化ログ表示** | ❌ | ✅ フィルタ・ドリルダウン | **Aspire 限定** |
| **コンソールログ** | ❌ | ✅ stdout/stderr ストリーミング | **Aspire 限定** |
| **トレース↔ログ相関** | ❌ | ✅ クリックで相関ログにジャンプ | **Aspire 限定** |

### トレース分析（Jaeger の強み）

| 機能 | Jaeger | Aspire Dashboard | 備考 |
|------|--------|-----------------|------|
| **サービス依存グラフ** | ✅ DAG 表示 + API[^5] | ❌ | **Jaeger 限定** |
| **Deep Dependency Graph** | ✅ 推移的依存の探索[^6] | ❌ | **Jaeger 限定** |
| **トレース比較** | ✅ 2 つのトレースを並べて比較 | ❌ | **Jaeger 限定** |
| **高度なトレース検索** | ✅ タグ・期間・サービスでフィルタ | △ 基本的なフィルタのみ | Jaeger が大幅に優位 |
| **トレースアーカイブ** | ✅ 長期保存ストレージへ昇格[^7] | ❌ | **Jaeger 限定** |

### ストレージ

| 機能 | Jaeger | Aspire Dashboard | 備考 |
|------|--------|-----------------|------|
| **Cassandra** | ✅ | ❌ | |
| **Elasticsearch / OpenSearch** | ✅ | ❌ | |
| **ClickHouse** | ✅ (v2 で最適化)[^8] | ❌ | |
| **BadgerDB (組み込み)** | ✅ | ❌ | |
| **インメモリ** | ✅ (開発用) | ✅ (唯一の選択肢) | |
| **リモート gRPC ストレージ** | ✅ カスタムバックエンド接続 | ❌ | **Jaeger 限定** |
| **データ永続化** | ✅ | ❌（再起動で消失） | |

### 開発者体験（Aspire の強み）

| 機能 | Jaeger | Aspire Dashboard | 備考 |
|------|--------|-----------------|------|
| **ゼロコンフィグ起動** | △ (all-in-one はある) | ✅ Docker 1 コマンド | Aspire が圧倒的に楽 |
| **テレメトリ Export/Import** | ❌ | ✅ OTLP/JSON/ZIP[^9] | **Aspire 限定** |
| **HTTP API** | ✅ `/api/traces` 等 | ✅ テレメトリ取得 API[^10] | 両方あり |
| **リソース管理 UI** | ❌ | ✅ サービスの開始/停止/再起動 | **Aspire 限定** |
| **認証 (トークン)** | △ (リバースプロキシ等で対応) | ✅ 組み込みトークン認証 | |

### 運用・スケーラビリティ

| 機能 | Jaeger | Aspire Dashboard | 備考 |
|------|--------|-----------------|------|
| **水平スケーリング** | ✅ Kubernetes ネイティブ[^11] | ❌ | **Jaeger 限定** |
| **マルチテナンシー** | ✅ (v2 で改善) | ❌ | **Jaeger 限定** |
| **アラート** | △ (Prometheus 連携で間接的に)[^12] | ❌ | 両方ともネイティブ不在 |
| **高スループット対応** | ✅ 数百万 span/sec | ❌ 開発規模のみ | |
| **セルフモニタリング** | ✅ OTel で自身をトレース | ❌ | **Jaeger 限定** |

---

## 片方でしかできないこと

### 🔵 Jaeger でしかできないこと

1. **サービス依存グラフ（Deep Dependency Graph）**: トレースデータから自動生成されるサービス間の依存関係マップ。推移的依存（A→B→C）を探索でき、`/api/dependencies` API でプログラマティックにも取得可能[^5][^6]
2. **トレース比較**: 2 つのトレースを並べて差分を分析。パフォーマンスリグレッションの原因特定に有用
3. **プロダクションストレージ**: Cassandra / Elasticsearch / ClickHouse 等への永続保存。数か月～年単位のトレース保持が可能[^7][^8]
4. **トレースアーカイブ**: 個別トレースを長期保存ストレージに昇格。インシデント調査やコンプライアンス対応に使用
5. **水平スケーリング**: Collector / Query を個別にスケーリング。大規模マイクロサービス環境に対応
6. **マルチテナンシー**: 複数チーム・プロジェクトでの共有利用

### 🟢 Aspire Dashboard でしかできないこと

1. **Traces + Metrics + Logs 統合表示**: 1 つの UI でトレース・メトリクス・構造化ログをすべて確認。Jaeger はトレースのみ[^2]
2. **トレース↔ログ相関ジャンプ**: トレースのスパンからクリック一つで関連ログにドリルダウン
3. **テレメトリ Export/Import**: OTLP/JSON/ZIP 形式でテレメトリを書き出し・再読み込み。バグ報告時にチーム間でテレメトリを共有可能[^9]
4. **リソース管理 UI**: 登録されたサービスの状態確認・開始・停止・再起動が UI 上で可能
5. **コンソールログストリーミング**: サービスの stdout/stderr をリアルタイム表示
6. **ゼロコンフィグ**: Docker 1 行で起動完了。ストレージバックエンドのセットアップ不要

---

## アーキテクチャの違い

```
┌─ Jaeger v2 ──────────────────────────────────┐
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Collector │  │  Query   │  │    UI    │   │
│  │ (OTLP    │  │ Service  │  │ (React)  │   │
│  │  受信)   │  │          │  │          │   │
│  └────┬─────┘  └────┬─────┘  └──────────┘   │
│       │              │                        │
│       ▼              ▼                        │
│  ┌─────────────────────────┐                 │
│  │ Storage Backend          │                 │
│  │ (Cassandra/ES/ClickHouse)│                 │
│  └─────────────────────────┘                 │
│                                               │
│  ※ v2: OTel Collector ベースの統合バイナリ    │
└───────────────────────────────────────────────┘

┌─ Aspire Dashboard ────────────────────────────┐
│                                               │
│  ┌──────────┐  ┌──────────────────────────┐  │
│  │ OTLP     │  │ Blazor/FluentUI          │  │
│  │ Receiver  │  │ ┌───────┬──────┬──────┐ │  │
│  │ (gRPC +  │──▶│ Traces│Metrics│Logs  │ │  │
│  │  HTTP)   │  │ └───────┴──────┴──────┘ │  │
│  └──────────┘  └──────────────────────────┘  │
│       │                                       │
│       ▼                                       │
│  ┌──────────┐                                │
│  │ In-Memory │  ← 再起動で消失               │
│  │ Storage   │                                │
│  └──────────┘                                │
└───────────────────────────────────────────────┘
```

---

## 本プロジェクトでの推奨

**現在の構成** (`docker-compose.yml`): Aspire Dashboard がすでに配置済み[^4]

```yaml
aspire-dashboard:
  image: mcr.microsoft.com/dotnet/aspire-dashboard:9.2
  ports:
    - "18888:18888"  # UI
    - "4317:18889"   # OTLP gRPC → 内部 18889 にマップ
```

### 推奨パターン

| フェーズ | 推奨ツール | 理由 |
|---------|-----------|------|
| **ローカル開発** | Aspire Dashboard ✅ | MAF Agent の OTel スパン + ログ + メトリクスを 1 画面で確認。セットアップ済み |
| **ステージング/QA** | Jaeger (all-in-one) | トレースの永続化・検索・依存グラフが必要になるフェーズ |
| **プロダクション** | Jaeger + Prometheus + Grafana | フルスタック可観測性。アラート・長期保存・ダッシュボードカスタマイズ |

**結論**: ローカル開発では Aspire Dashboard で十分（むしろ最適）。プロダクションに近づくにつれ Jaeger への移行が必要。OpenTelemetry SDK で計装しておけば、**エクスポーター先を切り替えるだけ**で移行できるため、両者は排他的ではなく段階的に使い分けるのがベスト。

---

## Confidence Assessment

| 項目 | 確信度 | 備考 |
|------|--------|------|
| 基本的な機能比較 | 🟢 高 | 公式ドキュメント・複数ソースで裏取り済み |
| Aspire Dashboard の制限事項 | 🟢 高 | Microsoft 公式が「開発用」と明記 |
| Jaeger v2 のアーキテクチャ | 🟢 高 | CNCF ブログ・公式ドキュメントで確認 |
| 本プロジェクトへの推奨 | 🟢 高 | docker-compose.yml で Aspire 使用を確認済み |
| Jaeger のマルチテナンシー | 🟡 中 | ロードマップ記載だが詳細実装は未確認 |

---

## Footnotes

[^1]: [Jaeger 公式サイト](https://www.jaegertracing.io/) — CNCF Graduated Project
[^2]: [Aspire Dashboard Overview](https://aspire.dev/dashboard/overview/) — Microsoft 公式
[^3]: [Jaeger Releases](https://github.com/jaegertracing/jaeger/releases) — v2.17.0 (2026/03)
[^4]: `docker-compose.yml` — 本プロジェクトの Aspire Dashboard 定義 (image: `mcr.microsoft.com/dotnet/aspire-dashboard:9.2`)
[^5]: [Jaeger Dependency Graph](https://deepwiki.com/jaegertracing/jaeger-ui/4.3-deep-dependencies-graph) — `/api/dependencies` API
[^6]: [Deep Dependencies Graph Discussion](https://github.com/orgs/jaegertracing/discussions/5999) — DDG API の詳細
[^7]: [Jaeger Storage Backends](https://www.jaegertracing.io/docs/2.dev/storage/) — アーカイブ機能含む
[^8]: [Jaeger v2 Released: OpenTelemetry in the Core](https://www.cncf.io/blog/2024/11/12/jaeger-v2-released-opentelemetry-in-the-core/) — ClickHouse 最適化
[^9]: [Aspire 13.2: Dashboard Gets Smarter Export and Telemetry](https://devblogs.microsoft.com/aspire/aspire-dashboard-improvements-export-and-telemetry/) — Export/Import 機能
[^10]: [Aspire Dashboard Telemetry](https://aspire.dev/fundamentals/telemetry/) — HTTP API
[^11]: [Practical Guide to Distributed Tracing with Jaeger](https://betterstack.com/community/guides/observability/jaeger-guide/) — K8s スケーリング
[^12]: [Jaeger Monitoring: Essential Metrics and Alerting](https://last9.io/blog/jaeger-monitoring/) — Prometheus 連携アラート
