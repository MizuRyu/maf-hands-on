# Microsoft Agent Framework 1.0.0: パッケージ状況・依存バージョン・開発支援ツール調査

> 調査日: 2026-04-05

---

## Executive Summary

Microsoft Agent Framework (MAF) が Python 向け `1.0.0` 安定版をリリースした。ただし **stable (`released`) なのは4パッケージのみ**であり、`agent-framework-azure-cosmos` は引き続き **`beta`** ステータス（`1.0.0b260402`）である。`opentelemetry-exporter-otlp-proto-grpc>=1.40.0` は MAF 開発環境の dev 依存として `opentelemetry-sdk==1.40.0` が採用されており、**1.40.0 を使用するのが正しい選択**。MAF 開発支援については、リポジトリ内の GitHub Copilot Agent Skills（`.github/skills/`）、MCP プロトコル対応、実験的 `SKILLS` 機能など複数のツールが用意されている。

---

## 1. MAF 1.0.0 に含まれる stable パッケージ一覧

`PACKAGE_STATUS.md` によると、`released`（stable）なパッケージは以下の **4つ**のみ[^1]：

| パッケージ名 | パス | ステータス | バージョン |
|---|---|---|---|
| `agent-framework` | `python/` | **released** | `1.0.0` |
| `agent-framework-core` | `python/packages/core` | **released** | `1.0.0` |
| `agent-framework-openai` | `python/packages/openai` | **released** | `1.0.0` |
| `agent-framework-foundry` | `python/packages/foundry` | **released** | `1.0.0` |

残りのパッケージはすべて `beta` ステータスであり、`--pre` フラグが必要。

### 全パッケージのステータス（beta含む）

| パッケージ名 | ステータス |
|---|---|
| `agent-framework-a2a` | beta |
| `agent-framework-ag-ui` | beta |
| `agent-framework-anthropic` | beta |
| `agent-framework-azure-ai-search` | beta |
| **`agent-framework-azure-cosmos`** | **beta** |
| `agent-framework-azurefunctions` | beta |
| `agent-framework-bedrock` | beta |
| `agent-framework-chatkit` | beta |
| `agent-framework-claude` | beta |
| `agent-framework-copilotstudio` | beta |
| `agent-framework-declarative` | beta |
| `agent-framework-devui` | beta |
| `agent-framework-durabletask` | beta |
| `agent-framework-foundry-local` | beta |
| `agent-framework-github-copilot` | beta |
| `agent-framework-lab` | beta |
| `agent-framework-mem0` | beta |
| `agent-framework-ollama` | beta |
| `agent-framework-orchestrations` | beta |
| `agent-framework-purview` | beta |
| `agent-framework-redis` | beta |

---

## 2. `agent-framework-azure-cosmos` の現状

### バージョン

GitHub main ブランチの `pyproject.toml` より[^2]：

```toml
version = "1.0.0b260402"   # beta (2026-04-02 付け)
```

**MAF 1.0.0 stable には含まれていない。** `PACKAGE_STATUS.md` でも `beta` と明記。

### インストール

```bash
# beta のためプレリリースフラグが必要
pip install agent-framework-azure-cosmos --pre
```

### 依存関係

```toml
dependencies = [
    "agent-framework-core>=1.0.0,<2",   # MAF core 1.0.0 stable が必要
    "azure-cosmos>=4.3.0,<5",
]
```

### 使用例

```python
from azure.identity.aio import DefaultAzureCredential
from agent_framework_azure_cosmos import CosmosHistoryProvider

provider = CosmosHistoryProvider(
    endpoint="https://<account>.documents.azure.com:443/",
    credential=DefaultAzureCredential(),
    database_name="agent-framework",
    container_name="chat-history",
)
```

---

## 3. `opentelemetry-exporter-otlp-proto-grpc` の推奨バージョン

### MAF における OpenTelemetry の依存定義

| ファイル | 設定 | 値 |
|---|---|---|
| `python/packages/core/pyproject.toml` | runtime deps | `opentelemetry-api>=1.39.0,<2` |
| `python/pyproject.toml` (dev group) | dev deps | `opentelemetry-sdk==1.40.0` |

MAF 開発環境自体が `opentelemetry-sdk==1.40.0` を pin しているため[^3]、**`opentelemetry-exporter-otlp-proto-grpc==1.40.0` の使用が推奨**。

