# 003: Cosmos DB 永続化層の設計

- Status: Accepted
- Date: 2025-07-18

## Context

MAF ベースのエージェント管理基盤で、仕様（Agent / Tool / Workflow）・実行状態・セッション・ユーザーの永続化が必要。
Cosmos DB NoSQL API を採用し、9 コンテナ構成でドメインモデルを格納する。
設計上の主要な判断事項が 13 件あり、一貫した方針を定める。

## Decision

1. **レイヤー構成**: ドメイン層に ABC（リポジトリインターフェース）、インフラ層に Cosmos DB 実装を配置
2. **ETag**: インフラ層の関心事。`update(entity, *, etag=None)` でオプション渡し
3. **ISP**: SpecRepository を AgentSpec / ToolSpec / WorkflowSpec の 3 ABC に分離
4. **シリアライズ**: `_to_document()` / `_from_document()` をインフラ層に閉じる
5. **共通ヘルパー**: BaseCosmosRepository は作らず、`cosmos_helpers.py`（error_handler + paginate）で共通化
6. **ページネーション**: continuation token ベース。戻り値は `tuple[list[T], str | None]`
7. **CRUD 命名**: `create`（→ create_item）+ `update`（→ replace_item）。`save` は使わない
8. **ドメイン例外**: NotFoundError / ConflictError / ConcurrencyError / ValidationError
9. **CheckpointStorage**: MAF Protocol 準拠。PK は `/checkpointId`（フラット）
10. **Execution + Step 分離**: 別コンテナ・別 PK のため、別リポジトリに
11. **with_status()**: frozen dataclass 上で `dataclasses.replace()` をラップ
12. **Lazy migrate-on-read**: スキーマ移行は読み取り時に変換（write-back しない）
13. **コンテナ作成**: `create_container_if_not_exists` で冪等

## Consequences

- 7 リポジトリ ABC + 7 Cosmos 実装 + CheckpointStorage 実装が生成される
- ドメイン層はインフラ非依存（テスト容易）
- ETag によるオプティミスティック排他制御が利用可能
- 将来の DB 変更時はインフラ層の差し替えのみで対応可能
