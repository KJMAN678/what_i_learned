# Research & Design Decisions

## Summary
- **Feature**: `site-design`
- **Discovery Scope**: Extension（daily-log-page・log-index の設計契約の上に乗る見た目の拡張。実装コードはまだ無く、上流の design.md / research.md を既存システムとして扱う。Zensical は pre-1.0 のため、テーマ関連の設定は公式ドキュメントで確認した）
- **Key Findings**:
  - Zensical の見た目は `zensical.toml` の `[project.theme]`（`palette`、`font`、`features`）と `[project] extra_css` で調整できる。追加 CSS は `docs_dir` 内に置き、`docs_dir` 基準のパスで登録する。テンプレート上書き（`custom_dir`）は使わずに要件を満たせる
  - 書体は `font = false` で Google Fonts の読み込みを止められ、CSS 変数 `--md-text-font` / `--md-code-font` で日本語のシステム書体を指定できる（`font-family` を直接書くとフォールバックが効かなくなると公式が注意）
  - 追加 CSS を `content/` に置くと、上流 `wil.records.ALLOWED_PATTERNS` の許可リスト検査（pre-commit とビルドの検証段）に掛かる。狭いパターン 1 つの追加が必要（上流が追加を許可している）
  - タグや本文の HTML クラス名は公式に記載が無い。契約に含めず、実装時に生成 HTML で確認する
  - ナビの日本語区分名は明示 `nav`（`{ "区分名" = "パス" }`）でだけ指定できる。トップと一覧ページだけを並べれば、ログが増えてもナビは伸びず、固定版 0.1.3 の `--strict` も通る（手元で検証）

## Research Log

### 上流契約の確認（daily-log-page / log-index）
- **Context**: brief で「見た目はこの spec が一元的に所有し、他 spec はページ構造のみ」と指定。上流の所有物に触れる範囲を確定する
- **Sources Consulted**: `.kiro/specs/01-daily-log-page/design.md`、`.kiro/specs/01-daily-log-page/research.md`、`.kiro/specs/01-daily-log-page/requirements.md`、`.kiro/specs/02-log-index/design.md`、`.kiro/specs/02-log-index/research.md`
- **Findings**:
  - `zensical.toml` は daily-log-page 所有。`[project]` に `site_name`、`site_url`、`docs_dir = "content"`、`site_dir = "site"`、`nav` 未指定。`[project.theme] language = "ja"`、`[project.plugins.tags]`。daily-log-page は「テーマ上書き、CSS、テンプレート上書き（site-design）」を Out of Boundary に明記
  - `docs_dir` / `site_dir` / `site_url` の変更は全下流の Revalidation Trigger。本 spec は触れない
  - `wil.records.ALLOWED_PATTERNS` は公開許可リストの唯一の定義。初期値 `index\.md`、`logs/\d{4}-\d{2}-\d{2}\.md`、log-index が `generated/.+\.md` を追加。「後続 spec が公開ファイルの種類を増やすときはここに追加する」と上流が許可
  - 検証 CLI（引数なし）は `content/` 以下の全ファイル（ドットファイル除く）を検査し、pre-commit は `files: ^content/` で同じ検査を呼ぶ。`.css` を置くと許可外として失敗する
  - `content/index.md` は daily-log-page 所有（説明 1〜2 文と「左のナビゲーションからログを選ぶ」旨）。log-index が末尾に `[学習ログ一覧](generated/log-index.md) から、すべてのログを新しい順に見られます。` を追記
  - 一覧ページ `content/generated/log-index.md`: H1「学習ログ一覧」、`## YYYY 年度`、`### YYYY 年 M 月`、各行 `- [YYYY-MM-DD](../logs/YYYY-MM-DD.md) — summary（tags: a, b）`。クラス等の印は無い。ナビのラベル・位置は site-design に委ねられている
  - `README.md` は daily-log-page 所有。log-index は節を追記する方式
  - CI は `uv run pytest` → `./scripts/build.sh`（検証 → 生成 → `zensical build --clean --strict`）→ デプロイ。pytest が失敗すれば公開されない