### バージョン履歴（参考）

| バージョン | リリース日 |
|---|---|
| `1.40.0` | 2026-03-04（最新） |
| `1.39.1` | 2025-12-11 |
| `1.38.0` | 2025-10-xx |

### 推奨 `pyproject.toml` 設定

```toml
dependencies = [
    "agent-framework==1.0.0",
    "agent-framework-azure-cosmos>=1.0.0b0,<2",   # beta
    "opentelemetry-exporter-otlp-proto-grpc>=1.40.0,<2",
    "opentelemetry-sdk>=1.40.0,<2",
]

[tool.uv]
prerelease = "if-necessary-or-explicit"   # beta パッケージのために必要
```

---

## 4. MAF の開発支援ツール・Agent Skills・MCP

### 4.1 リポジトリ内蔵の GitHub Copilot Agent Skills

MAF は `.github/skills/` ディレクトリに Copilot 向けの **Agent Skills** を持つ[^4]：

| スキル名 | 内容 |
|---|---|
| `python-development` | コーディング規約、型アノテーション、ドックストリング、パフォーマンスガイド |
| `python-testing` | テスト構造、fixtures、asyncio モード |
| `python-code-quality` | リント、フォーマット、型チェック、pre-commit フック |
| `python-feature-lifecycle` | パッケージ vs フィーチャーのライフサイクル管理、デコレータ |
| `python-package-management` | モノレポ構造、lazy loading、バージョン管理、新パッケージ追加 |
| `python-samples` | サンプルファイル構造、PEP 723、ドキュメントガイドライン |

**使い方**: GitHub Copilot（Copilot CLI / VS Code）が `AGENTS.md` 経由でスキルを自動参照。各スキルフォルダの `SKILL.md` に YAML フロントマターと詳細指示が記載されている。

### 4.2 MCP (Model Context Protocol) サポート

MAF core の optional deps で MCP が定義されている[^5]：

```toml
[project.optional-dependencies]
all = [
    "mcp>=1.24.0,<2",
    ...
]
```

dev 環境では `mcp[ws]==1.26.0` を使用。

#### MCP を使った開発フロー

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

# MCP ツールをエージェントに接続する例
agent = Agent(
    client=OpenAIChatClient(),
    instructions="You are a helpful assistant.",
    # mcp_server_url="http://localhost:8080/mcp" など
)
```

#### MAF エージェント自体を MCP ツールとして公開

MAF エージェントを MCP Server として公開し、他のエージェントや Copilot から呼び出すことも可能[^6]。

### 4.3 MAF 実験的 SKILLS 機能（`agent-framework-core` 内）

`PACKAGE_STATUS.md` に記載されている `SKILLS` フィーチャー[^1]：

```
Experimental features:
  SKILLS:
    - agent-framework-core: Skill, SkillResource, SkillScript, SkillScriptRunner,
      SkillsProvider (from agent_framework/_skills.py)
```

MAF 自体に **エージェントがスキル（専門タスク）を実行・管理するための API** が実験的に組み込まれている。

```python
from agent_framework import Skill, SkillsProvider  # experimental
```

### 4.4 GitHub Copilot SDK との統合

`agent-framework-github-copilot` パッケージ（beta）で GitHub Copilot をエージェントとして利用可能[^7]：

```bash
pip install agent-framework-github-copilot --pre
```

```python
from agent_framework.github import GitHubCopilotAgent

agent = GitHubCopilotAgent(
    default_options={"instructions": "You are a helpful assistant."}
)
```

### 4.5 VS Code / Copilot における MCP 活用

| ツール | 用途 |
|---|---|
| VS Code MCP 拡張設定 | `mcp.json` でローカル/リモート MCP サーバーを管理 |
| Copilot Agent Mode | MCP ツールを Copilot チャットから呼び出し |
| [microsoft/skills](https://github.com/microsoft/skills) | 公式スキルパック・MCP サーバーのコレクション |

---

## 5. 依存関係全体マップ

```
agent-framework 1.0.0 (stable)
  └── agent-framework-core[all] == 1.0.0
        ├── opentelemetry-api >= 1.39.0, < 2
        ├── pydantic >= 2, < 3
        ├── typing-extensions >= 4.15.0, < 5
        └── [optional] mcp >= 1.24.0, < 2

