# Research & Design Decisions: learning-recommendation

## Summary
- **Feature**: `learning-recommendation`
- **Discovery Scope**: Extension（上流 3 spec の設計契約の上に、生成器 1 つと手元専用の skill 1 つを足す。リポジトリは未実装で、上流はすべて設計契約として参照する）
- **Key Findings**:
  - 「未学習の領域」は LLM を要するが、公開サイトは静的で実行時に LLM も API キーも持てない。オーナーの手元で生成し、承認した結果を**公開コンテンツの外**にデータとしてコミットし、ビルド前生成でページにするのが、上流の全契約（`content/generated/` は毎回削除、`ALLOWED_PATTERNS` 不変、生成器は純粋関数）を変えずに済む唯一の形
  - tech-timeline の下流契約は import してよい名前を限定している（`build_index`、`tech_key`、`tag_key`、`Tech`、`TechEntry`、`AliasError`、`INDEX_PAGE`、`PAGE_DIR`）。`check_aliases` と `slug` は使えないため、別名表の検査は `build_index` の `AliasError` で受け、ページ名は `Tech.page` のファイル名部分から得る
  - 「学習済みの内容がログの事実に基づく」ことの機械検査は、日付が技術の学習日に含まれることだけでは「リンクが正しい」までしか示せない。要点ごとにログ本文からの短い引用を持たせ、正規化した部分一致で照合することで、根拠の所在を決定的に検査できる。要約の妥当性は検査できないため、オーナーの承認で確かめる

## Research Log

### 上流契約（daily-log-page / log-index / tech-timeline）
- **Context**: 再実装を避け、上流契約だけで成り立つかを確認する
- **Sources Consulted**: `.kiro/specs/01-daily-log-page/design.md`、`.kiro/specs/02-log-index/design.md`、`.kiro/specs/06-tech-timeline/design.md`
- **Findings**:
  - `wil.records`: `load_records()` は日付昇順の `list[Record]`、不正時 `RecordsInvalid`。`Record.body` は frontmatter を除いた本文原文。`LOGS_SUBDIR = "logs"`。`ALLOWED_PATTERNS` は `content/` 内だけを検査する（`content_dir` 外は対象外）
  - log-index: 生成器は `src/wil/<feature>.py`、純粋な描画関数 + `main()` が `wil.generated.run(render_pages)` を呼ぶ。出力は `content/generated/<feature>*.md`（gitignore、`generate.sh` が毎回 `rm -rf`）。`run` はページ名が `.md` 以外・絶対パス・`..` を含むと `ValueError`。登録は `scripts/generate.sh` に 1 行。`.gitignore` と `ALLOWED_PATTERNS` は区域単位で設定済み
  - `run(render_pages)` の `render_pages` は `Sequence[Record]` だけを受け取る。追加の入力（おすすめデータ）は `main()` で読み、クロージャで渡す（log-index 自身も `run(lambda rs: {PAGE_NAME: render(rs)})` の形を使っている）
  - tech-timeline: `build_index(records)` は最初に別名表を検査し、矛盾なら `AliasError`。`Tech.page = f"{PAGE_DIR}/{slug(key)}.md"`（区域相対）。`tech_key(表記)` で任意の表記から技術を引ける。`TechEntry.excerpt` はエスケープ前の原文
  - `.gitignore`（daily-log-page）に `data/` や `*.json` を無視する規則は無い。コミットされたデータが誤って無視されることはない
- **Implications**: 生成器は上流の契約内で書ける。コミットするデータは `content/` の外に置けば `ALLOWED_PATTERNS` の変更は不要

### リンクの相対パス
- **Context**: tech-timeline の下流例は「区域内の別ページ（例 learning-recommendation.md）から `../{tech.page}`」としている
- **Findings**: MkDocs 系のリンクはソースファイル相対。区域直下の `content/generated/learning-recommendation.md` から `../tech-timeline/x.md` は `content/tech-timeline/x.md` を指し、`--strict` で失敗する。`../{tech.page}` が正しいのは区域内で 1 階層下のページ（`learning-recommendation/<name>.md`）からのみ
- **Implications**: 技術別タイムラインへのリンクは技術別おすすめページ（1 階層下）にだけ置き、`../{tech.page}` を使う。一覧ページ（区域直下）は自分の技術別ページへのリンクだけを持つ。tech-timeline 設計の例のコメントの誤りは指摘し、tech-timeline 側で修正済み（解決済み）

### サイトデザインのスタイル契約
- **Context**: 注記・古さの表示に使える Markdown 構造の確認
- **Sources Consulted**: `.kiro/specs/04-site-design/design.md`（スタイル契約、TopPage）
- **Findings**: 見出し・箇条書き（入れ子 3 階層まで）・リンク・強調などの通常の Markdown 構造は使ってよい。クラス・属性・`style`・独自 CSS/JS は禁止。トップページ末尾に learning-recommendation のリンク行 1 行が来る想定
- **Implications**: 注記と古さの表示は強調（`**注意**:`）付きの段落、引用は入れ子の箇条書き（4 空白インデント）で表す。引用ブロック記法や属性は使わない

