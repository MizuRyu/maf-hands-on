# 009: platform/core 導入とコロケーション原則

- Status: Accepted
- Date: 2026-04-12
- Supersedes: ADR-005 (部分的: agents/ 構成)

## Context

ADR-005 で `catalog/` を廃止し `agents/` + `workflows/` + `tools/` に昇格したが、`agents/` 内にプラットフォーム機構（factory, middleware, policy）と Agent テンプレートが混在していた。

また、Tool や Agent の配置ルールが明文化されておらず、共有と固有の区別が曖昧だった。

## Decision

### 1. `platform/core/` の導入

プラットフォーム機構を `agents/` から分離し `core/` に移動する。

```
agents/ (変更前)           core/ (変更後)
  factory.py         →      agent_factory.py
  middleware/        →      middleware/
  policy.py          →      policy.py
  config_loader.py   →      config_loader.py
  compaction.py      →      compaction.py
  _types.py          →      types.py (AgentMeta, WorkflowMeta)
```

`agents/` には Agent テンプレートのみが残る。

### 2. コロケーション原則

Tool・Agent の配置ルールを以下に統一する。

**ルール: 持ち主のディレクトリに置く。共有なら共有ディレクトリ。**

```
tools/                              # 共有 Tool（どの Agent からも利用可）
  datetime_tools.py
  notification_tools.py

agents/                             # 共有 Agent テンプレート
  expense_checker/
    agent.py
    tools.py                        # この Agent 専用 Tool
    prompts.py

workflows/                          # Workflow 定義
  approval_workflow/
    workflow.py
    executors/
    agents/                         # この Workflow 専用 Agent
      risk_assessor/
        agent.py
        tools.py                    # その Agent 専用 Tool
    contracts.py
```

| スコープ | Tool の場所 | Agent の場所 |
|---------|-----------|------------|
| プラットフォーム共有 | `tools/` | `agents/` |
| Agent 固有 | `agents/<name>/tools.py` | — |
| Workflow 固有 | — | `workflows/<name>/agents/` |

### 3. 全体構成

```
src/platform/
  core/               # プラットフォーム機構（Factory, Middleware, Policy）
  agents/             # 共有 Agent テンプレート
  workflows/          # Workflow 定義（固有 Agent/Tool 含む）
  tools/              # 共有 Tool
  eval/               # 評価フレームワーク
  domain/             # ドメインモデル + repo ABC
  application/        # ユースケース Service
  infrastructure/     # Cosmos, OTel, Foundry, Settings
  api/                # FastAPI
```

### 不採用としたもの

| 案 | 理由 |
|---|---|
| Feature Module（Vertical Slice） | プラットフォームとしてレイヤー境界が曖昧になる。複数チーム開発でルール違反が起きやすい |
| domain/ のフラット化（models.py 1ファイル） | 肥大化が見えているため context 分割は維持すべき |
| application/ の廃止 | Workflow 実行管理のように実体のあるオーケストレーションを持つ Service が存在する |

## Consequences

- `agents/` が純粋にテンプレート置き場になり、platform 機構との混在が解消
- コロケーション原則により Tool/Agent の配置判断が明確化
- レイヤードアーキテクチャは維持されるため、依存方向の物理的な強制は変わらない
