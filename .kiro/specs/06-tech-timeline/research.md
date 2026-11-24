# Research & Design Decisions

## Summary
- **Feature**: `tech-timeline`
- **Discovery Scope**: Extension（daily-log-page の `wil.records` と log-index のビルド前生成方式の上に乗る拡張。いずれも未実装の設計契約であり、上流 design.md を既存システムとして扱う軽量調査）
- **Key Findings**:
  - Zensical の組み込み tags はタグ一覧（`<!-- material/tags -->` による listings）まで対応するが、書かれたとおりのタグをページ名で並べるだけで、表記ゆれの吸収・日付・初回/最終/回数は扱えない。組み込み検索は公式に英語のみ
  - log-index の `wil.generated.run` は `.md` 以外のページ名を拒否し、`content/generated/` の中身はすべて公開される。技術インデックスを JSON 等のデータファイルとして出す余地は契約上ない → Python API として提供する
  - log-writing-skill は提案用の比較キー `variant_key`（NFKC → casefold → 空白と `- _ . ・` を除去）を持ち、「tech-timeline が正規化規則を公開したら見直す」を再確認条件にしている。同じ規則を採用すれば置き換え可能になる

## Research Log

### 上流契約（daily-log-page / log-index）
- **Context**: 再実装を避け、上流の契約に厳密に従うため
- **Sources Consulted**: `.kiro/specs/01-daily-log-page/design.md`、`.kiro/specs/02-log-index/design.md`
- **Findings**:
  - `Record(date, path, url_path, tags, summary, body, sections)`。`tags` は書かれたとおり・書かれた順で、正規化は tech-timeline の責務と明記。`Section(level, title, body)`、フェンス内の `#` は見出しにならない。`load_records()` は日付昇順、不正時 `RecordsInvalid`
  - 生成器は `src/wil/<feature>.py`、純粋な描画関数 + `main()` が `wil.generated.run(render_pages)` を呼ぶ。`render_pages: Sequence[Record] -> Mapping[str, str]`（区域相対パス → Markdown）。パスは機能名で始める（例に `"tech-timeline/aws.md"`）
  - 登録は `scripts/generate.sh` に 1 行。`.gitignore` と `ALLOWED_PATTERNS`（`generated/.+\.md`）は区域単位で設定済み。ナビはフォルダ構造の既定ナビ、`zensical.toml` は変更しない
  - 生成器は `wil.records` と `wil.generated` のみを import し、他の生成器を import しない
  - `use_directory_urls` は既定 true（`x.md` → `x/`、`dir/index.md` → `dir/`）
- **Implications**: 技術インデックス API と生成器を 1 モジュール `wil.tech_timeline` に置けば、生成器の import 規則を満たしたまま下流に提供できる。log-index の `fiscal_year`・`escape_inline` は生成器内にあり import できない

### Zensical 組み込み tags
- **Context**: brief「組み込み検索・タグ機能でどこまで足りるかを確認し、足りない分だけを補う」
- **Sources Consulted**: https://zensical.org/docs/setup/tags/ 、https://zensical.org/compatibility/plugins/
- **Findings**:
  - tags は 0.0.58 以降ネイティブ実装。`listings`（`<!-- material/tags -->` を置いたページにタグ一覧を生成）、`tags_allowed`、`tags_hierarchy`、`tags_sort_by` / `listings_sort_by` に対応。`tags_file` は無視、独自 Python callable は不可
  - `[project.extra.tags]` はタグ → 識別子（アイコン用）の対応で、別名の統合機能ではない
  - タグは各ページ下部に表示され、検索での絞り込みに使える
- **Implications**: listings は「書かれたタグ → ページ」の対応しか出せず、表記ゆれの吸収、日付順、初回/最終/回数、抜粋を満たせない。有効化には daily-log-page 所有の `zensical.toml` の変更も要る。組み込み tags は各ログページのタグ表示（既存）として残し、技術一覧・タイムラインは生成で補う

### Zensical 組み込み検索
- **Sources Consulted**: https://zensical.org/docs/setup/search/ 、https://zensical.org/compatibility/plugins/
- **Findings**: 既定で有効。設定は `enabled` と `separator` のみ。「Search is currently only available in English」。日本語・CJK への言及なし。front matter による重み付けは無く、`search.exclude` のみ
- **Implications**: 技術別ページの H1 を表示名にし、別表記を本文に載せることで、英数字の技術名・別表記で技術別ページが検索に掛かるようにする（追加実装なし）。日本語検索の品質は保証せず、技術一覧ページを主な入口とする（6.5）