### 生成の起動方法（Claude Code skill かローカルスクリプトか）
- **Context**: brief が設計判断として求めている
- **Findings**:
  - ローカルスクリプト（Anthropic API を直接呼ぶ）: 手元に API キーが必要（環境変数で渡せばリポジトリには置かないが、鍵の管理と課金が別に発生する）。`anthropic` SDK の依存追加が必要。承認の対話を自前で作る必要がある
  - Claude Code の project skill: オーナーが普段使う Claude Code のセッションで動くため、リポジトリにもスクリプトにも鍵が現れない。依存追加なし。案の提示 → 修正 → 承認の対話がそのまま使える。log-writing-skill（`/wil-log`）と同じ形で、手元専用ツールの置き場所（steering の structure.md）にも合う
  - skill は確率的に動くため、決定的にすべき処理（対象候補の算出、根拠の検査、ページ生成）は Python 側に置く。log-writing-skill の「判断は Claude、規則の判定は Python」と同じ分担
- **Implications**: skill `wil-recommend` を採用。決定的な処理は `wil.learning_recommendation` の `status` サブコマンドと生成器に置く

### log-writing-skill との重なり
- **Findings**: `wil-log` は `content/logs/YYYY-MM-DD.md` の作成・追記と検証を所有する。本機能の skill はログを読むだけで、書き込み先は `data/learning-recommendation/<name>.json` の 1 ファイルに限る。git 操作をしない点は同じ
- **Implications**: skill の説明文と手順で「ログを作成・変更しない、ログを書きたい場合は `/wil-log` を案内する」を明記する。補助 CLI は共有しない（`wil.log_tags` を使わない）

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| A. データを `content/` 外にコミット + ビルド前生成 | `data/learning-recommendation/*.json` を正とし、生成器がデータ + 技術インデックスからページを作る | 上流契約を変えない。根拠リンクと古さ表示を毎ビルド現在のログから計算できる | なし（データ置き場は steering `structure.md` の「コミットする生成元データ: `data/<feature>/`」として定義済み） | 採用 |
| B. 生成済み Markdown を `content/` にコミット | skill が完成ページを書く | 生成器が不要 | `ALLOWED_PATTERNS` 変更が必要（daily-log-page/log-index への変更依頼）。ログが変わってもリンク切れ・古さを検出できない。`content/generated/` には置けない（毎回削除） | 不採用 |
| C. ビルド時に LLM を呼ぶ | CI で生成 | 常に最新 | CI に API キーが必要。roadmap の制約違反 | 不採用 |

## Design Decisions

### Decision: データは技術ごとの JSON ファイルとし `data/learning-recommendation/` に置く
- **Context**: 要件 1.4、1.5、brief の「差分を抑える更新単位」
- **Alternatives Considered**:
  1. 全技術を 1 ファイル — 1 技術の更新でファイル全体の差分・競合が出やすい
  2. YAML — PyYAML は既存依存だが、`yes`/`no` などの型の罠があり、skill が書く値の検査が増える
- **Selected Approach**: 1 技術 = 1 JSON ファイル。ファイル名は慣例として技術別タイムラインページと同じ名前（`Tech.page` のファイル名部分の拡張子違い）。照合はファイル名ではなく、データ内の `tech`（技術名）を `tech_key` で引いて行う
- **Rationale**: 標準ライブラリだけで厳密に検査でき、更新が 1 ファイルに閉じる。`tech_key` で照合するため、別名の追加で技術の識別子が変わっても追従する
- **Trade-offs**: JSON は手で書くとき引用符のエスケープが要る（skill が書くため許容）
- **Follow-up**: 公開リポジトリのため、データも公開される前提で扱う（ページと同じ内容）

### Decision: 起動方法は Claude Code の project skill
- 上記「生成の起動方法」を参照。鍵不要・依存なし・承認の対話を流用できることが決め手

### Decision: 対象技術の選び方
- **Selected Approach**: 起動時に技術名が指定されればそれ。無ければ `status` の一覧（学習回数の多い順）から「未生成」「要更新」の技術を候補として示し、オーナーが選ぶ。1 回の起動で 1 技術
- **Rationale**: 自動で全技術を一括生成すると差分が大きく、承認の負担も大きい。学習回数が多い技術ほど要約の価値が高い

### Decision: 根拠の検査は引用の部分一致で行い、ビルドは寛容にする
- **Context**: 要件 3.1–3.5、4.8、5.4、6.4
- **Selected Approach**:
  - 学習済みの要点ごとに `quote`（ログ本文からの逐語の抜き出し）を必須にし、`status` が「NFKC → casefold → 空白の連続を 1 つの空白に」の正規化後に、根拠日付のいずれかのログ本文に含まれるかを検査する
  - 誤りの分類: データ自身の誤り（形式、同じ技術の重複）はビルドも失敗させる。ログ側の変化で生じる不一致（技術が消えた、根拠日付のログからタグが外れた、新しいログが増えた）はビルドでは失敗させず、ページで「見つからない」「生成後に変化」と表示する。`status` はすべてを問題として示し非ゼロで終わる
