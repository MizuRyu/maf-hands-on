# コーディング規約・開発方針

## AI エージェント行動ルール（必ず守ること）

- **返答は必ず日本語で行う**
- **実装前に必ずユーザーの確認を取ること。確認なしに勝手に実装を開始してはならない**
- **実装前に計画のサマリーを提示し、ユーザーの許可を得てから実装を開始する**
- playground の実行はデフォルトで MockChatClient を使用する。ユーザーから明示的に「実際の LLM を使って」と指示された場合のみ `ALLOW_LLM_CALLS=true` を付与する
- `git commit` はユーザーから明示的に指示された場合のみ実行する
- `git push` はユーザーから明示的に指示された場合のみ実行する
- アーキテクチャの変更や全般的に関わる変更を行った場合は、`.agents/` 配下の関連ファイルを必ず最新状態に更新する
- 重要なアーキテクチャ上の意思決定を行った場合は、`docs/adr/` に連番 Markdown（例: `001-python-toolchain.md`）を作成または更新する

## アーキテクチャルール

### レイヤー構成

`src/platform/` は `domain → application → infrastructure → api` のレイヤード。
詳細は `ARCHITECTURE.md` を参照。

### 依存方向

- `domain/` で `azure.cosmos`, `opentelemetry` を import しない（`agent_framework` は OK）
- `platform/` から `playground/` を import しない
- `agents/`, `workflows/` は `agent_framework` を直接利用してよい
- `agents/`, `workflows/` は `infrastructure/` を直接 import しない
- `application/` が `agents/`, `workflows/`, `domain/`, `infrastructure/` を繋ぐ

## コーディング規約

- PEP 8 準拠（ruff でフォーマット）
- 型ヒントを必ず付与する（pyright basic）
- コメントは reason-only。
- I/O は async/await 必須
- ログは `get_logger` を使用（print 禁止）

## 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `TaskExecutor` |
| 変数・関数 | snake_case | `session_id`, `run_task()` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_MODEL` |
| ディレクトリ・ファイル | snake_case | `agents.py`, `workflow.py` |
| Agent 名 (`name=`) | kebab-case | `"summary-agent"` |
| Executor `id` | kebab-case | `"data-extractor"` |

## 型ヒント

### `from __future__ import annotations`

原則として全ファイルの先頭に記述する。

**例外**: MAF デコレータ使用ファイルでは使わない（詳細は `docs/agent-development-guide.md` 参照）。

### 引数

- 位置引数は 3 つ以下。4 つ以上は keyword-only（`*` 以降）にする
- `**kwargs` は原則使わない。使う場合は `client_kwargs: dict[str, Any] | None = None` のように明示

### 組み込み名のシャドーイング禁止

```
Good: input_data, type_name, format_str
Bad:  input, type, format, id, list
```

## コメント・Docstring（reason-only）

- **日本語**で記載する
- 「何をしたか」ではなく「**なぜそうするか**」だけを書く
- 型アノテーションがあれば Args / Returns は不要
- 不明な場合は推測で書かず実装者に確認する

## 非同期

I/O を伴う処理は必ず `async/await` を使用する。同期的なブロッキング呼び出しをイベントループ内で行わない。

## ログ

`print` は使わない。`get_logger` を使用する。

```python
from agent_framework import get_logger

logger = get_logger(__name__)
```

## API スキーマ命名規約

| 種別 | suffix | 定義場所 | 例 |
|------|--------|---------|-----|
| リクエスト | `*Request` | `api/schemas/` | `AgentSpecCreateRequest` |
| レスポンスデータ | `*ResponseData` | `api/schemas/` | `AgentSpecResponseData` |
| レスポンス (ラップ済み) | `*Response` | `api/routers/` | `AgentSpecResponse(BaseResponse[AgentSpecResponseData])` |
| 一覧レスポンス | `*ListResponse` | `api/routers/` | `AgentSpecListResponse(BaseResponse[list[AgentSpecResponseData]])` |

## 実装パターン

- リポジトリパターンを使用する（ABC は `domain/<context>/repositories/`、実装は `infrastructure/db/cosmos/repositories/`）
- domain 内の各 bounded context は `models/` + `repositories/` を必ず持つ
- `agent_framework` は `domain` を含む各層で利用してよい
- DI で注入し、直接インスタンス化しない
- API 層にビジネスロジックを書かない
- **CQRS**: Query (GET) は Router → Repository 直読み。Command (POST/PATCH/DELETE) は Router → Service → Repository

## テスト

- フレームワーク: pytest + pytest-asyncio（`asyncio_mode = "auto"`）
- テストは `tests/` に `src/` のミラー構造で配置
- 外部依存（Cosmos, LLM API 等）はモックに差し替え
- `playground/` のテストは任意

## よく使うコマンド

```bash
make lint       # ruff fix + format
make lint-check # CI 用チェック
make typecheck  # pyright
make test       # pytest
make test-cov   # カバレッジ付きテスト
make ci         # lint + type + test + dead + deps + security
make up         # Docker Compose 起動
make down       # Docker Compose 停止
```
