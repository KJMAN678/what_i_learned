# Roadmap

## Overview
日々の学習成果を 1日 = 1ページの Markdown ログとして書き、GitHub Pages（`https://kjman678.github.io/what_i_learned/`、公開リポジトリ `KJMAN678/what_i_learned`）で公開する。まず手書きで公開できる最小構成を作り、一覧 → Claude による記録支援 → デザイン → MCP → 技術タイムライン → 学習のおすすめ、と段階的に機能を足す。

サイトは Zensical（Material for MkDocs の後継）で生成する。Zensical が扱えない動的ページは、ビルド前の Python スクリプトで Markdown を生成して補う。

## Approach Decision
- **Chosen**: Zensical + Python（uv）+ GitHub Actions → GitHub Pages
- **Why**: 検索・タグ・テーマが組み込みで 01〜04 が速い。MCP（05）や生成ページ（06・07）も Python で書け、ログのパーサを 1 か所で共有できる。MkDocs Material は 2027-05-05 で重大修正も終わるため後継を選んだ（ユーザー判断）
- **Rejected alternatives**:
  - Astro + Pagefind: 自由度は高いが画面を全部自作する手間。ユーザーがゼロベース検討の上で Zensical を選択
  - MkDocs Material: 2027-05 でサポート終了
  - Jekyll: 検索に別途 JS、MCP とパーサ共有不可

## Scope
- **In**: 1日1ページのログ公開、公開事故防止、一覧、Claude skill による記録支援、デザイン改良、過去知見を返すローカル MCP、技術ごとの学習時期検索、学習のおすすめページ
- **Out**: コメント、CMS、アクセス解析、多言語対応、Web/スマホからの編集、実行時サーバー

## Constraints
- **公開前提**: リポジトリも Pages も公開。公開コンテンツディレクトリ外のファイル、秘密情報、意図しないファイルが公開されてはならない
- **書く手間を増やさない**: 必須 frontmatter は最小（`tags` のみを想定）。日付はファイル名 `YYYY-MM-DD.md` から取る
- **Zensical の制約（全 spec 共通）**:
  - pre-1.0 のためバージョンを固定する
  - 任意の MkDocs プラグイン・プラグイン API は使えない。MkDocs の `hooks:` が使える前提も置かない（使う場合は公式ドキュメントで確認）
  - ビルド時に作るページ（一覧、タイムライン等）は「Zensical ビルド前に Python スクリプトが Markdown を生成」で作る
  - 設定ファイル形式・出力ディレクトリ・content ディレクトリは daily-log-page の設計で公式ドキュメントを確認して確定する
- **秘密情報**: Pages のクライアントに API キーを置かない。実行時に LLM を呼ばない。LLM を使う生成はオフラインで行い、結果を Markdown としてコミットする
- **言語**: ドキュメント・UI ともに日本語（`lang="ja"`）
- **年度**: 4 月始まり（2026-11 は 2026 年度、2026-01 は 2025 年度）

## Boundary Strategy
- **Why this split**: ユーザー指定の段階（01〜07）をそのまま spec 境界にし、各段階が単独でリリースできる縦切りにした
- **01/02 の境界（確定）**: 01 は Zensical の blog プラグインを使わず、通常ページとして 1 ログ = 1 ページを公開する（blog プラグインは frontmatter に `date` を要求し書く手間が増えるため）。一覧・アーカイブ表示は 02 がビルド前生成で所有する。01 時点のナビゲーションは Zensical の既定ナビで足りるものとする
- **共有所有物**:
  - ログ形式（置き場所、ファイル名、frontmatter）と Python パーサ/バリデータ `wil.records` は **01 が所有**。02・05・06・07 は再実装せず利用する
  - GitHub Actions のワークフローとビルドコマンドは **01 が所有**。02 がビルド前生成ステップを最初に導入し、06・07 は同じ方式で自分の生成モジュールを追加する
  - 技術 → 学習日インデックス（タグ正規化を含む）は **06 が所有**。07 はそれを読む
  - テーマ・CSS・見た目は **04 が所有**。他 spec はページ構造のみを持ち、独自スタイルを入れない
  - ナビゲーションの構成（区分名・並び・長さ）とトップページの見出し・説明文は **04 が所有**。各生成 spec はトップページ末尾へのリンク行追記と、site-design のナビ契約に従う `nav` への 1 項目追記のみ行う
- **Shared seams to watch**:
  - `wil.records` のデータモデル（日付、tags、本文、見出し構造）
  - ビルド前生成の出力先ディレクトリ（02 が決め、06・07 が従う）とナビ契約（04 が決め、02・06・07 が従う）
  - 03（記録用 skill）と 07（おすすめ生成）はどちらも Claude を使う。03 はログを書く、07 はおすすめを作る、で分ける

## Specs (dependency order)
- [x] 01-daily-log-page -- 1日分の学習ログを手書きの Markdown 1ファイルから 1ページとして公開し、gitignore と pre-commit で意図しないファイルの公開を防ぐ。Dependencies: none
- [x] 02-log-index -- ログの一覧ページ（年度・月でグルーピング）をビルド前生成で追加する。Dependencies: 01-daily-log-page
- [x] 03-log-writing-skill -- Claude と対話しながらその日の学習成果をログ形式にまとめる Claude skill を作る。Dependencies: 01-daily-log-page
- [ ] 04-site-design -- サイトのデザイン（テーマ、配色、タイポグラフィ、ログ・一覧の見やすさ）を改良する。Dependencies: 01-daily-log-page, 02-log-index
- [x] 05-knowledge-mcp -- ログを元に、今困っていることに役立つ過去の知見を返すローカル MCP サーバーを作る。Dependencies: 01-daily-log-page
- [x] 06-tech-timeline -- 気になった技術をいつ学習したかを検索・時系列表示できるようにする（技術インデックスを所有）。Dependencies: 01-daily-log-page, 02-log-index
- [x] 07-learning-recommendation -- 技術ごとに「学習済みの内容」と「未学習で学ぶとよい内容」を示すおすすめページを作る。Dependencies: 01-daily-log-page, 02-log-index, 06-tech-timeline, 04-site-design