### 下流（learning-recommendation）と隣接 spec
- **Sources Consulted**: `.kiro/specs/07-learning-recommendation/brief.md`、`.kiro/specs/03-log-writing-skill/design.md`、`.kiro/specs/05-knowledge-mcp/design.md`、`.kiro/steering/structure.md`
- **Findings**:
  - learning-recommendation は「技術インデックス（技術 → 学習日・ログ・抜粋、表記ゆれ吸収済み）」を読み、ページ化は log-index 方式に従う。技術別ページへのリンクを出す可能性が高い
  - structure.md「機能同士は直接依存しない（例外: 07 は 06 の技術インデックスを読む）」
  - log-writing-skill `variant_key`: 「NFKC 正規化 → casefold → 空白と - _ . ・ を除去した比較キー」
  - knowledge-mcp は tags 比較で `casefold()` のみを使い、正規化を採用する場合は自 spec の再確認とする
- **Implications**: 公開 API は frozen dataclass + 純関数 `build_index(records)` + 識別子関数 `tech_key(tag)`。各技術にページの場所を含める。正規化規則は `variant_key` と同一にする。knowledge-mcp は本 spec の影響を受けない（自ら採用するまで）

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 1 モジュール `wil.tech_timeline`（インデックス API + 描画 + main） | 生成器モジュールに公開 API を同居 | 生成器の import 規則（records と generated のみ）をそのまま満たす。ファイル最小 | 下流が生成器モジュールを import する（steering が認める例外） | 採用 |
| 2 モジュール（`wil.tech_index` + `wil.tech_timeline`） | API と生成器を分離 | 責務が明確 | 生成器が records/generated 以外を import し、log-index の規則に反する | 不採用 |
| データファイル（JSON）出力 | 生成区域にインデックスを書き出す | 言語非依存 | `run` が `.md` 以外を拒否、区域は全公開、ビルド時のみ存在 | 不採用 |
| Zensical tags listings | 組み込みタグ一覧 | 実装不要 | 表記ゆれ・日付・集計なし、`zensical.toml` 変更が必要 | 不採用（既存のタグ表示は維持） |

## Design Decisions

### Decision: 技術インデックスは Python API として提供する
- **Context**: 8.1–8.4、brief「下流が読める形」、log-index 契約
- **Alternatives Considered**:
  1. JSON を `content/generated/` に出力 — `run` の名前検査で不可、全公開、コミットされない
  2. JSON をリポジトリにコミット — 生成物のコミットとなり差分管理が必要、二重の真実
  3. Python API — `load_records()` の結果から毎回計算
- **Selected Approach**: 3。`build_index(records) -> tuple[Tech, ...]` と `tech_key(tag) -> str`、型 `Tech` / `TechEntry`
- **Rationale**: 同じパッケージ内の Python 利用者のみが下流。ログ数は小さく再計算のコストは無視できる
- **Trade-offs**: Python 以外からは読めない（現時点で利用者なし）
- **Follow-up**: 型のフィールドを Revalidation Triggers に列挙

### Decision: 正規化規則は log-writing-skill の `variant_key` と同一にする
- **Context**: 1.1、1.3、1.8、隣接 spec との一貫性
- **Selected Approach**: `tag_key(tag) = NFKC → casefold → 空白と - _ . ・ を除去`。結果が空なら `tag.strip()`
- **Rationale**: 既存の提案規則と一致させ、log-writing-skill が後で `tech_key` に置き換えても提案結果が変わらない
- **Trade-offs**: `C` と `C++` は区別される（`+` は除去しない）一方、`.NET` と `NET` は同一になる。誤統合は別名表では解けない（別名表は統合のみ）。実害が出たら規則を見直す（Revalidation Trigger）

### Decision: 別名の対応表はモジュール内の (表記, 表示名) の組の列とする
- **Context**: 1.2、1.6、1.7、brief「正規化ルールの置き場所」
- **Alternatives Considered**:
  1. `dict` リテラル — 同じキーの重複が実行時に黙って上書きされる
  2. TOML/YAML ファイル — 読み込み処理と置き場所の規則が増える
  3. `tuple[tuple[str, str], ...]` 定数 `ALIASES`
- **Selected Approach**: 3。`src/wil/tech_timeline.py` 内（`content/` 外なので公開されない）。照合キーで重複・矛盾・連鎖を検査し `AliasError`
- **Rationale**: 最小の仕組みで、重複も実行時に検出できる。オーナーは 1 行追記するだけ
- **Trade-offs**: 表の変更が Python ファイルの変更になる（個人サイトで書き手はオーナーのみのため許容）

