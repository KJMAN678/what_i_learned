# Research & Design Decisions

## Summary
- **Feature**: `daily-log-page`
- **Discovery Scope**: New Feature（グリーンフィールド。既存コードなし、Zensical は pre-1.0 のため公式ドキュメントでの確認を伴うフル調査）
- **Key Findings**:
  - Zensical は `zensical.toml`（`[project]` テーブル）を正式な設定形式とし、`mkdocs.yml` も読める。MkDocs の `hooks` は「未対応」と明記されている
  - `docs_dir` は `.` にできず、既定の `docs/` は HEAD の非公開文書 `docs/superpowers/*` と衝突するため、公開コンテンツディレクトリを `content/` に分ける
  - PyPI の最新は 0.1.3（調査日 2026-11-23）。依存に `pyyaml>=6.0.2` を含む。組み込み検索は「英語のみ」と記載があり、日本語ログの検索品質はリスク

## Research Log

### 設定ファイル形式と基本設定
- **Context**: brief / roadmap が「設定形式・content ディレクトリ・出力ディレクトリは公式ドキュメントで確定」と要求
- **Sources Consulted**: https://zensical.org/docs/setup/basics/ , https://zensical.org/docs/create-your-site/ , https://zensical.org/docs/compatibility/mkdocs/
- **Findings**:
  - 設定は `zensical.toml`。全設定を `[project]` スコープに置く。`extra` は `[project.extra]`
  - `mkdocs.yml` も「ほぼすべての設定」がそのまま動く（互換モード）
  - `docs_dir`: 設定ファイルからの相対パス。例は `"docs"`。**`"."` は不可**
  - `site_dir`: 設定ファイルからの相対パス。既定 `site`
  - `use_directory_urls`: 既定 `true`（`logs/2026-11-23.md` → `logs/2026-11-23/`）
  - `exclude_docs`: **ドットファイル・ドットディレクトリ・トップレベル `templates/` は既定で除外**
  - `site_url`: 正規 URL。instant navigation 等に必要。ベースパスを別設定する項目はドキュメント上に無い
  - `zensical new` は `.github/workflows/docs.yml`、`docs/`、`zensical.toml` を生成する
- **Implications**: 新規プロジェクトなので互換モードではなく `zensical.toml` を採用。`docs_dir = "content"`、`site_dir = "site"`、`site_url = "https://kjman678.github.io/what_i_learned/"`。サブパスでの動作は `site_url` と相対リンク生成に依存するため、ビルド成果物で実地確認する（未検証 → 実装タスクで確認）

### hooks / プラグイン
- **Context**: roadmap は「`hooks:` が使える前提を置かない（使う場合は公式で確認）」
- **Sources Consulted**: https://zensical.org/docs/compatibility/mkdocs/migration/
- **Findings**: 「The following mkdocs.yml settings are not yet supported in Zensical: hooks」。プラグインは置き換え実装が順次提供されている段階
- **Implications**: hooks は使わない。ビルド前生成は「ビルド前に Python スクリプトを実行」で行う（roadmap 方針どおり）。この spec はその差し込み口（ビルドスクリプトの生成段）だけを用意する

### ビルドコマンドと検証（strict）
- **Sources Consulted**: https://zensical.org/docs/usage/build/ , https://zensical.org/docs/setup/validation/
- **Findings**:
  - `zensical build [--config-file/-f] [--clean/-c] [--strict/-s]`。`--clean` はキャッシュを消す
  - 検証は既定で `invalid_links` と `invalid_link_anchors` が有効（警告）。`--strict` または `[project] strict = true` で、問題を全件報告したのちビルドを中断し **終了コード 1**
- **Implications**: CI と手元のビルドは `zensical build --clean --strict` とし、リンク切れで公開を止める（6.3）

### 公開（GitHub Pages）
- **Sources Consulted**: https://zensical.org/docs/publish-your-site/
- **Findings**: 公式ワークフローは `main`/`master` への push で、`actions/configure-pages@v6` → `actions/checkout@v7` → `actions/setup-python@v6` → `pip install zensical` → `zensical build --clean` → `actions/upload-pages-artifact@v5`（`site`）→ `actions/deploy-pages@v5`。権限は `contents: read`、`pages: write`、`id-token: write`。Pages の Source を GitHub Actions にすることが前提。CI キャッシュは「キャッシュ機能を改修中のため現時点では非推奨」
- **Implications**: 公式構成を踏襲しつつ、pip の代わりに uv（`uv sync --frozen`）でロックファイルどおりに入れ、ビルドは共通スクリプト経由にする。Zensical のビルドキャッシュは CI でキャッシュしない。アクションのメジャーバージョンは実装時に最新を確認して固定する（未検証 → 実装タスクで確認）