agent-framework-azure-cosmos 1.0.0b260402 (beta)
  ├── agent-framework-core >= 1.0.0, < 2
  └── azure-cosmos >= 4.3.0, < 5

opentelemetry-exporter-otlp-proto-grpc 1.40.0
  └── opentelemetry-api ~= 1.40.0   (同バージョン系列)
```

---

## 6. このプロジェクトへの推奨 pyproject.toml

現在の `pyproject.toml`:
```toml
dependencies = ["agent-framework==1.0.0"]

[tool.uv]
prerelease = "allow"
```

**推奨追加設定**:
```toml
dependencies = [
    "agent-framework==1.0.0",
    "agent-framework-azure-cosmos>=1.0.0b0,<2",
    "opentelemetry-exporter-otlp-proto-grpc>=1.40.0,<2",
    "opentelemetry-sdk>=1.40.0,<2",
]

[tool.uv]
prerelease = "if-necessary-or-explicit"   # "allow" より安全
```

---

## Confidence Assessment

| 項目 | 確信度 | 根拠 |
|---|---|---|
| MAF 1.0.0 stable パッケージ一覧 | **高** | GitHub `PACKAGE_STATUS.md` を直接確認[^1] |
| `agent-framework-azure-cosmos` がbeta | **高** | `pyproject.toml` の `version = "1.0.0b260402"`[^2] と `PACKAGE_STATUS.md`[^1] |
| `opentelemetry-sdk==1.40.0` が MAF 推奨 | **高** | MAF `python/pyproject.toml` dev deps を直接確認[^3] |
| MCP バージョン `mcp>=1.24.0` | **高** | MAF core `pyproject.toml` optional deps を直接確認[^5] |
| Agent Skills のスキル一覧 | **高** | GitHub `.github/skills/` ディレクトリ直接確認[^4] |
| GitHub Copilot SDK 統合 | **中** | Web 検索＋devblogs.microsoft.com 情報[^7] |

---

## Footnotes

[^1]: [`python/PACKAGE_STATUS.md`](https://github.com/microsoft/agent-framework/blob/main/python/PACKAGE_STATUS.md) — パッケージステータス表（直接確認）

[^2]: [`python/packages/azure-cosmos/pyproject.toml`](https://github.com/microsoft/agent-framework/blob/main/python/packages/azure-cosmos/pyproject.toml) — `version = "1.0.0b260402"`, `beta` status confirmed

[^3]: [`python/pyproject.toml`](https://github.com/microsoft/agent-framework/blob/main/python/pyproject.toml) — dev deps: `"opentelemetry-sdk==1.40.0"`, `"mcp[ws]==1.26.0"`

[^4]: [`python/.github/skills/`](https://github.com/microsoft/agent-framework/tree/main/python/.github/skills) — Agent Skills ディレクトリ: python-development, python-testing, python-code-quality, python-feature-lifecycle, python-package-management, python-samples

[^5]: [`python/packages/core/pyproject.toml`](https://github.com/microsoft/agent-framework/blob/main/python/packages/core/pyproject.toml) — optional deps: `mcp>=1.24.0,<2`, runtime: `opentelemetry-api>=1.39.0,<2`

[^6]: [Microsoft Agent Framework: Exposing an Agent as MCP Tool](https://jamiemaguire.net/index.php/2026/02/08/microsoft-agent-framework-exposing-an-existing-ai-agent-as-an-mcp-tool/)

[^7]: [Build AI Agents with GitHub Copilot SDK and MAF](https://devblogs.microsoft.com/agent-framework/build-ai-agents-with-github-copilot-sdk-and-microsoft-agent-framework/) — devblogs.microsoft.com

[^8]: [PyPI: opentelemetry-exporter-otlp-proto-grpc](https://pypi.org/project/opentelemetry-exporter-otlp-proto-grpc/) — v1.40.0 released 2026-03-04

[^9]: [microsoft/skills GitHub](https://github.com/microsoft/skills) — 公式スキルパック・MCP サーバーコレクション

[^10]: [GitHub Copilot Agent Skills Changelog](https://github.blog/changelog/2025-12-18-github-copilot-now-supports-agent-skills/) — 2025-12-18