- **Implications**:
  - 見た目の定義ファイルは `content/stylesheets/extra.css` の 1 つ。許可リストにはそのファイル名だけを許す狭いパターン `r"stylesheets/extra\.css"` を追加する（`.+\.css` のような広いパターンは「意図しないファイルを公開しない」原則を弱めるため使わない）。`templates/` 配下は Zensical の既定除外に当たるため置かない
  - `zensical.toml` の変更は `[project] extra_css`・`nav` と `[project.theme]` の `palette`・`font`・`features` の追加のみ（`nav` の所有は roadmap の改訂で本 spec に移った）
  - トップページは説明文を書き換えるが、log-index の追記行は 1 文字も変えずに残す

### 配色・ライト/ダーク
- **Context**: Requirement 4（端末設定に従う初期配色、手動切り替え、日本語の操作名）
- **Sources Consulted**: https://zensical.org/docs/setup/colors/
- **Findings**:
  - `scheme = "default"`（ライト）/ `"slate"`（ダーク）。`primary`・`accent` は色名（例 `indigo`）または `custom`
  - 切り替えは `[[project.theme.palette]]` の配列。各要素に `toggle.icon` と `toggle.name`。`name` は切り替えボタンの `title` 属性とツールチップになる
  - `media = "(prefers-color-scheme: light)"` / `"(prefers-color-scheme: dark)"` で端末設定と結び付け、「最初に一致したクエリが既定の配色」
  - `toggle.icon` はテーマ同梱のアイコンでなければビルドが失敗する。例は `lucide/sun`、`lucide/moon`
  - 独自色は `primary = "custom"` と CSS 変数（`--md-primary-fg-color` 等）で行う
- **Implications**:
  - 2 要素の palette（ライト: `media` light + `default`、ダーク: `media` dark + `slate`）。`toggle.name` は日本語（「ダークモードに切り替え」「ライトモードに切り替え」）
  - 色は組み込みの色名 `indigo` から始め、コントラスト不足が実測で見つかった場合だけ、追加 CSS の配色別セレクタで該当変数を上書きする
  - 手動切り替えの保持（4.4）は公式に記載が無い。Material for MkDocs 由来の挙動（ブラウザに保存）を前提にし、実装時に確認する

### 書体
- **Context**: Requirement 1.1（日本語に適した書体）、1.7（外部から書体を読み込まない）
- **Sources Consulted**: https://zensical.org/docs/setup/fonts/
- **Findings**:
  - `font.text` / `font.code` は Google Fonts 名。`font = false` で Google Fonts を読み込まず、システム書体にフォールバック（プライバシー対応として公式が言及）
  - 独自書体は CSS 変数 `--md-text-font` / `--md-code-font` で指定する。`font-family` を直接書くとシステム書体のフォールバックが無効になるため避けるよう公式が注意
- **Implications**:
  - `font = false`。`--md-text-font` に日本語のシステム書体を並べる（例 `"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic UI", Meiryo`）。Web フォントを配信しないため追加ファイルも外部通信も無い
  - `--md-code-font` は既定（テーマのシステム等幅フォールバック）のままで足りるかを実装時に確認し、足りない場合だけ指定する

### 追加 CSS・テンプレート上書き
- **Context**: Requirement 8（見た目の定義を 1 か所に）、brief（テンプレート上書きは最小限、独自 JS なし）
- **Sources Consulted**: https://zensical.org/docs/customization/
- **Findings**:
  - 追加 CSS は `docs` ディレクトリに置き、`[project] extra_css = ["stylesheets/extra.css"]` で登録する
  - `extra_javascript` もあるが本 spec では使わない
  - `[project.theme] custom_dir = "overrides"` でテンプレート・パーシャルを上書きできる。公式は `base.html` より `main.html` の上書きを推奨（`base.html` は将来変わりやすい）。MiniJinja のため Python 関数は呼べない
