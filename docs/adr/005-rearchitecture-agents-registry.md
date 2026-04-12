# 005: リアーキテクチャ（agents/ + registry/ 構成）

- Status: Accepted
- Date: 2026-04-11
- Supersedes: ADR-002, ADR-004

## Context

Phase 0 実装を経て以下の問題が顕在化した:

1. `catalog/` がレイヤードアーキテクチャのどこにも属さない
2. `infrastructure/maf/` の PlatformAgentFactory は I/O アダプタではなく composition コード
3. `domain/specs/` + `domain/repository/` が分離しすぎで見通しが悪い
4. AgentMeta と AgentSpec の関係が未定義

## Decision

### 構造変更

- `catalog/` 廃止 → `agents/` + `workflows/` + `tools/` に昇格（platform 直下）
- `infrastructure/maf/` → `agents/` 内に統合（builder, policy, middleware）
- `domain/specs/` → `domain/registry/`
- `domain/runs/` → `domain/execution/`
- `domain/repository/` → 各 bounded context の `repositories/` に分散
- `usecases/` 廃止

### domain 内部ルール

全 bounded context で `models/` + `repositories/` を必ず持つ。

### 命名

- クラス名（AgentSpec, AgentSpecRepository 等）は据置
- AgentMeta は残す（Foundry export / scaffold 用）

## Consequences

- agents/ が「Agent を作ること」に関する全コードを集約し、見通しが改善
- domain/ の各 context が自己完結し、将来 services/ や events/ を追加しやすい
- infrastructure/ は純粋な I/O アダプタのみになり、責務が明確化
