**調査日:** 2026-04-05

# Python AI駆動開発ツールチェーン調査

AI駆動開発（Claude Code等）で**厳密にコード品質を担保する**ためのPythonツールチェーンを網羅的に調査する。
TypeScriptにおけるknipのような「モダンで厳密な」ツールをPythonでも実現することを目標とする。

---

## 1. Linter

### 主要ツール一覧

| ツール | Stars | 最新ver | 最終リリース | 言語 | 状態 |
|--------|-------|---------|------------|------|------|
| **ruff** | ~46,800 | v0.15.9 | 2026-04-02 | Rust | **推奨・デファクト** |
| **pylint** | ~5,700 | v4.0.5 | 2026-02-20 | Python | 補完用 |
| **flake8** | ~3,800 | - | 2025-12 | Python | レガシー（ruffで代替） |
| **pyflakes** | ~1,400 | - | 2025-06 | Python | レガシー |
| **pycodestyle** | ~5,200 | - | 2025-12 | Python | レガシー |
| **bandit** | ~7,900 | v1.9.4 | 2026-02-25 | Python | ruff S ルールで大半代替可 |
| **vulture** | ~4,400 | - | 2026-03 | Python | デッドコード検出（独自価値あり） |
| **Fixit** (Meta) | ~700 | - | 2026-04 | Python | auto-fix特化。ニッチ |
| **refurb** | ~2,500 | - | 2026-04 | Python | ruff FURBで一部取り込み済 |

### ruff が置き換えるツール群

ruff 1つで以下のツールをほぼ完全に代替できる:
- flake8 + 全プラグイン → F, E, W, B, S, C4, SIM, PT, ... 等60カテゴリ
- isort → I ルール
- pyupgrade → UP ルール
- pydocstyle → D ルール
- bandit → S ルール
- autoflake → F401 (未使用import自動修正)
- eradicate → ERA ルール (コメントアウトコード検出)

### ruff 全ルールカテゴリ（2026年4月 / v0.15.9時点）

| プレフィックス | 元ツール | 概要 |
|------------|---------|------|
| **F** | Pyflakes | 未使用import、未定義変数等 |
| **E/W** | pycodestyle | PEP 8 エラー/警告 |
| **C90** | mccabe | 循環的複雑度 |
| **I** | isort | import並び順 |
| **N** | pep8-naming | 命名規則 |
| **D** | pydocstyle | Docstringスタイル |
| **UP** | pyupgrade | Pythonバージョンアップグレード提案 |
| **ANN** | flake8-annotations | 型アノテーション欠如 |
| **ASYNC** | flake8-async | async/awaitアンチパターン |
| **S** | flake8-bandit | セキュリティ問題 |
| **BLE** | flake8-blind-except | 裸のexcept禁止 |
| **FBT** | flake8-boolean-trap | bool引数のアンチパターン |
| **B** | flake8-bugbear | よくあるバグパターン |
| **A** | flake8-builtins | 組み込み名のシャドーイング |
| **COM** | flake8-commas | 末尾カンマ |
| **C4** | flake8-comprehensions | 内包表記の最適化 |
| **DTZ** | flake8-datetimez | タイムゾーン未指定のdatetime |
| **T10** | flake8-debugger | デバッガ残留 |
| **EM** | flake8-errmsg | 例外メッセージのフォーマット |
| **FA** | flake8-future-annotations | `from __future__ import annotations` |
| **ISC** | flake8-implicit-str-concat | 暗黙の文字列結合 |
| **ICN** | flake8-import-conventions | import別名規則 |
| **LOG** | flake8-logging | loggingの誤使用 |
| **G** | flake8-logging-format | loggingフォーマット |
| **INP** | flake8-no-pep420 | `__init__.py`欠如 |
| **PIE** | flake8-pie | 冗長コード検出 |
| **T20** | flake8-print | print文の残留 |
| **PYI** | flake8-pyi | .pyiスタブファイル |
| **PT** | flake8-pytest-style | pytestスタイル |
| **Q** | flake8-quotes | クォート統一 |
| **RSE** | flake8-raise | raiseの書き方 |
| **RET** | flake8-return | returnの最適化 |
| **SLF** | flake8-self | プライベートメンバアクセス |
| **SLOT** | flake8-slots | `__slots__`推奨 |
| **SIM** | flake8-simplify | コード簡略化 |
| **TID** | flake8-tidy-imports | importの整理 |
| **TC** | flake8-type-checking | TYPE_CHECKINGブロック最適化 |
| **ARG** | flake8-unused-arguments | 未使用引数 |
| **PTH** | flake8-use-pathlib | os.path → pathlib移行 |
| **TD** | flake8-todos | TODOコメント形式 |
| **FIX** | flake8-fixme | FIXME/TODO/HACK検出 |
| **ERA** | eradicate | コメントアウトされたコード |
| **PD** | pandas-vet | pandasのアンチパターン |
| **PGH** | pygrep-hooks | 汎用正規表現ルール |
| **PL** | Pylint | Pylint互換ルール (PLC/PLE/PLR/PLW) |
| **TRY** | tryceratops | try/exceptのアンチパターン |
| **FLY** | flynt | f-string移行 |
| **NPY** | NumPy-specific | NumPy非推奨API |
| **FAST** | FastAPI | FastAPI固有ルール |
| **AIR** | Airflow | Airflow固有ルール |
| **PERF** | Perflint | パフォーマンス最適化 |
| **FURB** | refurb | Pythonic書き換え提案 |
| **DOC** | pydoclint | docstringパラメータ整合性 |
| **RUF** | Ruff-specific | Ruff独自ルール |