- **Implications**: 要件はすべて設定と追加 CSS で満たせるため、`custom_dir` は使わない（テンプレート上書き 0 件）。pre-1.0 の HTML 構造変更による破損範囲を CSS のセレクタだけに限定する

### ナビゲーション関連の機能フラグ
- **Context**: Requirement 6（上部へ戻る、前後ページのリンク）、log-index から委ねられたナビのラベル・位置
- **Sources Consulted**: https://zensical.org/docs/setup/navigation/ 、https://zensical.org/docs/setup/footer/ 、https://zensical.org/docs/authoring/frontmatter/
- **Findings**:
  - `features` に `navigation.top`（上部へ戻るボタン）、`navigation.footer`（前後ページのリンク）がある。他に `navigation.instant`、`navigation.tabs`、`navigation.sections`、`navigation.expand`、`navigation.indexes`、`toc.follow` 等。既定で有効かどうかは記載が無く、オプトインと読める
  - `nav` 未指定時はフォルダ構造からナビが作られる。フォルダ名からの区分名の決め方・並び順は記載なし
  - front matter `hide` は `navigation`、`toc`、`path`、`footer`、`feedback`、`tags` を受け付ける
- **Implications**:
  - `features = ["navigation.top", "navigation.footer"]` のみ。`navigation.instant` はページ遷移の挙動を変え、確認範囲を増やすため採用しない
  - ナビの構成（区分名・並び・長さ）は roadmap の改訂で本 spec の所有になった。次節「ナビゲーションの構成」で決める

### ナビゲーションの構成（区分名・長さ）
- **Context**: Requirement 10、6.2。roadmap がナビの区分名・並び・長さを本 spec の所有とした。ログ（`content/logs/YYYY-MM-DD.md`）と技術別ページは際限なく増え、生成ページは gitignore されている
- **Sources Consulted**: https://zensical.org/docs/setup/navigation/ 、https://zensical.org/docs/setup/validation/ 、固定版 zensical 0.1.3 での手元ビルド（scratchpad の使い捨てプロジェクト）
- **Findings**（公式文書）:
  - 明示 `nav` は `{ "Title" = "path" }` の組で書き、パスは `docs_dir` 相対。入れ子のリストのキーが区分名になる
  - 「Markdown ページに解決できない文字列は URL として扱う」と記載。参照先が無くてもエラーにならない
  - `not_in_nav` でページを既定ナビから外せ、外したページも「ビルドされ、検索とサイトマップに含まれる」
  - `nav` 未指定時はフォルダ構造からナビを作る。フォルダ名からの区分名の決め方・並び順は記載なし。`.pages`（awesome-nav 形式）の対応は記載なし
  - 機能フラグ `navigation.sections`・`navigation.tabs`・`navigation.expand`・`navigation.indexes`・`navigation.prune` は表示の仕方（グループ化、タブ化、展開、索引ページ、HTML の刈り込み）を変えるだけで、区分名は変えられない
  - Validation の項目は `invalid_links`・`invalid_link_anchors`（既定で有効）と非推奨の参照系だけで、ナビに無いページや `nav` の参照先は対象に無い。`--strict` は報告した問題があればビルドを中断し終了コード 1
- **Findings**（0.1.3 で `nav = [{"ホーム"="index.md"},{"学習ログ一覧"="generated/log-index.md"},{"未実装"="generated/missing.md"}]`、`features = ["navigation.footer"]`、ナビに無い `logs/*.md` 2 件で `zensical build --clean --strict`）:
  - 終了コード 0、出力は「No issues found」。ナビに無いページについての報告は無い
  - ログページ 2 件はビルドされる（`site/logs/<日付>/index.html`）。ナビにはログの日付が並ばず、区分名は日本語で出る
  - ログページには前後ページのリンク（footer）が出ない。ナビに載るページ同士にだけ出る
  - 存在しない `generated/missing.md` はナビに `./generated/missing.md` という無効なリンクとして出て、`--strict` でも検出されない
