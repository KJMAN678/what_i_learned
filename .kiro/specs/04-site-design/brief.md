# Brief: site-design

## Problem
既定テーマのままでは、学習ログとしての読みやすさ（入れ子の箇条書き、日付・タグの見え方、一覧の見渡しやすさ）が十分でなく、人に紹介するときの印象も弱い。

## Current State
daily-log-page で Zensical 既定テーマ + `lang="ja"`、log-index で一覧ページがある。見た目の調整はしていない。

## Desired Outcome
- ログ詳細ページ・一覧ページが日本語で読みやすい（フォント、行間、入れ子リストのインデント、日付・タグの表示）
- ライト/ダーク両対応
- サイトの目的（自分の学習記録）が伝わるトップの見せ方
- 今後追加されるページ（技術タイムライン、おすすめ）も同じテーマで破綻なく表示される

## Approach
Zensical のテーマ設定（配色、フォント、機能フラグ）と追加 CSS で改良する。テンプレート上書きは必要最小限にし、使う場合は Zensical の公式ドキュメントで対応状況を確認する。見た目はこの spec が一元的に所有し、他 spec はページ構造のみを持つ。

## Scope
- **In**:
  - テーマ設定（配色、ライト/ダーク、フォント、ナビゲーション関連の機能フラグ）
  - 追加 CSS（ログ本文、日付・タグ表示、一覧）
  - トップページの見せ方
  - アクセシビリティの基本（コントラスト、フォーカス表示）
  - 主要ページの表示確認手順
- **Out**:
  - ページの内容・生成ロジック（log-index、tech-timeline、learning-recommendation）
  - 独自 JS による機能追加
  - ロゴ・ブランド制作

## Boundary Candidates
- テーマ設定
- 追加 CSS とテンプレート上書き

## Out of Boundary
- 一覧・タイムラインの Markdown 構造（各 spec が所有。必要な class などはこの spec と合意する）

## Upstream / Downstream
- **Upstream**: daily-log-page（設定ファイル、テーマ）、log-index（一覧ページ構造）
- **Downstream**: tech-timeline、learning-recommendation のページはこのテーマに従う

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: log-index、tech-timeline（並行して作られるため、CSS で前提にする構造は汎用的にする）

## Constraints
- 凝りすぎない。読みやすさ優先
- Zensical は pre-1.0。テンプレート上書きは壊れやすいので最小限