**合計: 約60カテゴリ、900以上のルール**

---

## 2. Formatter

| ツール | Stars | 最新ver | 速度 | 状態 |
|--------|-------|---------|------|------|
| **ruff format** | (ruffに含む) | v0.15.9 | 最速 | **推奨** |
| **black** | ~41,400 | v26.3.1 | 速い | 安定だがruff formatに移行傾向 |
| **isort** | ~6,900 | - | 普通 | ruff Iルールで完全代替 |
| **yapf** (Google) | ~14,000 | - | 普通 | レガシー |
| **autopep8** | ~4,700 | - | 普通 | レガシー |

**結論**: ruff format がBlack互換（99.7%一致）でより高速。新規プロジェクトでは ruff format 一択。

---

## 3. 型チェッカー（Static Type Checker）

| ツール | Stars | 最新ver | 速度 | 状態 |
|--------|-------|---------|------|------|
| **mypy** | ~20,300 | v1.20.0 | 遅い | 最も成熟。プラグイン最充実 |
| **pyright** (MS) | ~15,400 | v1.1.408 | 速い | strict最も厳格。Pylanceバックエンド |
| **ty** (Astral) | ~18,200 | v0.0.28 | 最速(10-100x) | **ベータ**。将来のデファクト候補 |
| **pyre** (Meta) | ~7,200 | - | 速い | Pysa(taint分析)が独自の強み |
| **pytype** (Google) | ~5,000 | - | 遅い | Linuxのみ。ニッチ |
| **basedpyright** | ~2,000 | - | 速い | pyrightフォーク。より厳格 |

### 厳密さの比較

```
pyright strict > basedpyright > mypy strict > ty (beta) > pyre > pytype
```

### strict設定