- **Implications**:
  - 明示 `nav` にトップと一覧ページだけを書く。区分名を日本語にでき、ナビは最大 4 項目で止まる（10.1、10.2）。`.pages` や機能フラグでは区分名を変えられないため選ばない
  - gitignore された生成ページでも `--strict` は壊れない。`nav` はビルド時点のディスク上のファイルで解決され、build.sh と CI は常に生成後にビルドする。git の追跡状況は関係しない
  - 危険は逆向き（生成ページが無いと黙って無効なリンク）。pytest は生成前に動くので `nav` の形だけを検査し、参照先の存在はビルド後の確認で見る。生成器が無いページの項目は先に書かない
  - 6.2 は「ナビに載るページ」に範囲を絞る。ログ間の移動は一覧ページから行う
  - 将来の版でナビに無いページが警告になった場合は `not_in_nav` で抑える

### テーマのバリアント
- **Context**: 既定の見た目の土台
- **Sources Consulted**: Web 検索（"zensical theme variant classic modern"）の結果要約、https://zensical.org/docs/setup/basics/
- **Findings**: `modern`（既定）と `classic`（Material for MkDocs と同じ見た目、`variant = "classic"`）の 2 種。両者は同じ HTML 構造で、CSS の調整が期待どおりにならない場合は `classic` への切り替えが推奨されている
- **Implications**: 既定の `modern` のまま（設定しない）。追加 CSS が効かない場合の逃げ道として `classic` を記録する

### タグ・日付の表示
- **Context**: Requirement 2
- **Sources Consulted**: https://zensical.org/docs/setup/tags/
- **Findings**: タグは各ページの下部に表示される。HTML / CSS のクラス名は公式に記載が無い。タイトルが無いページのタイトルはファイルのベース名（日付）になる（上流 research.md）
- **Implications**: タグの見た目を整える CSS のセレクタは、実装時に生成 HTML を確認して決める。クラス名は他 spec との契約に含めない

### 固定版との差
- **Context**: 上流は `zensical==0.1.3` に完全一致で固定。参照した公式ドキュメントは調査時点の最新版の記述
- **Findings**: ドキュメントに版ごとの対応表は無い
- **Implications**: 次の項目は固定版での最初のビルドで確認し、失敗時の代替を決めておく。固定版は上げない（版の更新は daily-log-page の Revalidation Trigger）
  - `toggle.icon` の `lucide/sun` / `lucide/moon`: ビルド失敗時は `fontawesome/solid/sun` / `fontawesome/solid/moon` に替える（fontawesome はフッターの例で同梱が示されている）
  - `font = false`: 効かない（Google Fonts へのリクエストが出る）場合は設計に戻る
  - 配列形式の `[[project.theme.palette]]` と `media`: 切り替えボタンが出ない場合は設計に戻る

