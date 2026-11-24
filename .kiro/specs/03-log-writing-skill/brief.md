# Brief: log-writing-skill

## Problem
その日に学んだことを、ログ形式（ファイル名、frontmatter、見出しと入れ子の箇条書き）に沿って毎回まとめるのは手間がかかり、続かない。普段 Claude Code と壁打ちしながら学んでいるので、その流れでログまで仕上げたい。

## Current State
daily-log-page によりログ形式と検証（`wil.records` と pre-commit）がある。記録はすべて手書き。

## Desired Outcome
- Claude Code でこの skill を呼ぶと、対話しながらその日の学習内容（学習、気になった技術情報など）を聞き取り・整理し、正しい形式のログファイル `YYYY-MM-DD.md` を作成または追記する
- 生成されたログは daily-log-page の検証を通る
- 既存の tags の表記に揃えるよう提案する（表記ゆれを減らす）
- 公開前提であることを踏まえ、秘密情報や社外秘に見える内容を書く前に注意を促す

## Approach
リポジトリ内に Claude Code の skill（`SKILL.md` + 必要ならテンプレート）を置く。ログ形式の正本は daily-log-page の文書と `wil.records` にあり、skill はそれを参照する（形式を skill 側で二重定義しない）。作成後に検証コマンドを実行して結果を確認する。

## Scope
- **In**:
  - ログ作成・追記用の Claude skill
  - 聞き取りの流れ（その日の学習・気になった技術・メモ）と出力形式
  - 既存 tags の一覧取得と表記提案（`wil.records` 経由で読む）
  - 作成後の検証実行
- **Out**:
  - commit / push の自動実行（ユーザーが確認して行う）
  - 過去知見の検索・提示（knowledge-mcp）
  - 学習のおすすめ生成（learning-recommendation）
  - タグ正規化ルールの定義（tech-timeline）

## Boundary Candidates
- 聞き取りと要約のプロンプト設計
- ログファイルへの書き出し・検証

## Out of Boundary
- ログ形式の定義（daily-log-page が正本）
- おすすめ・推薦（learning-recommendation）

## Upstream / Downstream
- **Upstream**: daily-log-page（ログ形式、`wil.records`、検証コマンド）
- **Downstream**: なし（tech-timeline のタグ正規化ルールができたら、それを参照するよう更新されうる）

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: knowledge-mcp、learning-recommendation（いずれも Claude を使うが目的が違う）

## Constraints
- 書く手間を減らすことが目的。質問は最小限にし、ユーザーの文章を勝手に膨らませない
- 公開前提: 書き込み前に内容をユーザーに確認する
