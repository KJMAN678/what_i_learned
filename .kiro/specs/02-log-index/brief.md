# Brief: log-index

## Problem
ログが増えると、1 ページずつのナビゲーションだけでは何をいつ書いたか見渡せない。自分が見返すときも、人に紹介するときも、全体を一覧できる入口が要る。

## Current State
daily-log-page により、1 ログ = 1 ページの通常ページとして公開されている。一覧・アーカイブはなく、Zensical の既定ナビゲーションのみ。blog プラグインは使っていない（frontmatter に `date` を要求し書く手間が増えるため）。

## Desired Outcome
- トップ（または一覧ページ）から、全ログを新しい順に、年度（4 月始まり）と月でグルーピングして見渡せる
- 各行に日付、tags、summary（あれば）が表示され、詳細ページへ移動できる
- 新しいログを追加して push するだけで一覧が更新される（手で一覧を編集しない）

## Approach
Zensical ビルド前に Python スクリプトが `wil.records` でログを読み、一覧ページの Markdown を生成する。生成物は gitignore し、CI のビルドコマンド（daily-log-page 所有）に生成ステップを組み込む。このビルド前生成の方式（生成器モジュールの置き場所、出力先、ナビゲーションへの組み込み、ローカル実行方法）はこの spec が最初に定義し、tech-timeline・learning-recommendation が同じ方式に従う。

## Scope
- **In**:
  - ビルド前生成の方式の定義と、その最初の生成器（一覧ページ）
  - 年度計算（4 月始まり）と並び順のロジック、単体テスト（3/31 と 4/1 の境界を含む）
  - 一覧ページのナビゲーションへの組み込み（トップページにするかを含めて設計で決める）
  - ローカルでの生成 + プレビュー手順
- **Out**:
  - タグ別ページ・技術タイムライン（tech-timeline）
  - 見た目の作り込み（site-design）。この spec は Markdown の構造のみ
  - 全文検索（Zensical 組み込み検索をそのまま使う）

## Boundary Candidates
- ビルド前生成の共通方式（下流 spec が従う契約）
- 一覧ページの生成ロジック

## Out of Boundary
- ログ形式・パーサ（daily-log-page の `wil.records` を使う。再実装しない）
- CI ワークフロー本体の所有（daily-log-page。生成ステップの追加のみ行う）

## Upstream / Downstream
- **Upstream**: daily-log-page（`wil.records`、ビルドコマンド、content ディレクトリ）
- **Downstream**: tech-timeline、learning-recommendation（ビルド前生成方式に従う）、site-design（一覧の見た目）

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: daily-log-page（ビルドコマンド）、tech-timeline（タグからの導線）

## Constraints
- Zensical のプラグイン API・MkDocs hooks には頼らない
- 生成は「ログ → Markdown」の純粋な変換にし、テスト可能にする
- 年度は 4 月始まり