### アクセシビリティ
- **Context**: Requirement 7
- **Sources Consulted**: WCAG 2.2（1.4.3 コントラスト最低限 4.5:1、1.4.11 非テキストのコントラスト 3:1、2.4.7 フォーカスの可視化、1.4.1 色の使用）
- **Findings**: 本文リンクを色だけで区別するには周囲の文字とのコントラスト 3:1 が別途必要になるため、下線で区別するほうが単純
- **Implications**: 本文リンクに下線、`:focus-visible` に 2px のアウトライン。コントラストはブラウザの開発者ツールのコントラスト表示で両配色を実測する

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| テーマ設定 + 追加 CSS 1 ファイル（採用） | `[project.theme]` の組み込み機能と `content/stylesheets/extra.css` だけで調整 | テンプレート非依存、pre-1.0 の変更に強い、変更点が 2 ファイル | CSS のセレクタが生成 HTML のクラスに依存 | brief の方針どおり |
| テンプレート上書き（`custom_dir`） | `main.html` やパーシャルを上書きしてタグ・日付の HTML を変える | 表示を細かく制御できる | pre-1.0 で壊れやすい、確認範囲が増える | 要件に不要のため却下 |
| ページ側にクラスを付ける約束（`attr_list` 等） | 他 spec が生成 Markdown に `{ .class }` を付ける | ページごとの細かい装飾 | 他 spec に見た目の責務が漏れる、tech-timeline の構造に依存 | 却下。通常の文書構造だけで同じ見た目にする |
| Google Fonts で日本語 Web フォント | `font.text = "Noto Sans JP"` | 環境間で見た目が揃う | 第三者への通信、日本語フォントは重い | 却下（1.7） |
| `primary = "custom"` で独自配色 | 配色変数をすべて CSS で定義 | 色を自由に選べる | 両配色の全変数を管理する手間 | 却下。色名 + 不足時のみ部分上書き |

## Design Decisions

### Decision: 見た目の定義は `content/stylesheets/extra.css` の 1 ファイル、許可リストは狭く追加
- **Context**: 8.3、8.5。公開許可リストの原則（意図しないファイルを公開しない）
- **Alternatives Considered**:
  1. `r"stylesheets/.+\.css"` を許可 — 将来のファイル追加は楽だが、許可範囲が広がる
  2. `r"stylesheets/extra\.css"` のみ許可 — ファイルを増やすたびに許可リストの変更が要る
- **Selected Approach**: 2
- **Rationale**: 見た目の定義を 1 か所に集める要件（8.3）と一致し、許可範囲の拡大を最小にする
- **Trade-offs**: CSS を分割したくなったら許可リストの変更が必要（その時に判断する）
- **Follow-up**: 実装時に、`content/stylesheets/other.css` を置くと検証が失敗することを確認する

### Decision: 他 spec との約束は「通常の文書構造だけを書く」
- **Context**: 8.1、8.2、3.4。tech-timeline が並行して設計されており、その構造を前提にできない
- **Selected Approach**: CSS は `h1`〜`h4`、`ul`/`ol` の入れ子、`a`、`table`、`code`/`pre` などの要素型と、テーマの本文領域だけを対象にする。ページ固有のクラスや構造を前提にしない。他 spec はクラス・インライン style・`<style>`・独自 CSS ファイルを持たない
- **Rationale**: 新しいページが追加されても CSS の変更が要らない。見た目の責務が他 spec に漏れない
- **Trade-offs**: ページ単位の特別な装飾はできない。必要になった場合は本 spec の改訂として扱う

### Decision: 書体はシステムの日本語書体
- **Context**: 1.1、1.7
- **Selected Approach**: `font = false` + `--md-text-font` に日本語システム書体の列
- **Rationale**: 外部通信なし、追加ファイルなし、表示が速い
- **Trade-offs**: OS により書体が異なる（読みやすさの要件は満たす）

### Decision: 明示 `nav` にトップと一覧ページだけを日本語名で並べる
- **Context**: 10.1〜10.3、6.2。roadmap がナビの構成を本 spec の所有とした
- **Alternatives Considered**:
  1. 既定ナビ（`nav` 無指定）+ 機能フラグ — 区分名がフォルダ名由来で日本語にできず、ログの数だけ項目が増える
  2. `.pages` 形式 — Zensical の公式文書に対応の記載が無い
  3. 明示 `nav` にトップと一覧ページだけ — 区分名と並びを固定でき、ログは `nav` に書かずに済む
