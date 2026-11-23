# Brief: tech-timeline

## Problem
「この技術、前に学んだ気がするけどいつだっけ」を調べたい。全文検索では該当ページは見つかっても、その技術を学んだ日付の流れ（初めて触れた日、繰り返し学んだ時期）が見えない。タグの表記ゆれ（例: `MCP` と `mcp`、`AWS Lambda` と `Lambda`）があると、同じ技術が分散する。

## Current State
daily-log-page によりログごとに `tags` がある。log-index によりビルド前生成の方式と一覧ページがある。Zensical の組み込み検索・タグ機能が使える。

## Desired Outcome
- 技術（タグ）を指定または検索すると、その技術を学習した日付の一覧（時系列）と、各日のログへのリンク・該当抜粋が見られる
- 技術ごとの初回日・最終日・回数が分かる
- 表記ゆれを吸収した「技術インデックス」（技術 → 学習日の対応）ができ、learning-recommendation が利用できる

## Approach
`wil.records` でログを読み、タグ正規化（別名の対応表を含む）を行って技術インデックスを作る Python モジュールを `wil` 内に置く。log-index が定義したビルド前生成方式で、技術ごとのタイムラインページと技術一覧ページを生成する。技術の検索は Zensical 組み込み検索・タグ機能でどこまで足りるかを設計で確認し、足りない分だけを補う。

## Scope
- **In**:
  - タグ正規化ルール（別名対応表）とその置き場所
  - 技術インデックス（技術 → 学習日・ログ・抜粋）のデータモデルと生成モジュール。下流が読める形で提供する
  - 技術一覧ページと技術別タイムラインページの生成
  - 技術名での検索導線（組み込み検索・タグ機能の活用を含む）
  - インデックス生成・正規化の単体テスト
- **Out**:
  - おすすめ・未学習領域の提示（learning-recommendation）
  - 見た目（site-design）
  - 本文からの技術名自動抽出に LLM を使うこと（必要なら learning-recommendation 側でオフライン実施）

## Boundary Candidates
- タグ正規化と技術インデックス（learning-recommendation への契約）
- タイムラインページの生成

## Out of Boundary
- ログのパース（`wil.records`）、ビルド前生成の方式（log-index）
- 一覧ページ（log-index）

## Upstream / Downstream
- **Upstream**: daily-log-page（`wil.records`、ログ形式）、log-index（ビルド前生成方式）
- **Downstream**: learning-recommendation（技術インデックスを読む）、knowledge-mcp・log-writing-skill（正規化ルールを後から参照しうる）

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: log-index、knowledge-mcp

## Constraints
- 正規化ルールの追加で書く手間を増やさない（ログ側は自由に書き、吸収はインデックス側で行う）
- Zensical のプラグイン API・hooks に頼らない
