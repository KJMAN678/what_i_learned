# Brief: knowledge-mcp

## Problem
開発中に困ったとき、過去に同じような技術を学んだ・試したことがあっても思い出せず、ログを探しに行く手間もかかる。Claude Code での作業中に、自分の過去の知見を自然に呼び出したい。

## Current State
daily-log-page によりログ（`YYYY-MM-DD.md`、tags、本文）と共有パーサ `wil.records` がある。サイトには全文検索があるが、Claude からは使えない。

## Desired Outcome
- ローカルで動く MCP サーバーを Claude Code に登録すると、「今困っていること」（自然文やキーワード）を渡したときに、関連する過去ログの該当箇所を日付・tags・抜粋つきで返す
- 特定の日のログ、特定タグのログを取得できる
- サーバーはローカルのリポジトリ内ログを直接読み、外部サービスに送信しない

## Approach
MCP Python SDK（FastMCP）で stdio の MCP サーバーを `wil` パッケージ内のサブモジュールとして作る。ログの読み込みは `wil.records` を使う。関連度判定はまず標準ライブラリで足りる素朴な方法（キーワード・tags 一致、見出し単位の抜粋）から始め、埋め込み検索などは要求と設計で必要性を判断する。

## Scope
- **In**:
  - MCP サーバー（stdio）と Claude Code への登録手順
  - ツール: 困りごとに関連する過去知見の検索、日付指定の取得、タグ指定の一覧
  - 結果の形式（日付、tags、該当見出し・抜粋、サイト上の URL）
  - 検索ロジックの単体テスト
- **Out**:
  - 公開サイトへの組み込み（実行時サーバーは持たない）
  - タグ正規化・技術インデックス（tech-timeline が所有。必要なら後で利用）
  - 学習のおすすめ（learning-recommendation）
  - ログの作成（log-writing-skill）

## Boundary Candidates
- MCP のツール定義（入出力契約）
- 関連知見の検索ロジック

## Out of Boundary
- ログのパース（`wil.records` を使う）
- 外部 API・LLM 呼び出し（サーバー自身は LLM を呼ばない。要約は呼び出し側の Claude が行う）

## Upstream / Downstream
- **Upstream**: daily-log-page（`wil.records`、ログ形式、公開 URL の規則）
- **Downstream**: なし

## Existing Spec Touchpoints
- **Extends**: なし
- **Adjacent**: tech-timeline（技術インデックス）、log-writing-skill

## Constraints
- ローカル専用。ネットワーク送信なし
- 依存は MCP SDK を基本とし、検索のための重い依存は必要性が示されるまで入れない