- **Selected Approach**: 3。後続の生成 spec は `nav` 末尾に 1 項目を追記する（ナビ契約）
- **Rationale**: 設定 1 キーだけで済み、0.1.3 の `--strict` で成功を確認済み。ログを書く手間を増やさない
- **Trade-offs**: ログページに前後ページのリンクが出なくなる（6.2 の範囲を絞る）。ログ間の移動は一覧ページ経由。生成ページが欠けると無効なリンクになるが `--strict` では検出されない（ビルド後の確認で見る）
- **Follow-up**: tech-timeline・learning-recommendation の設計にある「`nav` は無指定のまま」を、ナビ契約に従う 1 項目の追記に読み替える必要がある（両 spec の Revalidation）

### Decision: 設定の回帰をテストで止める
- **Context**: 9.2、9.3、8.4、8.5
- **Selected Approach**: `tests/test_site_design.py` が `zensical.toml` を `tomllib` で読み、`extra_css` の参照先の存在、`language = "ja"`、tags プラグイン、2 配色と日本語の切り替え名、`font = false`、`custom_dir`・`extra_javascript` が無いこと、許可リストが CSS 1 ファイルだけを許すことを検査する。CI は pytest を build より先に実行するため、失敗すれば公開されない
- **Rationale**: CSS 自体はロジックを持たないので単体テストせず、壊れやすい「参照の切れ」と「上流設定の消失」だけを機械的に止める

## Synthesis Outcomes
- **Generalization**: 日付・タグ・一覧・今後のページの見た目は、すべて「本文領域内の要素型に対する共通の規則」として 1 つの CSS に集約できる。ページ種別ごとの規則は作らない
- **Build vs. Adopt**: 配色切り替え・上部へ戻る・前後リンク・書体のフォールバックはテーマ組み込み機能を採用。自作するのは本文の細部（行間、入れ子リスト、リンク下線、フォーカス枠、タグのラベル）の CSS のみ
- **Simplification**: テンプレート上書き 0、独自 JS 0、Web フォント 0、新規依存 0。CSS は既定で要件を満たしている項目について規則を書かない

## Risks & Mitigations
- 生成 HTML のクラス名が版更新で変わり CSS が効かなくなる — セレクタを本文領域と要素型に限定し、手順書の確認項目で検出する。版更新は上流の Revalidation Trigger
- `lucide/*` アイコンが固定版に無くビルドが失敗する — `fontawesome/solid/sun` / `moon` に替える
- 配色の保持（4.4）が固定版で働かない — 実装時に確認し、働かない場合は 4.4 を満たせない旨を記録して要件の見直しに戻る（独自 JS は追加しない）
- 組み込み色のコントラストが 4.5:1 / 3:1 に届かない — 追加 CSS の配色別セレクタで該当変数のみ上書きする
- 生成ページが欠けた状態でビルドすると、ナビの項目が黙って無効なリンクになる — build.sh は常に生成後にビルドする。実装時と表示確認でナビの各項目の HTML の存在を確認し、生成器の無いページは `nav` に書かない
- 将来の版でナビに無いページが `--strict` の対象になる — `not_in_nav` で `logs/` 等を外す

## References
- [Colors](https://zensical.org/docs/setup/colors/) — palette、切り替え、media、独自色
- [Fonts](https://zensical.org/docs/setup/fonts/) — `font = false`、CSS 変数
- [Customization](https://zensical.org/docs/customization/) — `extra_css`、`extra_javascript`、`custom_dir`
- [Navigation](https://zensical.org/docs/setup/navigation/) — `features` の一覧、`nav`、`not_in_nav`
- [Validation](https://zensical.org/docs/setup/validation/) — 検証項目と `--strict`
- [Footer](https://zensical.org/docs/setup/footer/) — `navigation.footer`
- [Front matter](https://zensical.org/docs/authoring/frontmatter/) — `hide`
- [Tags](https://zensical.org/docs/setup/tags/) — タグの表示位置
- [Basics](https://zensical.org/docs/setup/basics/) — `[project]` スコープ
- WCAG 2.2 — 1.4.1、1.4.3、1.4.11、2.4.7
