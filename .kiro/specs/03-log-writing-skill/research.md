# Research & Design Decisions

## Summary
- **Feature**: `log-writing-skill`
- **Discovery Scope**: Extension（daily-log-page が定める形式・`wil.records`・検証 CLI の上に載る。新規の外部依存なし。ライト調査）
- **Key Findings**:
  - 上流 daily-log-page は設計段階（`spec.json` の design 未承認）で、`content/`・`src/wil/` はまだ存在しない。本機能の実装は daily-log-page の実装完了が前提
  - `wil.records` には既存 tags を一覧する関数・CLI が無い。`load_records()` が `Record.tags` を返し、不正ログが 1 件でもあると `RecordsInvalid` を送出する。tags 一覧には薄い補助モジュールが要る
  - `wil.records` の CLI と `CONTENT_DIR` はカレントディレクトリ（リポジトリルート）基準の相対パス。skill からのコマンドはリポジトリルートで実行する必要がある

## Research Log

### 上流契約（daily-log-page design.md）
- **Context**: 形式を二重定義せず再利用するため、利用できる契約を確認
- **Sources Consulted**: `.kiro/specs/01-daily-log-page/design.md`、`requirements.md`、`spec.json`
- **Findings**:
  - 置き場所 `content/logs/YYYY-MM-DD.md`、frontmatter は `tags`（必須、空でない文字列のリスト）と `summary`（任意、1 行）、他キーは無視
  - 公開関数 `load_records(content_dir=CONTENT_DIR) -> list[Record]`。`Record.tags: tuple[str, ...]` は書かれたまま（正規化なし）
  - CLI `uv run python -m wil.records [PATH ...]`: 誤りごとに `path: reason` を標準エラーへ、誤り 0 件で終了コード 0、1 件以上で 1
  - 書き方の正本: `README.md`（Guide）とサンプルログ `content/logs/2026-11-23.md`
- **Implications**: skill は形式規則を本文に書き写さず、実行時に README とサンプルログを読んで従う。検証は CLI をそのまま呼ぶ。tags 一覧は `load_records` 経由で取る

### Claude Code skill の仕組み
- **Context**: skill の置き場所、呼び出し方、権限の扱い
- **Sources Consulted**: Claude Code の skill 仕様（既存の `.claude/skills/kiro-*/SKILL.md` の frontmatter 形式を参照）
- **Findings**:
  - プロジェクト skill は `.claude/skills/<name>/SKILL.md`。frontmatter に `name`・`description`・任意で `argument-hint`・`allowed-tools`。`/<name> 引数` で呼び出し、引数は `$ARGUMENTS`
  - `allowed-tools` は列挙したツールを確認なしで使えるようにする「事前許可」であり、列挙外のツールを禁止する仕組みではない
- **Implications**: 「git を実行しない」「対象日のログ以外を書かない」は skill の指示で守る。`allowed-tools` は読み取り専用の固定コマンドだけに絞り、Write/Edit や git を事前許可しない（書き込み時は Claude Code 標準の許可確認も残る）。`allowed-tools` の厳密な記法は実装時に公式ドキュメントで確認する

### 実行環境
- **Findings**:
  - `uv run` は既定でロックファイルを更新しうる。`--frozen` を付ければ `uv.lock` を書き換えない
  - `CONTENT_DIR` は相対パスのため、コマンドはリポジトリルートで実行する。ルートは `git rev-parse --show-toplevel`（読み取り専用）で得られる
- **Implications**: skill のコマンドはすべて `cd "$(git rev-parse --show-toplevel)" && uv run --frozen ...` の形にし、対象日のログ以外のファイル（`uv.lock` 含む）を変えない（5.6）

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| A. SKILL.md のみ（`python -c` のワンライナーで tags 取得） | 補助コードなし | ファイル最少 | `RecordsInvalid` の扱いと表記ゆれ判定がプロンプト頼みで再現性が無く、テストできない | 不採用 |
| B. SKILL.md + 小さな補助 CLI `wil.log_tags` | tags 一覧と表記ゆれ候補だけを決定的に出す | 判定が単体テスト可能。`wil.records` 経由で読む | ファイルが 2 つ増える | **採用** |
| C. 書き込み・追記も Python で実装 | frontmatter マージと追記をコード化 | 追記の機械的な正しさ | 対話で確定した全文をそのまま書く流れと二重になる。YAML 再出力で既存の書き方が崩れる | 不採用。書き込み後の検証で形式誤りは検出できる |

## Design Decisions

### Decision: tags の表記ゆれ判定を補助 CLI に置く
- **Context**: 3.1・3.2・3.4。既存 tags の取得と「大文字小文字・空白・記号だけが違う」判定
- **Alternatives Considered**:
  1. Claude が一覧を見て判断する
  2. 比較キーで機械的に候補を出す
- **Selected Approach**: `variant_key(tag)` = NFKC 正規化 → casefold → 空白と `-` `_` `.` `・` を除去。キーが一致し文字列が異なる既存 tag を候補として出す
- **Rationale**: 判定が決定的でテストでき、記号の範囲を絞ることで `C++` と `C` のような誤候補を出さない
- **Trade-offs**: 「k8s」と「Kubernetes」のような別名は検出しない（別名表は tech-timeline の責務）
- **Follow-up**: 比較キーは提案専用で保存しない。tech-timeline が正規化規則を公開したら、それを使うよう見直す

### Decision: 書き込みは Claude の Read/Write/Edit で行う
- **Context**: 5.1–5.3。承認された全文をそのまま書く
- **Selected Approach**: 新規は承認全文を Write、追記は既存ファイルを読み、frontmatter の `tags`（と承認時のみ `summary`）を更新し、本文末尾に承認された本文を加えた全文を書く
- **Rationale**: 承認された内容と書かれる内容を一致させる。形式誤りは直後の検証で必ず検出される

### Synthesis
- **Generalization**: 「新規作成」と「追記」はどちらも「対象パスに承認済み全文を書く」に一般化できる。追記は承認前の全文組み立てでのみ分岐する
- **Build vs Adopt**: 検証・読み取りは `wil.records` を採用（再実装しない）。秘密情報の機械検出は daily-log-page の pre-commit（gitleaks）が最終防衛線として既にあるため、skill 側は検出ツールを新設せず、書き込み前の目視確認の注意喚起に徹する
- **Simplification**: テンプレートファイルは置かない（形式の正本は README とサンプルログ）。追記用の Python 実装、設定ファイル、独自の秘密情報スキャナは作らない

## Consulted Skills
- `kiro-spec-design`（design-principles、design-discovery-light、design-synthesis、design-review-gate）

## Risks & Mitigations
- 上流 daily-log-page が未実装・未承認 — 実装タスクの最初に前提確認を置く。上流の契約変更は Revalidation Trigger とする
- 秘密情報・社外秘の見落とし（Claude の判断に依存）— 書き込み前に全文を提示して承認を必須にし、pre-commit の gitleaks が二重に止める
- 追記時に Claude が既存本文を変えてしまう — 書き込み前の全文提示で差分が見え、手順で「既存部分はそのまま」を明示する。検証シナリオで確認する
- `uv run` によるロックファイル変更 — `--frozen` を必須にする

## References
- `.kiro/specs/01-daily-log-page/design.md` — ログ形式、`wil.records` の契約、CLI
- `.kiro/steering/structure.md` — ローカル専用ツールの置き場所、`wil.records` 以外でパースしない原則