- **Rationale**: ログを書く・直すたびにビルドが壊れると「書く手間を増やさない」に反する。一方、データの書き損じは skill の直後に `status` で止まり、万一コミットされてもビルドで止まる
- **Trade-offs**: 引用の存在は「その文がログにある」までしか示さず、要約が正しいことは示さない。要約の妥当性と個人情報の有無はオーナーの承認で確かめる（要件 2.8、7.2 に明記）

### Decision: 生成器と検査 CLI を 1 モジュールにまとめる
- **Selected Approach**: `wil.learning_recommendation` に型・読み取り・検査・描画・CLI を置く。引数なしの `main()` は log-index 契約どおり `run` を呼ぶ（`generate.sh` が使う形）。`status` サブコマンドは skill とオーナー用
- **Alternatives Considered**: 別モジュール（`wil.log_tags` のような補助 CLI）。読み取り・照合・古さの計算を両方が使うため、分けると内部関数を跨いで import することになる
- **Rationale**: tech-timeline も API・描画・CLI を 1 モジュールに置いている。ファイル数を増やさない

### Decision: エスケープは `wil.generated.escape_inline` を使う
- log-index が `escape_inline(text) -> str` を共有ヘルパー `wil.generated` で提供する。本 spec は非公開の複製を置かず、これを import する（変更依頼は解決済み）

## Synthesis
- **Generalization**: 「学習済みの要点」と「未学習の項目」はどちらも「文 + 根拠日付の列」で、リンク描画・見つからない日付の扱い・検査（日付の照合）を共有する。引用は学習済みの要点だけが持つ
- **Build vs Adopt**: 技術の同定・表記ゆれ・学習日は tech-timeline の API を採用（再計算しない）。書き出し・誤り報告は `wil.generated.run`。ログ読み取りは `wil.records`。LLM 呼び出しは Claude Code のセッションを採用（SDK を足さない）。JSON の読み取りは標準ライブラリ。新規の外部依存なし
- **Simplification**: 検査 CLI は `status` 1 つ（一覧と技術指定の詳細を兼ね、問題があれば非ゼロ）。データ形式の版番号、生成時刻（時刻まで）、件数の上限検査、ファイル名と技術名の一致検査は持たない（重複は `tech_key` で検出できる）。pre-commit へのフック追加もしない（daily-log-page 所有。ビルドと `status` で止まる）

## Design Review Gate（inline）
- 判定: PASS（修正 1 回）
- 機械的チェック: 要件 ID 1.1–8.4 の 52 件すべてが追跡表に出現。Boundary の 4 節が具体的。File Structure Plan に具体的なパス。全コンポーネントにファイルがある
- 修正内容: 一覧ページから技術別タイムラインへのリンクを外した（区域直下からの `../{tech.page}` はリンク切れになるため）。別名表の検査を `check_aliases`（下流契約外）ではなく `build_index` の `AliasError` で受ける形に直した

## Risks & Mitigations
- 引用が Markdown 記法を含む行から取られると照合に失敗する — skill の手順で「ログの 1 行から記法を含まない連続した文字列をそのまま写す」と指示し、`status` で検出する
- 技術数が増えると skill 1 回 1 技術では追いつかない — 学習回数の多い順に候補を示す。一括生成は要望が出てから検討
- 生成 AI の提案が誤っている — ページに注記を出し（4.6）、承認で確かめる
- データは公開リポジトリに置かれる — ページと同じ内容しか持たず、gitleaks を含む既存 pre-commit がコミット時に検査する

## References
- `.kiro/specs/01-daily-log-page/design.md` — `wil.records` 契約、`.gitignore`、`ALLOWED_PATTERNS`
- `.kiro/specs/02-log-index/design.md` — ビルド前生成の契約、`wil.generated.escape_inline`
- `.kiro/specs/06-tech-timeline/design.md` — 技術インデックス API と下流の読み方
- `.kiro/specs/03-log-writing-skill/design.md` — skill と補助 CLI の分担の前例
- `.kiro/specs/04-site-design/design.md` — スタイル契約、トップページのリンク行

## Task-Graph Sanity Review（independent）
- 1 回目: NEEDS_FIXES（8 件: 6.1 のタグ除去確認にログ 2 件が必要、6.2 はオーナーの手動受け入れ確認、skill 置き場の書き込み許可、タスク 4 の要件 2.3/2.12 の追加、skill は design の CLI 契約に従う旨と実行確認、3.1/3.2 の引数処理の所有、status の同数時の並び、5.1 での 6.6 の確認）。すべて tasks.md に反映済み
- 2 回目: NEEDS_FIXES（残り 2 件: 6.1 の一時データで外すログの日付を要点の根拠日付に入れること、3.1 の使い方終了の文言）。規則により再レビューはせず、2 件の文言修正のみ tasks.md に反映。承認は false のまま（オーナーの確認後に承認する）
