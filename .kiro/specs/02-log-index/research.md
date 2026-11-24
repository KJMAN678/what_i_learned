# Research & Design Decisions

## Summary
- **Feature**: `log-index`
- **Discovery Scope**: Extension（daily-log-page の設計契約の上に乗る拡張。実装コードはまだ無く、上流の design.md / research.md を既存システムとして扱う軽量調査）
- **Key Findings**:
  - Zensical は MkDocs hooks・任意プラグインに対応しない（上流 research.md）。一覧はビルド前に Python で Markdown を生成する以外の手段が無い
  - Zensical がリポジトリの `.gitignore` を読んでビルド対象から外すという記述は公式ドキュメントに無い。除外は `exclude_docs` / `draft_docs` / `not_in_nav`（gitignore 形式の構文、`docs_dir` 基準）で明示的に行う仕組み。したがって gitignore した `content/generated/` もビルドには含まれる見込み（実装タスクの最初のビルドで実地確認する）
  - `nav` 未指定時はフォルダ構造からナビゲーションが作られるが、フォルダ名からのセクション名の決め方・並び順は公式に記載が無い。明示 `nav` は全ログの列挙が必要になり採用できない

## Research Log

### 上流契約（daily-log-page）の確認
- **Context**: brief / 依頼で「上流の契約を再定義せず再利用」と指定
- **Sources Consulted**: `.kiro/specs/01-daily-log-page/design.md`, `.kiro/specs/01-daily-log-page/research.md`, `.kiro/specs/01-daily-log-page/requirements.md`
- **Findings**:
  - `zensical.toml`: `docs_dir = "content"`、`site_dir = "site"`、`use_directory_urls` 既定 true、`nav` 未指定（一覧は log-index 所有と明記）
  - ログは `content/logs/YYYY-MM-DD.md`。`wil.records` は `Record(date, path, url_path, tags, summary, body, sections)`、`load_records(content_dir) -> list[Record]`（日付昇順、不正があれば `RecordsInvalid` で全件報告）、`CONTENT_DIR`、`LOGS_SUBDIR = "logs"`、`ALLOWED_PATTERNS`
  - `scripts/build.sh`: `set -eu` で「検証 `uv run python -m wil.records` → 生成段（空のコメント行）→ `uv run zensical build --clean --strict`」
  - 上流が明示的に許可している統合方法: 「生成ページを `content/` 配下に追加する spec は、`ALLOWED_PATTERNS` へのパターン追加と `scripts/build.sh` の生成段への追記で統合する」
  - CI（`deploy.yml`）は `uv run pytest` → `./scripts/build.sh` → Pages デプロイ。CI 本体の変更は不要
  - 検証 CLI は引数なしのとき `content/` 以下の全ファイル（ドットファイル除く）を許可リストで検査する
- **Implications**:
  - 検証段は生成段より前に走るため、手元に前回の生成物が残っていると許可外ファイルとして失敗する。生成物の区域を `ALLOWED_PATTERNS` に 1 パターンで許可する必要がある
  - `load_records` は `content/logs/*.md` を全件パースするため、生成ページを `content/logs/` に置くと（例: `logs/index.md`）ファイル名規則違反で読み取りが壊れる。生成ページは別サブディレクトリに置く

### Zensical の gitignore 扱い・ナビゲーション
- **Context**: 生成物は gitignore するが、ビルドとナビゲーションには載せたい
- **Sources Consulted**: https://zensical.org/docs/setup/basics/ , https://zensical.org/docs/setup/navigation/ , Web 検索（"zensical docs_dir gitignore"）
- **Findings**:
  - 「Dotfiles, files inside dot directories, and the top-level `templates/` directory are excluded by default」。`.gitignore` を読むという記述は無い。`exclude_docs` 等は「.gitignore syntax is supported」という構文の話
  - 「By default, Zensical creates the navigation sidebar on the basis of the folder structure」。フォルダ名からのラベル生成や並び順は記載なし
  - 明示 `nav` はパスの列挙。ディレクトリ単位の自動展開と明示エントリの混在は記載なし
  - section index pages（フォルダの `index.md` をセクションに付ける機能）はある
- **Implications**:
  - 生成先のディレクトリ名をドットや `templates` で始めない（既定除外に当たらないように）
  - ナビゲーションは既定（フォルダ構造）に任せ、`zensical.toml` は変更しない。ナビのラベル・位置の実表示は実装タスクで確認する。ナビゲーションの構成（区分名・並び・長さ）は roadmap に従い site-design が所有する
  - ナビの表示が確実でないため、到達経路の主はトップページからのリンクとする

