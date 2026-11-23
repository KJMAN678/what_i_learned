# Technology Stack

## Architecture

静的サイト。Markdown のログを Zensical（Material for MkDocs の後継）でビルドし、GitHub Actions から GitHub Pages に公開する。実行時サーバーは持たない。

動的に作るページ（一覧、技術タイムライン等）は、**Zensical ビルド前に Python スクリプトが Markdown を生成する**方式で作る。Zensical は現時点で任意の MkDocs プラグインや独自プラグイン API を提供しないため、プラグインには頼らない。

ローカル専用の機能（MCP サーバー、Claude skill）は、公開サイトとは別にリポジトリ内のログを直接読む。

## Core Technologies

- **Language**: Python 3.12+
- **Site generator**: Zensical（pre-1.0。バージョンを固定する）
- **Package / env**: uv（`pyproject.toml` + `uv.lock`）
- **Hosting**: GitHub Pages（GitHub Actions でビルド・デプロイ）

## Key Libraries

- Zensical: サイト生成。組み込みの検索・タグ・テーマ機能を優先して使う
- pre-commit: コミット前の公開事故防止
- MCP Python SDK（`mcp` 2.x、`MCPServer`。旧 FastMCP）: ローカル MCP サーバー

## Development Standards

### Code Quality
- ruff（lint + format）

### Testing
- pytest。ロジック（パース、日付計算、集計、生成）に小さな単体テストを置く

### Simplicity
- 標準ライブラリ・Zensical 組み込み機能で足りるなら依存を増やさない
- ログのパース処理は共有パッケージに 1 か所だけ置き、他機能は再利用する

## Development Environment

### Required Tools
- uv, Python 3.12+, git, pre-commit

### Common Commands
```bash
# Dev:   uv run zensical serve
# Build: 生成スクリプト実行 → uv run zensical build（正確なコマンドは daily-log-page 設計で確定）
# Test:  uv run pytest
```

## Key Technical Decisions

- MkDocs Material は 2027-05 で重大修正も終了するため、後継の Zensical を採用（ユーザー判断）
- Zensical の設定ファイル形式・出力ディレクトリ・hooks 対応可否は、推測せず公式ドキュメントで確認してから使う
- 公開サイトに秘密情報や API キーを置かない。LLM を使う生成はオフラインで行い、結果を Markdown としてコミットする

---
_Document standards and patterns, not every dependency_