### Decision: ページの配置と場所の決め方
- **Context**: 4.3、5.1、5.5、5.6、5.8、log-index の例 `"tech-timeline/aws.md"`
- **Selected Approach**: 一覧 `tech-timeline.md`（URL `generated/tech-timeline/`）、技術別 `tech-timeline/<slug>.md`（URL `generated/tech-timeline/<slug>/`）。`slug` は技術の識別子から作り、`[a-z0-9]` はそのまま、それ以外の文字は `-<16進コードポイント>-` に置き換える。識別子には `-` が残らないため単射。`slug == "index"` は `tech-timeline/index.md` が一覧と同じ URL になるため `index-` に置き換える
- **Rationale**: 識別子が同じ限り場所が変わらず（表示名の大文字小文字の変更では動かない）、異なる技術が重ならない
- **Trade-offs**: 日本語や記号を含む技術名の URL が読みにくい（例 `-578b--30d2-...`）。見た目の改善は site-design または将来の別名表の拡張で扱う

### Decision: 抜粋の選び方
- **Context**: 3.1–3.5、「該当抜粋」
- **Selected Approach**: 表示名と全表記を NFKC + casefold して、区間の見出し + 本文に部分一致する最初の区間 → その本文のフェンス外の最初の空でない行（無ければ見出し）→ 無ければ summary → 無ければ本文のフェンス外・見出し以外の最初の空でない行 → 無ければ空。120 文字超は先頭 120 文字 + 「…」
- **Rationale**: 本文の構造（`Section`）を上流が提供済みで、追加の解析が要らない。決定的で単体テストできる
- **Trade-offs**: 短い技術名（例 `go`）は無関係な語（`google`）にも一致しうる。抜粋の質の問題に留まり、学習日の判定（tags のみ）には影響しない

### Decision: `escape_inline` と `fiscal_year` の扱い
- **Context**: 生成器は他の生成器を import できない。log-index の `escape_inline` は `wil.log_index` にある
- **Selected Approach**: `fiscal_year` は使わない（タイムラインは日付の時系列で、年度グルーピングを要件に含めない）。`escape_inline` は **未解決事項**: log-index 所有の `wil.generated` へ移すのが本来の形。暫定の既定として、`wil.tech_timeline` に log-index と同一規則の非公開関数 `_escape` を置き、テストで log-index と同じ入出力例を確認する。移設されたら `_escape` を削除して `wil.generated` のものを使う
- **Rationale**: 上流所有ファイルを本 spec で変えない。重複は 1 関数に限定し、置き換え条件を明記する
- **Follow-up**: log-index へ移設を依頼（Revalidation Trigger に記載）

### Decision: 一覧はリスト形式（表にしない）
- **Context**: 4.2、4.6
- **Selected Approach**: 1 技術 1 行のリスト項目。表（`|` 区切り）は `escape_inline` の規則が `|` を扱わないため避ける
- **Trade-offs**: 列の揃いは無い。見た目は site-design

## Synthesis
- **Generalization**: 「表記 → 技術の識別子」を `tech_key` 1 関数に集約し、インデックス作成・別名表検査・下流の照合・ページの場所のすべてがこれを使う
- **Build vs. Adopt**: 組み込み tags listings と検索を確認し、ログページのタグ表示と英数字の検索は既存機能をそのまま使う。集計・正規化・タイムラインのみを生成で補う。新規依存なし（標準ライブラリ `unicodedata`、`re`、`dataclasses`）
- **Simplification**: モジュールは 1 つ。データファイル出力・設定ファイル化・本文からの技術抽出・年度グルーピングは作らない

## Risks & Mitigations
- 技術数に比例して既定ナビに技術別ページが並ぶ — 構造のみ本 spec、ナビの整理は site-design（`zensical.toml` は変更しない）
- 組み込み検索が英数字の技術名でも技術別ページを返さない — ビルド後の E2E 確認で検出し、返さなければ設計に戻る。一覧ページが主な入口
- gitignore された生成ページがビルド対象外になる — log-index と同じ前提。log-index の E2E 確認に依存
- 正規化規則による誤統合（`.NET` と `NET` など）— 規則変更は Revalidation Trigger。実例が出るまで規則を増やさない
- `escape_inline` の重複 — 未解決事項として記録し、移設時に削除

## References
- [Zensical Tags](https://zensical.org/docs/setup/tags/) — tags の設定と表示
- [Zensical Compatibility: Plugins](https://zensical.org/compatibility/plugins/) — tags listings の対応状況、search の設定項目
- [Zensical Search](https://zensical.org/docs/setup/search/) — 英語のみの記載
- `.kiro/specs/01-daily-log-page/design.md`、`.kiro/specs/02-log-index/design.md` — 上流契約
- `.kiro/specs/03-log-writing-skill/design.md` — `variant_key` の定義