**mypy:**
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-cast", "truthy-bool", "truthy-iterable", "unused-awaitable"]
```

**pyright:**
```toml
[tool.pyright]
typeCheckingMode = "strict"
```

**ty (ベータ):**
```toml
[tool.ty.rules]
all = "error"
```

### 推奨戦略

- **安定重視**: mypy strict（プラグインエコシステムが最も充実: Django, Pydantic, SQLAlchemy等）
- **最大厳密**: mypy strict + pyright strict 併用
- **将来への布石**: ty をウォッチしつつ、安定版到達後にruff + uv + ty のAstral統一環境へ移行

---

## 4. Dead Code / 未使用検出（knip相当）

TypeScriptの[knip](https://github.com/webpro-nl/knip)は未使用ファイル・エクスポート・依存・型を包括的に検出する。Pythonには単一の完全代替はないが、以下の組み合わせで同等以上をカバーできる。

| knipの機能 | Pythonツール | Stars | 説明 |
|---|---|---|---|
| 未使用コード/関数/クラス | **vulture** | ~4,400 | 信頼度スコア付き。最も成熟 |
| 未使用コード | **deadcode** | ~160 | 13種パターン検出+`--fix`自動削除 |
| 未使用import | **ruff (F401)** | - | 自動修正可能。ruff単体で対応 |
| 未使用依存パッケージ | **deptry** | ~1,300 | Rust製。DEP001(未宣言)/DEP002(未使用)/DEP004(dev誤用) |
| 未使用依存 | **creosote** | - | PEP-621, Poetry, Pipenv, PDM対応 |
| コメントアウトコード | **ruff (ERA)** | - | eradicate互換 |

### 設定例

```toml
[tool.vulture]
min_confidence = 80
paths = ["src"]
exclude = ["src/migrations/"]

[tool.deptry]
extend_exclude = ["scripts", "docs"]
```

**結論**: `vulture + deptry + ruff (F401, ERA)` でknipの主要機能をカバー。完全に同一ではないが、実用上十分。

---

## 5. セキュリティスキャナー

| ツール | Stars | 対象 | 推奨度 |
|--------|-------|------|--------|
| **ruff (Sルール)** | - | ソースコード | banditの大半を内包。ruff使用なら追加不要 |
| **bandit** | ~7,900 | ソースコード | ruffでカバーされない高度ルール用 |
| **semgrep** | ~14,700 | ソースコード(多言語) | カスタムルール最強。SAST |
| **pip-audit** | ~1,240 | 依存パッケージ | OSV DB使用。無料。**推奨** |
| **safety** | ~1,970 | 依存パッケージ | 商用利用は有料 |
| **trivy** | ~34,400 | コンテナ/依存/IaC | 最も包括的 |
| **grype** | ~11,900 | コンテナ/依存 | Syftと連携 |
| **detect-secrets** (Yelp) | - | シークレット | .secrets.baselineでFP管理 |

### 推奨構成

- **ソースコード**: ruff Sルール（bandit大半をカバー）
- **依存脆弱性**: pip-audit（無料・正確）
- **シークレット**: detect-secrets（pre-commit hook）
- **コンテナ**: trivy（CI/CD）

---

## 6. Docstring / ドキュメント品質

| ツール | Stars | 状態 | 説明 |
|--------|-------|------|------|
| **ruff (D)** | - | **推奨** | pydocstyle互換。全ルール実装 |
| **ruff (DOC)** | - | **推奨** | pydoclint互換。パラメータ整合性 |
| **interrogate** | ~660 | アクティブ | docstringカバレッジ計測。`--fail-under 80` |
| **docsig** | ~42 | アクティブ | シグネチャとdocstringの整合性 |
| **pydocstyle** | ~1,120 | **メンテ停止** | ruff Dに移行 |
| **darglint** | ~480 | **メンテ停止** | ruff DOCに移行 |

**ruff (D+DOC)** がpydocstyle/darglintの後継。interrogateはruffにない「カバレッジ計測」機能で補完価値あり。

---

## 7. 複雑度・品質メトリクス

| ツール | Stars | 特徴 |
|--------|-------|------|
| **ruff (C90)** | - | mccabe循環的複雑度。`max-complexity`設定可 |
| **complexipy** | ~660 | Rust製。**認知的複雑度**（SonarSource方式）。人間の理解度に近い |
| **radon** | ~1,960 | CC/MI/Halstead。最も多機能 |
| **xenon** | ~270 | radonベースのCIゲート |
| **wily** | ~1,270 | Git履歴と連携した複雑度の時系列トラッキング |

**推奨**: ruff C90（循環的複雑度） + complexipy（認知的複雑度）の併用。

---

## 8. パッケージ管理

| ツール | Stars | 速度 | PEP 621 | Python管理 | モノレポ | 推奨度 |
|--------|-------|------|---------|-----------|---------|--------|
| **uv** | ~50,000+ | 極めて高速(Rust) | 完全 | 内蔵 | workspace対応 | **最優先** |
| **Poetry** | ~32,000 | 遅め | v2で改善 | なし | なし | レガシー向け |
| **PDM** | ~8,000 | 中程度 | 完全 | なし | なし | ニッチ |
| **Hatch** | ~6,000 | 中程度 | 完全 | なし | 環境マトリクス | PyPA公式寄り |

**結論**: 2026年の新規プロジェクトは **uv一択**。pip, pip-tools, virtualenv, pyenv, pipxの機能を統合。

### uv workspace（モノレポ）

```toml
# ルート pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]