### インストールとバージョン固定
- **Sources Consulted**: https://zensical.org/docs/get-started/ , https://pypi.org/pypi/zensical/json
- **Findings**:
  - uv の場合 `uv add --dev zensical`、実行は `uv run zensical`
  - **uv の symlink link-mode は非対応**
  - PyPI 最新 `0.1.3`、`requires_python >=3.11`。依存: `click, jinja2, markdown, pathspec, pygments, pymdown-extensions, pyyaml>=6.0.2, tomli, zensical-ui==0.0.43`
  - 依頼文では「0.1.0（2026-11）」とされていたが、調査時点の PyPI 最新は 0.1.3。差異を記録する
- **Implications**: `pyproject.toml` で `zensical==0.1.3` と完全一致で固定し、`uv.lock` をコミットする。別の版に上げる場合は、先に設計（技術スタックの版）を改訂してから固定し直す（バージョン更新は Revalidation Trigger）。`wil.records` の frontmatter 解析に使う PyYAML は Zensical の推移的依存として既に入るが、`wil` が直接使うため `pyyaml` を直接依存として明示する

### frontmatter・タイトル・タグ
- **Sources Consulted**: https://zensical.org/docs/authoring/frontmatter/ , https://zensical.org/docs/setup/tags/ , https://zensical.org/docs/setup/navigation/ , 第三者ミラーの title 優先順位記述（Web 検索結果）
- **Findings**:
  - 認識される frontmatter: `title`、`description`、`icon`、`status`、`template`、`hide`。**任意のキーの追加は許容**（テンプレートから `page.meta` で参照可能）
  - tags は**組み込みのネイティブ実装**。`[project.plugins.tags]` で有効化。frontmatter は `tags:` のリスト。タグは追加設定なしで検索対象になる
  - ナビゲーション未指定時はフォルダ構造から生成。並び順はドキュメントに記載なし
  - タイトルの決定順（第三者ミラー）: nav のタイトル → frontmatter `title` → 本文の最初の H1 → ファイルのベース名。公式ドキュメント上でベース名からの変換規則（MkDocs のように `-` を空白に置換するか）は確認できず
- **Implications**: 書き手に `title` や H1 を要求しない（書く手間を増やさない）。H1 が無ければタイトルはファイル名由来になり、`2026-11-23` もしくは `2026 11 23` のどちらでも日付は識別できる（3.2 を満たす）。実際の表示は実装タスクで確認する。未知キーは許容（Zensical 側の `hide` 等も使えるようにするため）

### 言語と検索
- **Sources Consulted**: https://zensical.org/docs/setup/language/ , https://zensical.org/docs/setup/search/
- **Findings**: `[project.theme] language = "ja"` が「Complete」として対応。HTML の `lang` 属性に反映されるかはドキュメントに明記なし。検索は既定で有効、ただし「currently only available in English」
- **Implications**: `language = "ja"` を設定し、生成 HTML の `<html lang="ja">` を実装タスクで確認する。日本語検索の品質はこの spec では保証せず、リスクとして記録（改善は後続 spec で判断）

### コミット前検査（pre-commit）
- **Context**: 5.1〜5.6
- **Findings**（一般知識。バージョンは実装時に確認）:
  - `pre-commit/pre-commit-hooks` に `check-added-large-files`（`--maxkb`）と `detect-private-key` がある
  - `gitleaks` は公式に pre-commit フック（id `gitleaks`、`language: golang`）を提供。pre-commit が Go ツールチェーンを自動で用意する
  - pre-commit の `language: fail` で、特定パターンのファイル名を無条件に拒否できる
  - `language: system` のローカルフックで `uv run` 経由の自前検証を呼べる
