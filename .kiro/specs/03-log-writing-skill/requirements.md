# Requirements Document

## Project Description (Input)
### Problem
その日に学んだことを、ログ形式（ファイル名、frontmatter、見出しと入れ子の箇条書き）に沿って毎回まとめるのは手間がかかり、続かない。普段 Claude Code と壁打ちしながら学んでいるので、その流れでログまで仕上げたい。

### Current State
daily-log-page によりログ形式と検証（`wil.records` と pre-commit）がある。記録はすべて手書き。

### Desired Outcome
- Claude Code でこの skill を呼ぶと、対話しながらその日の学習内容（学習、気になった技術情報など）を聞き取り・整理し、正しい形式のログファイル `YYYY-MM-DD.md` を作成または追記する
- 生成されたログは daily-log-page の検証を通る
- 既存の tags の表記に揃えるよう提案する（表記ゆれを減らす）
- 公開前提であることを踏まえ、秘密情報や社外秘に見える内容を書く前に注意を促す

### Approach
リポジトリ内に Claude Code の skill（`SKILL.md` + 必要ならテンプレート）を置く。ログ形式の正本は daily-log-page の文書と `wil.records` にあり、skill はそれを参照する（形式を skill 側で二重定義しない）。作成後に検証コマンドを実行して結果を確認する。

### Constraints（brief より）
- 書く手間を減らすことが目的。質問は最小限にし、ユーザーの文章を勝手に膨らませない
- 公開前提: 書き込み前に内容をユーザーに確認する
- commit / push は自動実行しない（ユーザーが確認して行う）
- 過去知見の検索（knowledge-mcp）、おすすめ生成（learning-recommendation）、タグ正規化ルール（tech-timeline）は扱わない

## Introduction
サイトのオーナーが Claude Code との壁打ちの流れのまま、その日の学習内容（学んだこと、気になった技術情報、メモ）を対話で聞き取り・整理してもらい、daily-log-page が定めたログ形式に沿ったログファイルを作成または追記できるようにする。書く手間を減らすことが目的であり、質問は最小限にとどめ、オーナーの書いた内容を勝手に膨らませない。リポジトリとサイトは公開されるため、書き込み前に必ず内容をオーナーに確認し、秘密情報や社外秘に見える内容には書き込み前に注意を促す。作成後は daily-log-page の検証を実行して結果を示す。commit と push はオーナーが自分で行う。

## Boundary Context
- **In scope**:
  - Claude Code から呼び出す記録支援 skill（ログの作成・同じ日のログへの追記）
  - その日の学習内容の聞き取りと、見出し・入れ子の箇条書きへの整理
  - 既存ログに使われている tags の一覧取得と、表記を揃えるための提案
  - 書き込み前の内容確認と、秘密情報・社外秘に見える内容への注意喚起
  - 書き込み後の daily-log-page の検証の実行と結果の提示
- **Out of scope**:
  - ログ形式（置き場所、ファイル名、frontmatter の規則）の定義。daily-log-page が正本であり、この機能は再定義しない
  - commit・push・ステージングの実行
  - 過去知見の検索・提示（knowledge-mcp が所有）
  - 学習のおすすめ生成（learning-recommendation が所有）
  - タグの正規化ルール・別名表の定義（tech-timeline が所有）
  - 公開サイトの見た目・一覧ページ
- **Adjacent expectations**:
  - daily-log-page が、ログ形式・ログの読み取り機能・検証コマンドを提供していること。この機能はそれらを利用し、独自の検証規則を持たない
  - 書き込んだログの最終的な公開可否は、オーナーによる確認と daily-log-page のコミット前検査で決まる

## Requirements

### Requirement 1: 呼び出しと対象日の決定
**Objective:** サイトのオーナーとして、Claude Code での作業中にすぐ記録を始めたい。記録のための準備で手間を増やさないため。

#### Acceptance Criteria
1. When オーナーが Claude Code から記録支援 skill を呼び出す, the 記録支援 skill shall その場で聞き取りを開始する
2. When オーナーが対象日を指定せずに呼び出す, the 記録支援 skill shall 実行環境のローカル日付の当日を対象日とする
3. When オーナーが対象日を指定して呼び出す, the 記録支援 skill shall その日付を対象日とする
4. If 指定された対象日が暦上存在しない日付である, the 記録支援 skill shall 書き込みを行わず、その旨をオーナーに伝えて日付の指定し直しを求める
5. The 記録支援 skill shall 対象日のログファイルの置き場所とファイル名を、daily-log-page が定めた規則に従って決める

### Requirement 2: 学習内容の聞き取りと整理
**Objective:** サイトのオーナーとして、思いつくままに話した内容をログの形に整えてほしい。形式を気にせずに記録を続けられるようにするため。

#### Acceptance Criteria
1. When 聞き取りを開始し、同じ会話の中に学習内容がまだ無い, the 記録支援 skill shall その日に学んだこと・気になった技術情報・メモを 1 回の質問でまとめて尋ねる
2. Where 同じ会話の中でオーナーがすでに学習内容を話している, the 記録支援 skill shall それを記録の候補として示し、同じ内容を改めて尋ねない
3. When オーナーが学習内容を伝える, the 記録支援 skill shall その内容を見出しと入れ子の箇条書きに整理したログ本文の案を作る
4. The 記録支援 skill shall ログ本文の案に、オーナーが伝えていない事実・説明・感想を追加しない
5. The 記録支援 skill shall オーナーが伝えたコード・コマンド・URL を書き換えずにログ本文の案に含める
6. If オーナーの伝えた内容だけでは tags を 1 つも決められない, the 記録支援 skill shall tags に関する質問だけを追加で行う
7. The 記録支援 skill shall 書き込みまでの追加の質問を、tags と対象日の確認など書き込みに不可欠なものに限る