### Markdown のエスケープ
- **Context**: summary / tags は書き手の任意文字列。`[`, `*`, `<` 等で一覧の構造（リンク・強調・HTML）が崩れうる（3.6）
- **Sources Consulted**: Python-Markdown のバックスラッシュエスケープ仕様（一般知識。Zensical は Python-Markdown ベース）
- **Findings**: Python-Markdown の基本エスケープ対象は `` \ ` * _ { } [ ] ( ) > # + - . ! ``。HTML は素通しされる
- **Implications**: `& < >` を HTML 実体参照に、上記記号をバックスラッシュでエスケープする。拡張由来の記法（`~~` 等）は対象外（リスクに記録）

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| ビルド前生成スクリプト + 専用ディレクトリ（採用） | `scripts/generate.sh` が `content/generated/` を作り直し、各生成器モジュールを順に呼ぶ | 単一の登録箇所、CI と手元が同じ、純粋関数でテスト可能 | ナビのラベルは Zensical 既定任せ | roadmap / tech.md の方針どおり |
| build.sh の生成段に各生成器を直接列挙 | 生成器ごとに build.sh に 1 行 | ファイルが 1 つ少ない | 手元プレビュー用の生成手順が別途必要になり登録箇所が 2 つ（6.5 違反） | 却下 |
| Python の集約エントリ（`python -m wil.generate` が全生成器を import） | 登録を Python のリストで行う | シェル不要 | 集約モジュールが全機能に依存し「機能同士は直接依存しない」に反する | 却下 |
| 生成ページを `content/logs/index.md` に置く | URL `/logs/` | URL が自然、セクション index | `load_records` が `logs/*.md` を全件パースし壊れる、手書きと生成物の混在（structure.md 違反） | 却下 |
| 一覧をトップページ `content/index.md` として生成 | トップ = 一覧 | 入口が 1 つ | 上流所有のコミット済みファイルを gitignore 化・上書きすることになり、生成前は top が無い | 却下 |
| 明示 `nav` を `zensical.toml` に書く | ナビ位置を制御 | ラベル・順序を確定できる | 全ログを列挙する必要があり、書く手間を増やす | 却下 |

## Design Decisions

### Decision: 生成ページの区域は `content/generated/`（gitignore）、各ページ名は機能名
- **Context**: 5.4、6.2、6.3。structure.md「手書きログと生成ページを別サブディレクトリに分け、CI 生成物は gitignore」「生成ページは生成元の機能名がわかる名前」
- **Alternatives Considered**: 1. 機能ごとのトップレベルディレクトリ（`content/log-index/` 等）2. 共通の `content/generated/`
- **Selected Approach**: 共通の `content/generated/`。log-index は `content/generated/log-index.md`（URL `generated/log-index/`）。後続は `generated/<feature-name>.md` または `generated/<feature-name>/...`
- **Rationale**: `.gitignore` 1 行・`ALLOWED_PATTERNS` 1 パターン・削除 1 回で全生成器をまとめて扱え、後続 spec はこれらに触れずに済む（6.5）
- **Trade-offs**: URL に `generated/` が入る。ナビに `generated` 由来のセクションが出る可能性がある（ナビゲーションの構成は site-design が所有）

### Decision: 単一の登録箇所 `scripts/generate.sh`
- **Context**: 6.1、6.5、7.2。手元と CI で同じ生成を 1 コマンドで行う
- **Selected Approach**: `scripts/generate.sh` が `content/generated/` を削除してから各生成器（`uv run python -m wil.<feature>`）を順に実行する。`scripts/build.sh` の生成段はこのスクリプトを呼ぶ 1 行だけ。後続 spec は `generate.sh` に 1 行追加する
- **Rationale**: 登録箇所が 1 つ。古い生成物を毎回消すので 6.6 を満たす。上流が許可した「生成段への追記」の範囲内
- **Trade-offs**: スクリプトが 1 つ増える

### Decision: 共有ヘルパー `wil.generated` を置く
- **Context**: 3 つの生成器（log-index、tech-timeline、learning-recommendation）が同じ「ログを読む → 不正なら全件報告して終了コード 1 → 区域にページを書く」を行う。steering は「機能 → `wil.records`」の依存のみを想定
- **Selected Approach**: `src/wil/generated.py` に区域の定数と `run()`（読み取り・誤り報告・書き出し）、全生成器共通の `escape_inline()` だけを置く。機能固有のロジックは持たない。依存は `wil.records` のみ
- **Rationale**: 出力先と終了コードの規則を 1 か所に固定し、後続が同じ振る舞いになる（5.6、6.2）。機能同士の依存（後続 → `wil.log_index`）を避ける
- **Trade-offs**: 小さなモジュールが 1 つ増える。年度計算は現時点で log-index 専用のため `wil.log_index` に置く（2 つ目の利用者が出たら共有化を検討）

### Decision: 生成器は純粋関数 `render` + 薄い `main`
- **Context**: brief「ログ → Markdown の純粋な変換」、8.1–8.3
- **Selected Approach**: `wil.log_index.render(records) -> str` は I/O なし。`main()` は `wil.generated.run` に `render` を渡すだけ
- **Rationale**: テストは `Record` を直接組み立てて `render` を呼ぶだけで済む

### Decision: ナビゲーションは既定に任せ、トップページからリンクする
- **Context**: 4.1–4.4。Zensical の既定ナビのラベル・順序は未記載
- **Selected Approach**: `zensical.toml` は変更しない（フォルダ構造の既定ナビに `generated/log-index.md` が載る）。`content/index.md` に一覧へのリンクを 1 行追加する。トップページ自体は生成しない
- **Rationale**: 明示 `nav` は全ログ列挙が必要で不可。トップページのリンクは確実な到達経路
- **Follow-up**: ナビ上のラベル・位置を実装時に確認し research に追記。ラベルは H1「学習ログ一覧」が使われる想定

### Decision: リンクはソース相対パス `../logs/YYYY-MM-DD.md`
- **Context**: 3.2、8.3、上流 3.6（サブパス動作）・6.3（`--strict` のリンク検証）
- **Selected Approach**: 生成 Markdown では `Record.url_path` や `site_url` ではなく、生成ページからのソース相対パスでログを指す
- **Rationale**: `--strict` のリンク検証対象になり、サブパス配下でも Zensical が正しい相対 URL に変換する。ルート絶対パスを生まない

### Decision: 年度・月の並び
- **Context**: 1.2–1.5、2.1–2.3
- **Selected Approach**: `fiscal_year(d) = d.year if d.month >= 4 else d.year - 1`。ログを日付降順に並べ、連続する同一年度・同一 (暦年, 月) をグループにする。日付降順の 1 列から作るため、年度内でも翌年 1〜3 月が先に来る
- **Rationale**: ソート 1 回 + 連続グループ化で済み、並びの規則が 1 つにまとまる

## Synthesis Outcomes
- **Generalization**: 「ログ → 生成ページ群」を `render_pages(records) -> dict[str, str]` の形で `wil.generated.run` に渡す。log-index は 1 ページだが、tech-timeline のように複数ページを作る生成器も同じ入口で扱える（インターフェースだけを一般化し、実装は 1 ページ分のみ）
- **Build vs Adopt**: Zensical blog プラグイン（アーカイブ機能）は frontmatter `date` 必須のため不採用（roadmap 確定事項）。テンプレートエンジン（Jinja2）は Zensical の推移的依存として入るが、出力が数十行の Markdown で文字列連結で足りるため使わない。新規依存なし
- **Simplification**: 設定ファイル（生成器の一覧を書く YAML 等）は作らない。登録は `generate.sh` の 1 行。`fiscal_year` は共有化しない。CSS・テンプレート上書きは site-design に委ねる

## Risks & Mitigations
- Zensical が gitignore されたファイルを読まない可能性 — 公式に記述なし。実装の最初のビルドで `site/generated/log-index/index.html` の生成を確認する。読まない場合は設計に戻る（`exclude_docs` の否定パターンなど）
- ナビの `generated` セクション名・並び順が不格好 — 要件はナビに項目が出ることまで。ナビゲーションの構成（区分名・並び・長さ）は site-design が所有。トップページのリンクを主な到達経路とする
- `zensical serve` を生成なしで起動するとトップのリンクが切れる（警告） — 手順書に「先に `./scripts/generate.sh`」を記載（7.3）。ビルドは build.sh 経由なので必ず生成される
- Markdown 拡張記法（`~~`、`==` 等）が summary 内で解釈される — 基本記号のみエスケープ。拡張記法は書き手の意図と区別できないため許容
- 生成物を `git add -f` で強制追加 — gitignore が既定で防ぐ。強制追加は想定外の操作として扱わない

## References
- [Zensical Basics](https://zensical.org/docs/setup/basics/) — `docs_dir`、既定除外（ドットファイル・`templates/`）、`exclude_docs` の構文
- [Zensical Navigation](https://zensical.org/docs/setup/navigation/) — フォルダ構造からの既定ナビ、明示 `nav`、section index pages
- `.kiro/specs/01-daily-log-page/design.md` — `wil.records` 契約、`scripts/build.sh` の生成段、`ALLOWED_PATTERNS` 拡張方針