- **Implications**: 秘密情報は gitleaks + detect-private-key、大きなファイルは `--maxkb=500`、`.env` 系は fail フック、公開ディレクトリの許可外ファイルとログ書式は `wil.records` の CLI で検出する

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 通常ページ + 共有パーサ（採用） | `content/logs/YYYY-MM-DD.md` を通常ページとして公開。検証・読み取りは `wil.records` 1 モジュール | 書く手間最小、下流が同じ解釈で読める、プラグイン非依存 | 一覧は 01 時点では既定ナビのみ | roadmap 01/02 境界どおり |
| blog プラグイン | 投稿として公開 | アーカイブが自動 | frontmatter に `date` 必須、01/02 境界違反 | 却下 |
| hooks でビルド時検証 | MkDocs hooks で検証 | ビルドに統合 | Zensical は hooks 未対応 | 却下 |
| 検証を pre-commit / CI で別実装 | 正規表現等で別々に検査 | 依存が少ない | 規則が二重化しずれる（2.9 違反） | 却下 |

## Design Decisions

### Decision: 公開コンテンツディレクトリを `content/` にする
- **Context**: `docs/` は既定値だが、HEAD に非公開文書 `docs/superpowers/*` が追跡されている。`docs_dir` は `.` 不可
- **Alternatives Considered**: 1. `docs/` を使い `exclude_docs` で除外 2. `site_src/` などの別名 3. `content/`
- **Selected Approach**: `docs_dir = "content"`、手書きログは `content/logs/`、トップは `content/index.md`
- **Rationale**: 除外パターンに頼らず「ディレクトリに入れたものだけが公開される」を構造で保証できる（4.1, 4.2）。`docs/` は非公開設計文書の置き場として steering と整合
- **Trade-offs**: Zensical 既定と異なるため設定が 1 行増える
- **Follow-up**: log-index の生成ページは `content/` 配下の別サブディレクトリになる（名前は log-index が決める）

### Decision: 検証と読み取りを 1 モジュール `wil.records` に集約し、CLI も同モジュールに置く
- **Context**: 2.9（同じ規則）、7.5、steering「ログのパースは `wil.records` 以外で再実装しない」
- **Selected Approach**: `src/wil/records.py` に型・パース・検証・許可リスト・CLI（`python -m wil.records`）を置く。pre-commit はファイル名を渡して呼び、ビルドは引数なしで全体を検査する
- **Rationale**: 1 か所に規則がある。モジュール数を増やす理由（複数実装・独立した変更理由）が無い
- **Trade-offs**: ファイルが 1 つで約 200 行になる見込み。肥大化したら分割する

### Decision: 単一のビルドスクリプト `scripts/build.sh`
- **Context**: 6.5（手元と CI で同じ手順、生成段の差し込み口）
- **Alternatives Considered**: 1. CI YAML に直接書く 2. Makefile 3. Python のビルドモジュール 4. シェルスクリプト
- **Selected Approach**: `scripts/build.sh` が「検証 → 生成段（現時点では空、コメントで位置を明示）→ `zensical build --clean --strict`」を順に実行し、どれかが失敗したら非ゼロで終了
- **Rationale**: 依存を増やさず、手元・CI の両方から同じ 1 コマンドで呼べる。log-index は生成段に 1 行足すだけでよい
- **Trade-offs**: Windows ネイティブ環境は対象外（オーナーは macOS）

### Decision: frontmatter 未知キーは許容、`tags` は 1 個以上必須
- **Context**: 「書く手間を増やさない」「厳しすぎる書式は anti-goal」と、下流（tech-timeline 等）が tags に依存すること
- **Selected Approach**: `tags` は空でない文字列のリスト（1 個以上）。単一文字列 `tags: aws` はエラー（Zensical のタグ表示が崩れるため）。`summary` は改行なしの文字列。他キーは無視
- **Rationale**: 必須は 1 項目のみ。Zensical の `hide` 等の正当な利用を妨げない
- **Trade-offs**: タイポした `tag:` は「`tags` が無い」として検出される（未知キー許容でも見逃さない）

### Decision: ドットファイルは検証対象外
- **Context**: macOS の `.DS_Store` 等が `content/` に生じうる。Zensical はドットファイルを既定で公開から除外する
- **Selected Approach**: 許可リスト検査はドットで始まるファイル・ディレクトリを無視する。`.DS_Store` と `.env` 系は `.gitignore` で、`.env` 系のコミットは pre-commit の fail フックで止める
- **Rationale**: 公開されないファイルで誤検出しない

