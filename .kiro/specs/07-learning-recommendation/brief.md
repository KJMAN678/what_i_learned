# Brief: learning-recommendation

## Problem
ある技術に興味を持ったとき、自分がその周辺で何をすでに学んでいて、何が抜けているのかが分からない。ログを読み返して自分で整理するのは大変。

## Current State
tech-timeline により、技術インデックス（技術 → 学習日・ログ・抜粋、表記ゆれ吸収済み）とタイムラインページがある。公開サイトは静的で、実行時サーバーや API キーを持てない。

## Desired Outcome
- 技術ごとに「あなたはこの周辺でこういうことを学習している」（ログに基づく要約と根拠となる日付・リンク）と「この辺りはまだ学習していないので学ぶとよい」（未学習の関連領域）を示すページがサイトに公開される
- おすすめの根拠（どのログに基づくか）が辿れる
- ログが増えたら、手順に従っておすすめを更新できる

## Approach
「未学習で学ぶとよい領域」はログ外の知識が必要なため LLM を使う。公開サイトには秘密情報を置けず実行時に LLM を呼べないので、**オフラインで生成し、結果を Markdown（またはデータファイル）としてコミットする**のを既定とする。生成の起動方法（Claude Code の skill か、ローカルスクリプトか）と、対象技術の選び方は設計で決める。技術インデックスは tech-timeline のものを読む。ページ化は log-index のビルド前生成方式に従う。

## Scope
- **In**:
  - おすすめ内容のデータ形式（学習済みの要約、根拠ログ、未学習領域、生成日時）
  - オフライン生成の手順と仕組み
  - おすすめページ（技術別、一覧）の生成とナビゲーションへの組み込み
  - 学習済み部分がログの事実に基づくことの検証方法
- **Out**:
  - ログの作成支援（log-writing-skill）
  - 技術インデックス・タグ正規化（tech-timeline）
  - 過去知見の MCP 提供（knowledge-mcp）
  - 実行時の LLM 呼び出し、ブラウザ側での生成

## Boundary Candidates
- おすすめのオフライン生成
- おすすめページの生成

## Out of Boundary
- log-writing-skill の領域（ログを書く skill）。この spec の skill/スクリプトはおすすめ生成専用で、ログを書き換えない
- タグ正規化ルールの変更（tech-timeline に依頼する）

## Upstream / Downstream
- **Upstream**: daily-log-page（`wil.records`）、tech-timeline（技術インデックス）、log-index（ビルド前生成方式）
- **Downstream**: なし

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: log-writing-skill、knowledge-mcp、tech-timeline

## Constraints
- API キー・秘密情報をリポジトリや Pages に置かない
- 生成物は公開されるため、ログにない個人情報を推測で書かない
- 生成のたびに大きな差分が出すぎないよう、更新単位を設計で考える
