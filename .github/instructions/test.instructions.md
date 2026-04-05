## テスト規約

### フレームワーク
- pytest + pytest-asyncio（asyncio_mode = "auto"）
- モック: `unittest.mock`（MagicMock / AsyncMock / patch）

### テスト配置
- `tests/` 配下に配置
- プロダクトコードのディレクトリ構造をミラーする

### 命名規則
- ファイル: `test_<モジュール名>.py`
- 関数: `test_<対象>_<状況>_<期待結果>`
- 例: `test_agent_run_with_empty_input_raises_error`

### 方針
- ブラックボックステスト主体（入力→出力の検証）
- 外部依存（Cosmos, LLM API）はモックに差し替え
- 1テスト1検証事項
- 正常系・異常系・境界値を網羅

### コマンド
```bash
make test              # 全テスト
uv run pytest -k "キーワード"  # 特定テスト
make test-cov          # カバレッジ付き
```