### Decision: 見出し区間の抽出は ATX 見出しのみ、フェンス内は除外
- **Context**: 7.3。knowledge-mcp が見出し単位で抜粋する
- **Selected Approach**: 行頭 `#`〜`######` + 空白の ATX 見出しで区切る。` ``` ` / `~~~` のフェンス内は見出しとみなさない。Setext 見出し（下線形式）は扱わない。最初の見出しより前の本文はレベル 0・見出し文字列なしの区間とする
- **Rationale**: Markdown パーサを追加せず標準ライブラリで足りる。ログの見出しは ATX で書く運用（手順書に記載）

## Risks & Mitigations
- 組み込み検索が英語のみ（日本語の分かち書き非対応の可能性） — 3.8 は「検索を提供する」までとし、品質改善は後続 spec。リスクとして記録
- ファイル名由来タイトルの見た目（`2026 11 23` になる可能性） — 日付は識別可能なので要件は満たす。実装タスクで実表示を確認し、見た目の改善は site-design / log-index に委ねる
- サブパスでのアセット・リンク解決 — ビルド成果物に `/assets` などルート絶対パスが無いことを実装タスクで検査する
- Zensical pre-1.0 の挙動変更 — 完全一致のバージョン固定と `uv.lock`。更新は手動で行い、ビルドで確認する
- Zensical のキャッシュディレクトリ名がドキュメントで未確認 — 実装タスクで初回ビルド後に生成物を確認し `.gitignore` に追加する
- 旧 Astro 生成物が index に残っている — `.gitignore` で再混入を防ぎ、除去はオーナーが行う（手順書に記載）

## 統合確認の結果（タスク 4.2）
- ファイル名由来タイトル: H1 の無いログは `<title>` とナビ表示が `2026 11 23`（`-` が空白に置換）。日付は識別可能で 3.2 を満たす。H1 入りの一時ログでは H1（`見出し`）がタイトルになり、URL は `logs/2026-11-24/` のまま
- サブパス: ルート絶対パスは `404.html` のみで、すべて `/what_i_learned/` 接頭辞付き（`site_url` 由来）。`"/assets` 形式は無い。他ページは相対パス
- キャッシュ: Zensical はリポジトリ直下に `.cache/` を作る（中に `*` だけの `.gitignore` を自前で置くため元々 untracked には出ない）。明示のため `.gitignore` に `.cache/` を追加
- 日本語検索の品質（記録のみ）: `search.json` の config は `lang: ["ja"]`、区切りは空白・記号のみ（`[\s\-_,:!=\[\]()\\"`/]+|\.(?!\d)`）。分かち書きをしないため、空白の無い日本語文は長い 1 トークンとして索引され、文中の部分語での一致は期待できない（英字語・空白区切り語・見出し単位では見つかる見込み）。ブラウザでの実検索は未実施。改善は後続 spec

## References
- [Zensical Basics](https://zensical.org/docs/setup/basics/) — 設定項目、`docs_dir` / `site_dir` / `exclude_docs`
- [Create your site](https://zensical.org/docs/create-your-site/) — プロジェクト構成、`site_url`
- [Publish your site](https://zensical.org/docs/publish-your-site/) — GitHub Pages ワークフロー
- [Get started](https://zensical.org/docs/get-started/) — uv でのインストール、symlink 非対応
- [Build](https://zensical.org/docs/usage/build/) — CLI オプション
- [Validation](https://zensical.org/docs/setup/validation/) — strict モードと終了コード
- [MkDocs compatibility](https://zensical.org/docs/compatibility/mkdocs/) / [Migration](https://zensical.org/docs/compatibility/mkdocs/migration/) — hooks 未対応
- [Front matter](https://zensical.org/docs/authoring/frontmatter/) / [Tags](https://zensical.org/docs/setup/tags/) / [Navigation](https://zensical.org/docs/setup/navigation/)
- [Language](https://zensical.org/docs/setup/language/) / [Search](https://zensical.org/docs/setup/search/)
- [PyPI zensical](https://pypi.org/project/zensical/) — 0.1.3、依存一覧
