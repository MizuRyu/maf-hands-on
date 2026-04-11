# 002: フォルダ構成とレイヤードアーキテクチャの採用

- Status: Superseded by ADR-005
- Date: 2026-04-05

## Context

MAF 1.0.0 をフル活用したエージェントプラットフォームを構築するにあたり、フォルダ構成とアーキテクチャパターンを決定する必要があった。

検討の過程で以下の論点があった:

- レイヤードの基本構成（domain / application / infrastructure / api）をどう適用するか
- MAF 依存を domain から排除すべきか
- 業務フロー実装（usecases）をどこに置くか（platform 外 or 内）
- 共通資産（catalog）と業務フロー固有資産（usecases）をどう分けるか

## Decision

### アーキテクチャパターン

**レイヤードアーキテクチャ** を採用する。

- 基本はレイヤード（domain / application / infrastructure / api）
- MAF はこのプラットフォームの存在理由であり、domain を含む全層で利用を許可する
- Cosmos DB / OpenTelemetry への依存は infrastructure 層に集約する

### フォルダ構成

`src/playground/` と `src/platform/` を分離し、platform 内は以下の 6 ゾーンで構成する。

```
src/
├─ playground/          # MAF 検証の場
└─ platform/
   ├─ domain/           # コアモデル（specs, runs, common, repository）
   ├─ application/      # サービス層（spec_management, run_management）
   ├─ infrastructure/   # 外部技術アダプター（maf, db, observability）
   ├─ api/              # HTTP 入口（routers, schemas, deps）
   ├─ catalog/          # 共通資産（複数 usecase で再利用する Agent/Tool 等）
   └─ usecases/         # 業務フロー別の実装（MAF 直接利用）
```

### 不採用としたもの

| 案 | 理由 |
|---|---|
| 全面的 Port/Adapter | MAF を差し替える可能性がほぼゼロ。抽象層が読みにくさを増すだけ |
| domain からの MAF 排除 | 過剰な隔離。プラットフォームの存在理由が MAF である以上、非現実的 |
| usecases を platform 外に分離 | 管理と実装が離れすぎる。オールインワンの方がシンプル |
| registry を独立概念にする | SpecRepository.save() で十分。責務衝突のリスクが高い |

## Consequences

- MAF を直接使えるため開発速度が高い
- Cosmos / OTEL の依存は infrastructure 層に閉じるためテスト容易性を確保
- catalog / usecases の 2 軸で共通資産と業務固有資産を分離できる
- MAF の破壊的変更時、影響が infrastructure に収まらない可能性がある（受容するリスク）
- 将来 catalog_management 等が必要になった場合は application に追加する