# packages/api/pyproject.toml
[tool.uv.sources]
core = { workspace = true }
```

---

## 9. テスト

### フレームワーク

| ツール | Stars | 用途 |
|--------|-------|------|
| **pytest** | ~13,000 | デファクト。プラグイン最充実 |
| **Hypothesis** | ~7,500 | プロパティベーステスト。AI駆動と相性◎ |
| **mutmut** | ~2,500 | ミューテーションテスト。テスト品質検証 |

### 主要pytestプラグイン

| プラグイン | Stars | 用途 |
|-----------|-------|------|
| **pytest-xdist** | ~1,500 | テスト並列実行 (`-n auto`) |
| **pytest-cov** | ~1,800 | カバレッジ計測 |
| **pytest-sugar** | ~1,300 | 美しい出力 |
| **pytest-randomly** | ~600 | テスト順序ランダム化 |
| **pytest-benchmark** | ~1,300 | パフォーマンステスト |
| **pytest-asyncio** | ~1,500 | asyncテスト |
| **pytest-mock** | ~1,900 | mockラッパー |
| **pytest-timeout** | ~800 | タイムアウト設定 |
| **inline-snapshot** | ~500 | インラインスナップショット。LLM生成コードの回帰テストに有用 |

### AI駆動テスト戦略

- **TDD**: テスト→実装の順序でLLMに指示。テスト仕様が「要件」の役割を果たす
- **Property-based Testing**: Hypothesisで不変条件を定義し、反例を自動探索
- **Mutation Testing**: mutmutでLLM生成テストの質を客観検証

---

## 10. pre-commit

### 推奨 .pre-commit-config.yaml

```yaml
repos:
  # === 汎用 ===
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key
      - id: check-ast

  # === Ruff (lint + format) ===
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.x
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # === 型チェック ===
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.20.x
    hooks:
      - id: mypy
        additional_dependencies: []  # 必要に応じてスタブ追加

  # === セキュリティ ===
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.x
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # === 未使用依存検出 ===
  - repo: https://github.com/fpgmaas/deptry
    rev: 0.25.x
    hooks:
      - id: deptry

  # === pyproject.toml整形 ===
  - repo: https://github.com/tox-dev/pyproject-fmt
    rev: v2.x
    hooks:
      - id: pyproject-fmt

  # === デッドコード ===
  - repo: local
    hooks:
      - id: vulture
        name: vulture
        entry: vulture src --min-confidence 80
        language: python
        types: [python]
```

---

## 11. タスクランナー

| ツール | Stars | 言語 | 特徴 |
|--------|-------|------|------|
| **just** | ~24,000 | Rust | Makefileのモダン版。**推奨** |
| **Taskfile (go-task)** | ~12,000 | Go | YAMLベース |
| **Makefile** | - | - | 歴史的標準。タブ問題あり |
| **nox** | ~1,300 | Python | テスト環境マトリクス向け |

### justfile例

```just
default:
    @just --list

