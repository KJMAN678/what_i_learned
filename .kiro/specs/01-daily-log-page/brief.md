# Brief: daily-log-page

## Problem
自分（サイトのオーナー）は日々の学習成果を残したいが、書く場所と公開の仕組みがない。公開リポジトリなので、書き方を間違えると設計メモや秘密情報、ビルド生成物まで公開されてしまう危険がある。

## Current State
- リポジトリ `KJMAN678/what_i_learned` は実質空。`.gitignore` は空ファイル
- git の index に、以前の Astro 試作の `dist/`、`node_modules/`、`.astro/` がステージされたまま残っている（作業ツリーでは削除済み）
- HEAD には非公開の計画文書 `docs/superpowers/*` が追跡されている。Zensical の既定 content ディレクトリ `docs/` と衝突し、そのままだと公開されうる
- `.kiro/` と `.claude/` は仕様・ツール用で公開対象外

## Desired Outcome
- 手書きの Markdown 1ファイル = 1日 = 1ページとして、`main` への push で GitHub Pages に公開される
- 公開されるのは公開コンテンツディレクトリ内のログだけ。ビルド生成物・仮想環境・キャッシュ・秘密情報・非公開文書はコミットも公開もされない
- 書式の誤り（日付として不正なファイル名、`tags` の欠落、壊れた frontmatter）をコミット前に手元で検出できる

## Approach
- Zensical（バージョン固定）+ uv。blog プラグインは使わず、通常ページとして 1 ログ = 1 ページにする（roadmap の 01/02 境界）
- ログ形式と Python のパーサ/バリデータ `wil.records`（`src/wil/`）をこの spec で定義する。pre-commit とビルドの両方から同じバリデータを呼ぶ
- GitHub Actions でビルドし、GitHub Pages にデプロイする
- 設定ファイル形式（`zensical.toml` か `mkdocs.yml` か）、content ディレクトリ、出力ディレクトリ、`site_url` / ベースパスの扱いは、設計段階で zensical.org の公式ドキュメントを確認して確定する

## Scope
- **In**:
  - Zensical プロジェクトの初期構成（設定、pyproject、uv.lock、Zensical のバージョン固定）
  - ログ形式: ファイル名 `YYYY-MM-DD.md`、frontmatter は `tags`（必須、文字列配列）と `summary`（任意）、本文は自由な Markdown（入れ子の箇条書きを含む）
  - 共有パッケージ `wil.records`: ログ一覧の読み込み、日付・tags・本文のパース、検証。単体テスト付き
  - 公開コンテンツディレクトリの決定と、非公開文書（`docs/superpowers/*` 等）が公開されない構成
  - `.gitignore`: Zensical の出力、`.venv`、Python キャッシュ、旧 Astro 生成物（`dist/`、`node_modules/`、`.astro/`）、`.env` 系
  - pre-commit: 秘密情報の検出、大きなファイルの拒否、公開ディレクトリ内の許可外ファイルの拒否、ログ書式の検証
  - GitHub Actions: `main` への push でビルド → Pages デプロイ。ビルド時にもログ書式を検証し、不正ならビルドを失敗させる
  - 書き方の手順（ログの置き場所、frontmatter の例、ローカル確認・検証コマンド）を短くまとめた文書
  - 初期ログ 1 件（サンプル）
- **Out**:
  - 一覧・アーカイブページ（log-index）
  - テーマ・見た目の改良（site-design）。既定テーマ + `lang="ja"` のみ
  - タグ正規化・技術インデックス（tech-timeline）
  - Claude による記録支援（log-writing-skill）
  - git index に残った旧 Astro 生成物の除去作業そのもの（ユーザーが行う。gitignore で再混入は防ぐ）

## Boundary Candidates
- ログ形式と `wil.records`（下流すべてが依存する契約）
- 公開範囲の制御（content ディレクトリ、gitignore、pre-commit）
- ビルド・デプロイのパイプライン（Actions とビルドコマンド）

## Out of Boundary
- ビルド前生成の仕組み（log-index が最初に導入する。この spec はビルドコマンドに生成ステップを差し込める形にするだけで、生成器は作らない）
- 見た目の調整、一覧、検索 UI のカスタマイズ

## Upstream / Downstream
- **Upstream**: なし
- **Downstream**: log-index、log-writing-skill、knowledge-mcp、tech-timeline、site-design、learning-recommendation（全て `wil.records` とログ形式を利用）

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: log-index（ナビゲーション・ビルドコマンド）、site-design（テーマ設定）

## Constraints
- 書く手間を増やさない: 必須 frontmatter は `tags` のみ。日付は frontmatter に書かない
- 公開前提: 「公開コンテンツディレクトリにあるログだけが公開される」を構造で保証する
- GitHub Pages のプロジェクトサイト（`https://kjman678.github.io/what_i_learned/`）としてサブパスで正しく動くこと
- Pages の Source を「GitHub Actions」に切り替える初回設定はユーザーが行う
