# Project Structure

## Organization Philosophy

「公開コンテンツ」「共有 Python パッケージ」「ローカル専用ツール」を分ける。公開ディレクトリに入れたものだけが公開される、を構造で保証する。

## Directory Patterns

### 公開コンテンツ
**Location**: Zensical の content ディレクトリ（名前は daily-log-page 設計で確定。リポジトリ内の非公開文書と混ざらないこと）
**Purpose**: 学習ログ本体と、ビルド前に生成されるページ
**Rule**: 手書きログと生成ページを別サブディレクトリに分け、CI 生成物は gitignore する

### 共有 Python パッケージ
**Location**: `src/wil/`（`wil` = what_i_learned）
**Purpose**: ログのパース・検証（`wil.records`）など、複数機能から使うロジック
**Rule**: 機能ごとにサブモジュールを持つ。ログのパースは `wil.records` 以外で再実装しない

### ローカル専用ツール
**Location**: Claude skill はリポジトリの skill ディレクトリ、MCP サーバーは `wil` 内のサブモジュール
**Purpose**: 公開サイトに含めない、ローカルでのみ動く機能

### コミットする生成元データ
**Location**: `data/<feature>/`
**Purpose**: オフライン生成した結果など、生成器の入力としてコミットするデータ（例: おすすめの JSON）
**Rule**: content ディレクトリの外に置くためサイトには出ないが、公開リポジトリには含まれる。その機能の生成器・CLI・skill だけが読み書きする

### 仕様・設計
**Location**: `.kiro/`, `docs/`（非公開の設計文書。公開対象外）

## Naming Conventions

- **ログファイル**: `YYYY-MM-DD.md`（ファイル名が日付。frontmatter に日付を重複して書かない）
- **Python モジュール・関数**: snake_case
- **生成ページ**: 生成元の機能名がわかる名前

## Code Organization Principles

- 依存方向: 各機能 → `wil.records`、各生成器 → `wil.generated`（log-index 所有の共有ヘルパー）。機能同士は直接依存しない（例外: 07 は 06 の技術インデックスを読む）
- ビルド前生成は「ログを読み → Markdown を書き出す」純粋な変換にし、単体テスト可能にする

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
