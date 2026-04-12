# 006: Foundry as Enterprise Control Plane

- Status: Accepted
- Date: 2026-04-12

## Context

エンタープライズ機能（RBAC, Identity, Observability, Eval, Content Safety）を自前で再実装するか Foundry に寄せるかを決める必要があった。

Foundry Agent Service は hosting / scaling / identity / observability / enterprise security を managed platform として提供している。自前で再実装すると Foundry との二重管理・乖離・保守コストが発生する。

## Decision

**Foundry に任せられるエンタープライズ機能は Foundry に寄せる。自前で再実装しない。**

| 領域 | Foundry に任せる | 自前に残す |
|------|----------------|-----------|
| 実行権限 | Agent Application RBAC | 相関 ID の保存 |
| Agent Identity | Foundry Agent Identity / Entra ID | Foundry identity ref の保持 |
| Tool 認証 | Foundry managed credentials / OBO | ローカル custom tool の approval |
| Observability | OTel + App Insights + Foundry Traces | execution_id と trace_id の相関 |
| Eval | MAF LocalEvaluator + Foundry Evals | dataset 規約、release gate 閾値 |
| Content Safety | Foundry Content Filter | domain-specific policy だけ middleware で追加 |
| Versioning | Foundry Agent versioning | 自前 AgentSpec version との対応 |

自前 platform は product-specific control plane に絞る: AgentSpec / WorkflowSpec / ToolSpec の source of truth、eval dataset 規約、Foundry sync。

## Consequences

- 自前 ACL を持たない。Azure RBAC のみ。
- 監査ログは OTel / Foundry Traces 主系。自前 DB には相関 ID のみ。
- eval engine は自前実装しない。MAF LocalEvaluator + Foundry Evals を使う。
- Foundry の機能更新に追従する必要がある。
- Foundry が提供しない domain-specific な制御だけ middleware で自前実装する。