### Requirement 3: tags の表記の提案
**Objective:** サイトのオーナーとして、過去のログと同じ表記で tags を付けたい。表記ゆれでタグ検索や後続機能の集計が分かれないようにするため。

#### Acceptance Criteria
1. When tags の案を作る, the 記録支援 skill shall 既存のログに使われている tags の一覧を、daily-log-page の読み取り機能を通じて取得する
2. When tags の案に、既存の tag と大文字小文字・空白・記号の違いだけで異なるものがある, the 記録支援 skill shall 既存の表記を使うよう提案する
3. The 記録支援 skill shall 既存の表記への置き換えを提案にとどめ、最終的な tags はオーナーの選択に従う
4. If 既存のログを読み取れない（不正なログがあるなど）, the 記録支援 skill shall 表記の提案を行わずに続行し、提案できなかった理由をオーナーに伝える
5. The 記録支援 skill shall tags を、daily-log-page の規則を満たす 1 つ以上の空でない文字列のリストとして案に含める

### Requirement 4: 書き込み前の確認と秘密情報への注意
**Objective:** サイトのオーナーとして、公開される前に内容を自分で確かめたい。秘密情報や社外秘を誤って公開しないため。

#### Acceptance Criteria
1. The 記録支援 skill shall ログファイルへ書き込む前に、書き込むファイルのパスと書き込む内容の全文をオーナーに提示し、承認を求める
2. If 書き込む内容に、秘密情報（API キー、トークン、パスワード、秘密鍵、接続文字列など）に見える文字列が含まれる, the 記録支援 skill shall 承認を求める前に該当箇所を示して公開されることへの注意を促す
3. If 書き込む内容に、社外秘・個人情報・社内の固有名（社内システム名、社内 URL、顧客名など）に見える記述が含まれる, the 記録支援 skill shall 承認を求める前に該当箇所を示して公開されることへの注意を促す
4. When オーナーが修正を求める, the 記録支援 skill shall 修正した内容の全文を再度提示して承認を求める
5. If オーナーが承認しない、または中止を求める, the 記録支援 skill shall ファイルを作成・変更せずに終了する
6. The 記録支援 skill shall オーナーの承認なしにログファイルを作成・変更しない

### Requirement 5: ログファイルの作成と追記
**Objective:** サイトのオーナーとして、同じ日に何度呼び出しても 1 日 1 ファイルのログにまとまってほしい。既に書いた内容を失わないため。

#### Acceptance Criteria
1. When 承認され、対象日のログファイルが存在しない, the 記録支援 skill shall 承認された内容で対象日のログファイルを新規に作成する
2. When 承認され、対象日のログファイルがすでに存在する, the 記録支援 skill shall 既存の本文と、`tags`・`summary` 以外の frontmatter 項目を変更せずに、承認された本文を本文の末尾に追記する
3. When 対象日のログファイルがすでに存在する, the 記録支援 skill shall 既存の tags を残したまま、新しい tags のうち未登録のものだけを加えた tags を書き込み内容の案として提示する
4. When 対象日のログファイルがすでに存在する, the 記録支援 skill shall 既存の `summary` を変更する場合は、変更前と変更後の両方を提示して承認を求める
5. If 対象日のログファイルがすでに存在し、daily-log-page の規則に照らして不正である, the 記録支援 skill shall 追記を行わず、不正の理由をオーナーに伝える
6. The 記録支援 skill shall 対象日のログファイル以外のファイルを作成・変更・削除しない

### Requirement 6: 書き込み後の検証
**Objective:** サイトのオーナーとして、書かれたログが公開前の検査を通るかをその場で知りたい。コミット時やビルド時に失敗して手戻りしないため。

#### Acceptance Criteria
1. When ログファイルを書き込んだ, the 記録支援 skill shall daily-log-page の検証コマンドを書き込んだファイルに対して実行する
2. When 検証が成功する, the 記録支援 skill shall 成功したことと書き込んだファイルのパスをオーナーに伝える
3. If 検証が失敗する, the 記録支援 skill shall 検証が示した理由をそのままオーナーに伝え、修正案を提示して承認を求める
4. If オーナーが修正案を承認しない, the 記録支援 skill shall ファイルが検証を通らない状態で残っていることと、その理由をオーナーに伝える
5. If 検証コマンドを実行できない, the 記録支援 skill shall 検証が行われていないことと実行できなかった理由をオーナーに伝え、検証済みとは伝えない

### Requirement 7: 範囲外の操作をしないこと
**Objective:** サイトのオーナーとして、公開につながる操作は自分で行いたい。意図しない内容が公開されないため。

#### Acceptance Criteria
1. The 記録支援 skill shall git の commit・push・ステージングを実行しない
2. When ログの書き込みと検証が終わる, the 記録支援 skill shall commit と push はオーナーが内容を確認して行うものであることを伝える
3. The 記録支援 skill shall 過去ログの内容の検索・提示、および学習のおすすめの生成を行わない
