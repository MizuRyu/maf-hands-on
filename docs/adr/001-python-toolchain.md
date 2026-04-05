# 001: Python ツールチェーンの選定

- Status: Accepted
- Date: 2026-04-05

## Context

MAF 1.0.0 の検証用リポジトリをAI駆動（Claude Code等）で開発する。AI生成コードの品質を厳密に担保するため、linter・型チェッカー・テスト・セキュリティ等のツールチェーンを統一的に選定する必要があった。

## Decision

以下のツール構成を採用する。

| カテゴリ | ツール | 役割 |
|---------|--------|------|
| パッケージ管理 | **uv** | 依存管理・仮想環境・Python版管理 |
| Linter + Formatter | **ruff** | flake8/black/isort/bandit等を統合代替 |
| 型チェッカー | **pyright** (basic) | 静的型チェック。Pylance バックエンド |
| テスト | **pytest** | pytest-asyncio, pytest-cov, pytest-randomly |
| デッドコード検出 | **vulture** | 未使用関数・クラス・変数の検出 |
| 未使用依存検出 | **deptry** | pyproject.toml の依存整合性チェック |
| 依存脆弱性 | **pip-audit** | 既知脆弱性の検出 |
| シークレット検出 | **detect-secrets** | APIキー等の混入防止 |
| Git フック | **pre-commit** | コミット前の自動チェック |

### 不採用としたもの

| ツール | 理由 |
|--------|------|
| black / isort | ruff で完全代替 |
| flake8 | ruff で完全代替 |
| mypy | pyright を採用。プラグイン不要な構成のため |
| bandit | ruff S ルールで大半カバー |
| Hypothesis | MAF エージェント系では使いどころが限定的。必要時に追加 |
| mutmut | テストが揃ってから検討 |
| just | CLAUDE.md にコマンド記載で十分 |
| Faker | 現時点では不要。必要時に追加 |

## Consequences

- ruff 1つで lint + format + import sort + security check をカバーし、ツール数を最小化
- pyright basic + ruff ANN ルールで型安全性を担保
- pre-commit（ruff, pyright, detect-secrets）→ CI（+ vulture, deptry, pip-audit, pytest）の多層防御
- vulture + deptry でコード・依存の両面から不要物を検出
- deptry, vulture, pip-audit は CI のみ（pre-commit には入れない。全体スキャンやネットワーク依存のため）