lint:
    uv run ruff check .
    uv run ruff format --check .

fix:
    uv run ruff check --fix .
    uv run ruff format .

typecheck:
    uv run mypy src/

test *ARGS:
    uv run pytest {{ARGS}}

dead:
    uv run vulture src --min-confidence 80

deps:
    uv run deptry src

security:
    uv run pip-audit

ci: lint typecheck test dead deps security
```

---

## 12. 環境変数・設定管理

| ツール | Stars | 特徴 |
|--------|-------|------|
| **pydantic-settings** | ~800 | 型安全+バリデーション。**最推奨** |
| **python-dotenv** | ~7,500 | .env読み込みの定番。シンプル |
| **dynaconf** | ~4,000 | 多層設定管理(env/TOML/YAML/Redis) |

---

## 13. Claude Codeフック（リアルタイム品質ゲート）

Claude Codeのフック機能でファイル書き込み後に自動lint/type checkを実行できる。

### settings.json 設定例

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-python.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### .claude/hooks/check-python.sh

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path')

if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
  exit 0
fi

ERRORS=""
RUFF_OUTPUT=$(ruff check "$FILE_PATH" 2>&1)
[ $? -ne 0 ] && ERRORS="$ERRORS\n--- Ruff ---\n$RUFF_OUTPUT"

MYPY_OUTPUT=$(mypy "$FILE_PATH" 2>&1)
[ $? -ne 0 ] && ERRORS="$ERRORS\n--- Mypy ---\n$MYPY_OUTPUT"

if [ -n "$ERRORS" ]; then
  echo -e "$ERRORS" >&2
  jq -n '{ decision: "block", reason: "Lint/type check failed." }'
else
  exit 0
fi
```

### 品質ゲートの全体像

```
AIのコード生成
    ↓
[CLAUDE.md] ──── AIへの行動指示
    ↓
[Claude Code Hooks] ──── PostToolUse で即座にlint/type check → ブロック → AI修正
    ↓
[pre-commit] ──── ruff, mypy, deptry, vulture, detect-secrets
    ↓
[CI (GitHub Actions)] ──── 全チェック + テスト + カバレッジ + pip-audit
    ↓
[Mutation Testing] ──── mutmutでテスト品質検証
    ↓
マージ
```

---

## 14. pyproject.toml 厳密設定（統合例）

```toml
[project]
name = "maf-hands-on"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=6.0",
    "pytest-xdist>=3.0",
    "pytest-randomly>=3.0",
    "pytest-asyncio>=0.24",
    "hypothesis>=6.0",
    "ruff>=0.15",
    "mypy>=1.20",
    "vulture>=2.0",
    "deptry>=0.25",
    "pip-audit>=2.0",
    "pre-commit>=4.0",
    "complexipy>=0.6",
]

# ===== Ruff =====
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "F",      # Pyflakes
    "E", "W", # pycodestyle
    "C90",    # mccabe complexity
    "I",      # isort
    "N",      # pep8-naming
    "D",      # pydocstyle
    "UP",     # pyupgrade
    "ANN",    # flake8-annotations
    "ASYNC",  # flake8-async
    "S",      # flake8-bandit (security)
    "BLE",    # flake8-blind-except
    "FBT",    # flake8-boolean-trap
    "B",      # flake8-bugbear
    "A",      # flake8-builtins
    "COM",    # flake8-commas
    "C4",     # flake8-comprehensions
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "EM",     # flake8-errmsg
    "FA",     # flake8-future-annotations
    "ISC",    # implicit-str-concat
    "ICN",    # flake8-import-conventions
    "LOG",    # flake8-logging
    "G",      # flake8-logging-format
    "INP",    # flake8-no-pep420
    "PIE",    # flake8-pie
    "T20",    # flake8-print
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RSE",    # flake8-raise
    "RET",    # flake8-return
    "SLF",    # flake8-self
    "SLOT",   # flake8-slots
    "SIM",    # flake8-simplify
    "TID",    # flake8-tidy-imports
    "TC",     # flake8-type-checking
    "TD",     # flake8-todos
    "ARG",    # flake8-unused-arguments
    "PTH",    # flake8-use-pathlib
    "FIX",    # flake8-fixme
    "ERA",    # eradicate
    "PL",     # Pylint (PLC/PLE/PLR/PLW)
    "TRY",    # tryceratops
    "FLY",    # flynt
    "PERF",   # Perflint
    "FURB",   # refurb
    "DOC",    # pydoclint
    "RUF",    # Ruff-specific
]
ignore = [
    "D100",   # Missing docstring in public module
    "D104",   # Missing docstring in public package
    "COM812", # Missing trailing comma (formatter競合)
    "ISC001", # Implicit str concat (formatter競合)
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "D", "ANN"]
"scripts/**/*.py" = ["T20"]

[tool.ruff.format]
docstring-code-format = true

# ===== mypy =====
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
enable_error_code = [
    "ignore-without-code",
    "redundant-cast",
    "truthy-bool",
    "truthy-iterable",
    "unused-awaitable",
]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

# ===== pyright (併用する場合) =====
[tool.pyright]
typeCheckingMode = "strict"

# ===== pytest =====
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
filterwarnings = ["error"]
xfail_strict = true

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
    "@overload",
    "raise NotImplementedError",
]
fail_under = 80
show_missing = true

# ===== vulture =====
[tool.vulture]
min_confidence = 80
paths = ["src"]

# ===== deptry =====
[tool.deptry]
extend_exclude = ["scripts", "docs"]
```

