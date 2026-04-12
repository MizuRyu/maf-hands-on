# Foundry Hub-Spoke マルチテナント構成調査

**調査日:** 2026-04-11

---

## 1. Foundry のリソースモデル

Foundry は **Resource > Project** の2階層構造 [公式ドキュメント](https://learn.microsoft.com/azure/foundry/concepts/architecture#how-resources-relate-in-foundry)。

```
Foundry Resource (トップレベル Azure リソース)
├── Project A (開発チーム A の作業境界)
├── Project B (開発チーム B の作業境界)
└── Project C
```

- **Resource レベル**: ネットワーク、セキュリティ、モデルデプロイメント、接続を管理
- **Project レベル**: Agent、評価、ファイル、トレースなどの開発資産を管理
- RBAC は Resource / Project 両方のスコープで割り当て可能

### 制約事項

- **クロスサブスクリプション接続はモデルデプロイメントに対して非対応** [公式ドキュメント](https://learn.microsoft.com/azure/foundry/how-to/connections-add#network-isolation)
- Project は同一 Foundry Resource 内の子リソース。別サブスクリプションの Foundry Resource 間でのエージェント共有は直接サポートされない

## 2. マルチテナント分離モデル

Azure 公式アーキテクチャガイドでは3つの分離モデルを提示 [マルチテナンシーガイド](https://learn.microsoft.com/azure/architecture/guide/multitenant/service/openai)。

| モデル | データ分離 | パフォーマンス分離 | 運用複雑度 |
|-------|-----------|----------------|----------|
| **専用インスタンス (テナント別)** | 高 | 高 | テナント数に比例 |
| **共有インスタンス + 専用デプロイメント** | 中 | 高 | 中 |
| **共有インスタンス + 共有デプロイメント** | 低 | 低〜中 | 低 |
| **テナント提供リソース** | 高 | 高 | テナント側で管理 |

### テナント提供リソースパターン

テナント (部署) が自身のサブスクリプションに Azure OpenAI を作成し、プラットフォーム側アプリにアクセスを許可するパターン。**マルチテナント Entra ID アプリケーション**で実現する [公式ドキュメント](https://learn.microsoft.com/azure/architecture/guide/multitenant/service/openai#isolation-models)。

## 3. エンタープライズ Hub-Spoke アーキテクチャ

Microsoft Tech Community のリファレンスアーキテクチャ [Azure AI Hub-and-Spoke Landing Zone](https://techcommunity.microsoft.com/blog/azurearchitectureblog/architecting-an-azure-ai-hub-and-spoke-landing-zone-for-multi-tenant-enterprises/4491161) から。

### サブスクリプション構造

```
Tenant Root Management Group
├── Platform Management Group
│   ├── Connectivity Sub (Hub VNet, Firewall, DNS)
│   ├── Management Sub (Log Analytics, Monitor)
│   └── Security Sub (Defender, Sentinel)
├── AI Hub Management Group
│   └── AI Hub Sub (共有 AI サービス、ガバナンス)
└── AI Spokes Management Group
    ├── Spoke Sub A (部署 A)
    ├── Spoke Sub B (部署 B)
    └── Spoke Sub C (部署 C)
```

### Hub (中央共有サービス)

- Application Gateway + WAF
- Azure Firewall
- API Management (内部モード)
- 共有 Azure OpenAI デプロイメント
- Azure Monitor / Log Analytics
- Azure Policy / RBAC

### Spoke (テナント専用)

- テナント専用ストレージ・DB
- テナントスコープの AI Search インデックス
- AKS ランタイム (テナント固有の Agent・バックエンド)
- テナント固有の Key Vault / Managed Identity

### テナントオンボーディングフロー

1. Spoke サブスクリプションをプロビジョニング
2. Spoke VNet を作成し Hub とピアリング
3. Private DNS / Firewall ルート設定
4. AKS テナンシー・データサービスをデプロイ
5. Identity・API サブスクリプションを登録
6. 監視・コスト帰属を有効化

### 分離レベル

| レイヤー | 手段 |
|---------|------|
| ネットワーク | 専用 VNet、Private Endpoint、Public AI Endpoint なし |
| ID | Entra ID + テナント認識 claims + 条件付きアクセス |
| コンピュート | AKS namespace / node pool / 専用 cluster |
| データ | テナント別ストレージ・DB・ベクトルインデックス |

### コスト管理

必須タグ: `tenantId`, `costCenter`, `application`, `environment`, `owner`。Azure Policy で強制。共有リソースは API Management のテレメトリ + AKS の namespace 使用量で按分。

## 4. 本プラットフォームへの示唆

### 2つのアプローチ

| アプローチ | 概要 | 利点 | 課題 |
|-----------|------|------|------|
| **A) サブスクリプション分離** | 部署ごとに Spoke サブスクリプション | データ分離が強い。Azure の標準的な Landing Zone パターン | インフラ運用コスト大。部署ごとにリソース重複 |
| **B) プラットフォーム上で開発** | 単一サブスクリプション内で Project 分離 + アプリ層制御 | インフラシンプル。開発者体験が良い | データ分離をアプリ層で担保する必要あり |

### 推奨: ハイブリッド

- **初期 (Phase 1-2)**: 単一サブスクリプション + Foundry Project 分離で開始。アプリ層で権限制御
- **スケール後 (Phase 3-4)**: 規制要件やデータ分離要件が厳しい部署は Spoke サブスクリプションに分離

理由:
- 初期は部署数が少なく、サブスクリプション分離のオーバーヘッドが大きすぎる
- Project 分離 + RBAC で多くのケースはカバーできる
- 「プラットフォーム上で Agent を作ってもらう」モデルなら、Project 分離が自然
- 本当にデータ分離が必要な部署だけ Spoke サブスクリプションに切り出す

### Agent の共有

- クロスサブスクリプションでの Agent 直接共有は Foundry 非対応
- **A2A (Agent-to-Agent) プロトコル**で異なる Project / サブスクリプション間の Agent 連携は可能 [Foundry Agent Service](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/building-a-digital-workforce-with-multi-agents-in-azure-ai-foundry-agent-service/4414671)
- 共有 Action Agent は Hub の API として公開し、Spoke から呼び出すパターンが現実的

## 5. 参考リソース

- [AI Landing Zone (GitHub)](https://github.com/Azure/AI-Landing-Zones)
- [AI Hub Gateway Solution Accelerator](https://github.com/mohamedsaif/ai-hub-gateway-landing-zone)
- [Citadel Governance Hub](https://github.com/Azure-Samples/ai-hub-gateway-solution-accelerator/blob/citadel-v1/README.md)
- [AKS Multi-Tenancy Best Practices](https://learn.microsoft.com/azure/aks/operator-best-practices-cluster-isolation)

**最終更新日:** 2026-04-11