---

## 15. その他モダンツール

| ツール | Stars | 用途 | 注目度 |
|--------|-------|------|--------|
| **deptry** | ~1,300 | 未使用依存検出（Rust製） | ★★★ |
| **pyproject-fmt** | ~200 | pyproject.toml整形 | ★★ |
| **validate-pyproject** | ~100 | pyproject.tomlスキーマ検証 | ★★ |
| **complexipy** | ~660 | 認知的複雑度（Rust製） | ★★★ |
| **interrogate** | ~660 | docstringカバレッジ | ★★ |
| **inline-snapshot** | ~500 | インラインスナップショットテスト | ★★ |
| **basedpyright** | ~2,000 | pyrightフォーク（より厳格） | ★★ |
| **just** | ~24,000 | タスクランナー（Rust製） | ★★★ |
| **act** | ~56,000 | GitHub Actionsローカル実行 | ★★ |
| **copier** | ~3,300 | テンプレートエンジン（更新差分適用） | ★★ |
| **cookiecutter-uv** | ~1,300 | uvネイティブPythonテンプレート | ★★★ |
| **mkdocs-material** | ~22,000 | ドキュメント生成 | ★★★ |

---

## 16. 推奨ツールスタック（総括）

| カテゴリ | 第1選択 | 補完 |
|---------|---------|------|
| パッケージ管理 | **uv** | - |
| Linter | **ruff** | pylint (高度解析) |
| Formatter | **ruff format** | - |
| 型チェック | **mypy strict** | pyright strict (併用) |
| テスト | **pytest** + cov + xdist + randomly | Hypothesis, mutmut |
| デッドコード | **vulture** | deadcode |
| 未使用依存 | **deptry** | - |
| セキュリティ(コード) | **ruff Sルール** | semgrep (高度) |
| セキュリティ(依存) | **pip-audit** | trivy (コンテナ) |
| シークレット検出 | **detect-secrets** | - |
| Docstring品質 | **ruff D+DOC** | interrogate (カバレッジ) |
| 複雑度 | **ruff C90** + **complexipy** | wily (時系列) |
| pre-commit | **pre-commit** | - |
| タスクランナー | **just** | Makefile |
| 設定管理 | **pydantic-settings** | - |
| ドキュメント | **mkdocs-material** | - |
| AI品質ゲート | **Claude Code Hooks** | - |

**最終更新日:** 2026-04-05
