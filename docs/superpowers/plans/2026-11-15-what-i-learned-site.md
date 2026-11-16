# 学んだことの記録サイト（日報/週報版） Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 非公開扱いの日報（`daily/`）から `/weekly` スキルで週報（`weekly/`）を作り、週報だけを年度別一覧・詳細・タグ・全文検索・直近4週ページを持つ静的サイトとして GitHub Pages に公開する。週報は手元の Claude Code でも、Actions の手動実行（結果は PR）でも作れる。

**Architecture:** Astro の Content Collection（glob loader）で `weekly/` だけを読み、Zod スキーマとファイル名チェックで書式を厳しく検証する。週・年度・タグ・4週集計の計算は `src/lib/week-logic.ts` の純粋関数に集め、Node 標準のテストで検証する。対象週の計算は `scripts/week.ts` として CLI 化し、スキルと Actions の両方から使う。ビルド後に Pagefind で索引を作り、`deploy.yml` で公開する。`weekly.yml` は `anthropics/claude-code-action` で `/weekly` を実行し、`gh pr create` で PR にする。

**Tech Stack:** Astro（インストール時点の最新安定版）、Pagefind、Node 24（`node --test` と型ストリップで TS を直接実行）、GitHub Actions（`withastro/action`、`actions/deploy-pages`、`anthropics/claude-code-action`、`gh` CLI）

**Spec:** `docs/superpowers/specs/2026-11-15-what-i-learned-site-design.md`

## Global Constraints

- 公開 URL: `https://kjman678.github.io/what_i_learned/`。`astro.config.mjs` は `site: 'https://kjman678.github.io'`、`base: '/what_i_learned'`。
- サイトの対象は `weekly/` だけ。`daily/` は Astro から一切読まない。
- 週報: `weekly/YYYY-MM-DD.md`、ファイル名はその週の月曜の日付。frontmatter は `tags`（文字列配列、1個以上必須）と `summary`（文字列、任意）。
- 書式違反（`tags` なし/空、ファイル名が `YYYY-MM-DD` でない、実在しない日付、月曜でない、YAML 破損）はビルドを失敗させる。
- 週は月曜〜日曜、タイムゾーン Asia/Tokyo。年度は4月始まりで、週の月曜の日付で決める。
- 「この1ヶ月」= 今週を含む直近4週（今週の月曜〜その3週前の月曜）。ブラウザ側で集計する。
- UI フレームワーク・CSS ライブラリは入れない。素の CSS、ライト/ダーク両対応、`<html lang="ja">`。
- npm 依存の追加は `astro` と `pagefind` のみ。テストは `node --test`。
- サイト内リンクはすべて `base` 付き（`/what_i_learned/...`）。
- Actions の週報は必ず PR にする。`main` に直接コミットしない。認証 Secret 名は `CLAUDE_CODE_OAUTH_TOKEN`。

## Review Focus

1. **日報の漏れ** — `daily/` の文章が `dist/` に1文字も出ない。→ Task 3 の確認。
2. **年度・週の境界** — 月曜 2026-03-30 の週は 2025年度。日曜 2026-11-15 の月曜は 2026-11-09。→ Task 1 のテスト。
3. **対象週の既定値** — 引数なしで実行したとき、今日が月曜でも日曜でも「直前に終わった週」になる（2026-11-16(月) → 11/09〜11/15、2026-11-15(日) → 11/02〜11/08）。→ Task 1 のテスト。
4. **記号・日本語・大小違いのタグ** — `C#` / `C++` / `C` / `CI/CD` / `猫見守り` が衝突しない URL になり、`AWS` と `aws` が同じタグページにまとまる。→ Task 1 のテスト。
5. **日報がない週・週報が既にある週** — `/weekly` も Actions も週報を作らず、理由を出して止まる（Actions は失敗扱いで PR を作らない）。→ Task 6 と Task 7 の確認。

---

### Task 1: プロジェクト骨組みと週ロジック

**Files:**
- Create: `package.json`, `astro.config.mjs`, `tsconfig.json`, `.gitignore`
- Create: `src/lib/week-logic.ts`
- Create: `scripts/week.ts`
- Test: `src/lib/week-logic.test.ts`

**Interfaces:**
- Produces（すべて `src/lib/week-logic.ts` から export。日付はすべて `YYYY-MM-DD` 文字列）:
  - `isValidDate(s: string): boolean` — 形式と実在
  - `isValidWeekId(id: string): boolean` — `isValidDate` かつ月曜
  - `addDays(date: string, n: number): string`
  - `weekMonday(date: string): string`
  - `weekSunday(monday: string): string`
  - `targetWeek(arg: string | undefined, today: string): { monday: string; sunday: string }` — `arg` があればその日を含む週、なければ直前に終わった週。`arg` が不正な日付なら `Error('Invalid date: <arg>')`
  - `fiscalYear(monday: string): number`
  - `groupByFiscalYear<T extends { id: string }>(items: T[]): [number, T[]][]` — 年度降順、各年度内は `id` 降順
  - `tagSlug(tag: string): string`
  - `countRecent(weeks: { id: string; tags: string[] }[], today: string, n?: number): { writtenWeeks: number; tags: [string, number][] }` — `n` 既定 4。`tags` は回数降順、同数は表記昇順。表示名は最初に見つかった表記
  - `todayInTokyo(now?: Date): string`
- `scripts/week.ts`: `node scripts/week.ts [date]` → 標準出力に `<monday> <sunday>` を1行。不正な日付なら stderr にメッセージ、終了コード 1
- npm scripts: `"dev": "astro dev"`, `"build": "astro build && pagefind --site dist"`, `"preview": "astro preview"`, `"test": "node --test src/lib/*.test.ts"`, `"check": "npm test && npm run build"`

- [ ] **Step 1: 骨組みを作る**

`package.json`（`"type": "module"`、上の scripts）。`npm install astro`、`npm install -D pagefind`。`tsconfig.json` は `{"extends": "astro/tsconfigs/strict"}`。`astro.config.mjs` に `site` と `base`。`.gitignore` は `node_modules/`, `dist/`, `.astro/`。

- [ ] **Step 2: 失敗するテストを書く**

```ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isValidDate, isValidWeekId, weekMonday, weekSunday, targetWeek, fiscalYear,
  groupByFiscalYear, tagSlug, countRecent, todayInTokyo } from './week-logic.ts';

test('isValidDate / isValidWeekId', () => {
  assert.equal(isValidDate('2024-02-29'), true);
  assert.equal(isValidDate('2026-02-30'), false);
  assert.equal(isValidDate('2026-11-5'), false);
  assert.equal(isValidWeekId('2026-11-09'), true);   // 月曜
  assert.equal(isValidWeekId('2026-11-15'), false);  // 日曜
  assert.equal(isValidWeekId('memo'), false);
});

test('weekMonday / weekSunday', () => {
  assert.equal(weekMonday('2026-11-15'), '2026-11-09');  // 日曜
  assert.equal(weekMonday('2026-11-16'), '2026-11-16');  // 月曜
  assert.equal(weekMonday('2027-01-01'), '2026-12-28');  // 年またぎ
  assert.equal(weekSunday('2026-11-09'), '2026-11-15');
});

test('targetWeek: 既定は直前に終わった週', () => {
  assert.deepEqual(targetWeek(undefined, '2026-11-16'), { monday: '2026-11-09', sunday: '2026-11-15' });
  assert.deepEqual(targetWeek(undefined, '2026-11-15'), { monday: '2026-11-02', sunday: '2026-11-08' });
  assert.deepEqual(targetWeek('2026-11-12', '2026-11-16'), { monday: '2026-11-09', sunday: '2026-11-15' });
  assert.throws(() => targetWeek('2026-02-30', '2026-11-16'), /Invalid date/);
});

test('fiscalYear: 4月始まり・月曜で判定', () => {
  assert.equal(fiscalYear('2026-03-30'), 2025);
  assert.equal(fiscalYear('2026-04-06'), 2026);
});

test('groupByFiscalYear', () => {
  assert.deepEqual(groupByFiscalYear([{ id: '2026-03-30' }, { id: '2026-11-09' }, { id: '2026-04-06' }]), [
    [2026, [{ id: '2026-11-09' }, { id: '2026-04-06' }]],
    [2025, [{ id: '2026-03-30' }]],
  ]);
});

test('tagSlug', () => {
  assert.equal(new Set(['C#', 'C++', 'C', 'CI/CD'].map(tagSlug)).size, 4);
  assert.equal(tagSlug('AWS'), tagSlug('aws'));
  assert.equal(tagSlug('猫見守り'), '猫見守り');
  assert.doesNotMatch(tagSlug('CI/CD'), /\//);
});

test('countRecent: 今週含む4週', () => {
  const r = countRecent([
    { id: '2026-11-16', tags: ['AWS', 'MCP'] },  // 今週
    { id: '2026-10-26', tags: ['aws'] },         // 3週前
    { id: '2026-10-19', tags: ['FBC'] },         // 4週前（対象外）
    { id: '2026-11-23', tags: ['FBC'] },         // 未来（対象外）
  ], '2026-11-18');
  assert.equal(r.writtenWeeks, 2);
  assert.deepEqual(r.tags, [['AWS', 2], ['MCP', 1]]);
});

test('todayInTokyo: UTC 15:00 は JST の翌日', () => {
  assert.equal(todayInTokyo(new Date('2026-11-15T15:00:00Z')), '2026-11-16');
});
```

- [ ] **Step 3: 失敗を確認**

Run: `npm test` / Expected: FAIL（`week-logic.ts` が無い）

- [ ] **Step 4: `src/lib/week-logic.ts` と `scripts/week.ts` を実装**

日付計算はすべて UTC の `Date`（`Date.UTC`）で行い、ローカル時刻に依存させない。`isValidDate` は正規表現 `^\d{4}-\d{2}-\d{2}$` と、作り直した `Date` の年月日一致で判定。`tagSlug` は小文字化 → `#`→`sharp`、`+`→`plus` → `\p{L}\p{N}` 以外の連続を `-` → 前後の `-` を除去。`countRecent` の集計キーは `tagSlug`。`todayInTokyo` は `toLocaleDateString('sv-SE', { timeZone: 'Asia/Tokyo' })`。`scripts/week.ts` は `targetWeek(process.argv[2], todayInTokyo())`。

- [ ] **Step 5: 通過を確認**

Run: `npm test` / Expected: 8 tests PASS
Run: `node scripts/week.ts 2026-11-12` / Expected: `2026-11-09 2026-11-15`
Run: `node scripts/week.ts 2026-02-30; echo $?` / Expected: エラーメッセージと `1`

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json astro.config.mjs tsconfig.json .gitignore src/lib scripts docs/superpowers
git commit -m "feat: プロジェクト骨組みと週ロジック"
```

---

### Task 2: 週報コレクション・書式チェック・初期データ

**Files:**
- Create: `src/content.config.ts`, `src/lib/weekly.ts`
- Create: `daily/2026-11-15.md`, `weekly/2026-11-09.md`, `CLAUDE.md`
- Create（仮）: `src/pages/index.astro`

**Interfaces:**
- Consumes: `isValidWeekId`（Task 1）
- Produces: `getWeeklies(): Promise<CollectionEntry<'weekly'>[]>`（`src/lib/weekly.ts`）— `id` 降順。`isValidWeekId` を満たさない `id` があれば `Error('Invalid weekly filename: weekly/<id>.md (expected Monday date YYYY-MM-DD.md)')`

- [ ] **Step 1: コレクションと `getWeeklies` を作る**

`src/content.config.ts` に `weekly` コレクション。`glob({ pattern: '*.md', base: './weekly' })`、スキーマ `z.object({ tags: z.array(z.string().min(1)).min(1), summary: z.string().optional() })`。

- [ ] **Step 2: 初期データを置く**

- `daily/2026-11-15.md`: ユーザーの例そのまま（frontmatter なし、「学習」「気になった技術情報」の入れ子箇条書き、「〜〜」も残す）。
- `weekly/2026-11-09.md`: 設計書のひな形（`## 今週学んだこと` / `## 気になった技術情報` / `## 来週やりたいこと`）を、上の日報の内容だけで埋めたサンプル。`tags: [MCP, Docker, AWS, FBC]`。
- `CLAUDE.md`（20〜30行）: `daily/` は自由書式・非公開、`weekly/` の置き場所と frontmatter とひな形、週報は `/weekly [日付]` で作る、作り直しは既存ファイルを消してから、push 前に `npm run check`。

- [ ] **Step 3: 書式チェックが効くことを確認**

仮の `src/pages/index.astro` で `getWeeklies()` の件数を表示（Task 3 で置き換え）。以下を1つずつ置いて `npm run build`、確認後に削除。

| 置くファイル | Expected |
|---|---|
| なし | 成功 |
| `weekly/2026-11-02.md`（`tags: []`） | 失敗、`tags` のエラー |
| `weekly/2026-10-26.md`（frontmatter なし） | 失敗、`tags` のエラー |
| `weekly/2026-10-19.md`（`tags: [a` で YAML 破損） | 失敗 |
| `weekly/2026-11-15.md`（日曜、正しい frontmatter） | 失敗、`Invalid weekly filename` |
| `weekly/memo.md`（正しい frontmatter） | 失敗、`Invalid weekly filename` |
| `daily/memo.md`（中身は何でも） | 成功（日報はチェックしない） |

- [ ] **Step 4: Commit**

```bash
git add src daily weekly CLAUDE.md
git commit -m "feat: 週報コレクションと書式チェック"
```

---

### Task 3: レイアウト・一覧・詳細・タグページ

**Files:**
- Create: `src/layouts/Base.astro`, `src/lib/url.ts`, `src/components/WeeklyList.astro`
- Modify: `src/pages/index.astro`（仮ページを置き換え）
- Create: `src/pages/weekly/[id].astro`, `src/pages/tags/[tag].astro`

**Interfaces:**
- Consumes: `getWeeklies`（Task 2）、`groupByFiscalYear`, `tagSlug`, `weekSunday`（Task 1）
- Produces:
  - `url(path: string): string`（`src/lib/url.ts`）— `import.meta.env.BASE_URL` を前置。`url('weekly/2026-11-09/')` → `/what_i_learned/weekly/2026-11-09/`
  - `Base.astro` props `{ title: string }`。`<html lang="ja">`、ヘッダーに「一覧」（`url('')`）と「この1ヶ月」（`url('recent/')`）、`<slot />` と `<slot name="head" />`。CSS 変数の配色を `prefers-color-scheme: dark` で切替
  - `WeeklyList.astro` props `{ weeklies: CollectionEntry<'weekly'>[] }` — 「YYYY年度」見出し + 各行「MM/DD〜MM/DD・summary（あれば）・タグ（リンク）」。行は詳細ページへのリンク

- [ ] **Step 1: `url.ts` と `Base.astro`**
- [ ] **Step 2: `index.astro`** — `Base` + 全タグ一覧（`tagSlug` で重複除去、リンク）+ `<div id="search"></div>` + `WeeklyList`
- [ ] **Step 3: `weekly/[id].astro`** — `getStaticPaths` は `getWeeklies()` から。見出し「YYYY/MM/DD〜YYYY/MM/DD の週」、タグ（リンク）、`render(entry)` の本文。本文を囲む要素に `data-pagefind-body`
- [ ] **Step 4: `tags/[tag].astro`** — `tagSlug` ごとに1ページ。見出し `#表示名` + `WeeklyList`

- [ ] **Step 5: ビルド出力を確認**

Run: `npm run build && ls dist/weekly/2026-11-09 dist/tags`
Expected: `index.html` と `mcp/`, `docker/`, `aws/`, `fbc/` がある

Run: `grep -rhoE 'href="/(weekly|tags|recent)[^"]*"' dist | head`
Expected: 出力なし（base 抜けのリンクがない）

Run: `grep -rl '気になった技術情報' dist; grep -rl 'daily' dist --include=*.html`
Expected: 1つ目は `dist/weekly/2026-11-09/index.html` だけ（週報の見出し）。2つ目は出力なし。さらに日報だけにある一文（例: `docker sandboxes 環境にコンテナを配置し`）で `grep -rl` して、出力なし

- [ ] **Step 6: 見た目を確認**

Run: `npm run preview`
Expected: `http://localhost:4321/what_i_learned/` に「2026年度」の下に「11/09〜11/15」の行。クリックで詳細、タグクリックでタグページ。ダークモードでも読める

- [ ] **Step 7: Commit**

```bash
git add src
git commit -m "feat: 週報の一覧・詳細・タグページ"
```

---

### Task 4: 全文検索

**Files:** Modify: `src/pages/index.astro`

**Interfaces:** Consumes: `url`（Task 3）、`#search` と `data-pagefind-body`（Task 3）

- [ ] **Step 1:** `head` スロットに `url('pagefind/pagefind-ui.css')`、本文末尾に `<script is:inline src={url('pagefind/pagefind-ui.js')}>` と `new PagefindUI({ element: '#search', showSubResults: true })`
- [ ] **Step 2: 確認**

Run: `npm run build && npm run preview`
Expected: ビルドログで Pagefind が 1 page を索引。一覧で「猫見守り」「MCP」を検索すると 11/09 の週がヒットし、リンク先が `/what_i_learned/weekly/2026-11-09/`

- [ ] **Step 3: Commit** — `git add src/pages/index.astro && git commit -m "feat: Pagefind による全文検索"`

---

### Task 5: 「この1ヶ月」ページ

**Files:** Create: `src/pages/recent.astro`

**Interfaces:** Consumes: `getWeeklies`（Task 2）、`countRecent`, `todayInTokyo`, `tagSlug`（Task 1）、`url`（Task 3）

- [ ] **Step 1:** ビルド時に `{ id, tags }[]` を `<script type="application/json" id="weekly-data">` に埋め込む。クライアント `<script>`（Astro がバンドル）で `countRecent(data, todayInTokyo())` を計算し、「週報を書いた週: N週 / 4週」と、タグ別回数の表（多い順、タグは `url('tags/' + tagSlug(tag) + '/')` へリンク）を描画。0件なら「直近4週の週報はありません」。`<noscript>` で一言
- [ ] **Step 2: 確認**

Run: `npm run build && npm run preview`
Expected: `/what_i_learned/recent/` に「週報を書いた週: 1週 / 4週」と MCP / Docker / AWS / FBC が各1回（今日が 2026-11-09〜2026-12-06 の場合）

- [ ] **Step 3: Commit** — `git add src/pages/recent.astro && git commit -m "feat: この1ヶ月ページ"`

---

### Task 6: `/weekly` スキル

**Files:** Create: `.claude/skills/weekly/SKILL.md`

**Interfaces:** Consumes: `node scripts/week.ts [date]`（Task 1）、週報のひな形と frontmatter（Task 2 の `CLAUDE.md`）

注意: このセッションのサンドボックスは `.claude/skills` への Bash 書き込みを禁止している。Write ツールで作る（許可を求められたらユーザーが承認する）。書けなければ、内容をユーザーに渡して作ってもらう。

- [ ] **Step 1: SKILL.md を書く**

frontmatter: `name: weekly`、`description`（日報から週報を作る。引数は任意の日付）。本文の手順は設計書の「`/weekly` スキル」のとおりで、次の値を固定する。
1. `node scripts/week.ts $ARGUMENTS` で `<monday> <sunday>` を得る。失敗したらそのメッセージを報告して終了。
2. `weekly/<monday>.md` があれば「既にあります。作り直すなら先に消してください」と報告して終了。
3. `daily/<monday>.md`〜`daily/<sunday>.md` のうち存在するものを読む。1つもなければ「この週の日報がありません」と報告して終了。
4. `weekly/*.md` の既存タグを集め、同じ意味のタグはその表記を使う。
5. ひな形（`## 今週学んだこと` / `## 気になった技術情報` / `## 来週やりたいこと`）で `weekly/<monday>.md` を書く。日報にない内容は書かない。`summary` は1行。
6. `npm run check` を実行し、失敗したら直す。
7. コミット・push はしない。作ったファイルのパスを報告する。

- [ ] **Step 2: 確認（手元）**

1. `/weekly 2026-11-12` → 「既にあります」で止まる（サンプルがあるため）。
2. `weekly/2026-11-09.md` を一時退避して `/weekly 2026-11-12` → `weekly/2026-11-09.md` ができ、`npm run check` が通る。日報にない内容がない。確認後、どちらを残すかユーザーに聞く。
3. `/weekly 2026-10-01` → 「この週の日報がありません」で止まり、ファイルは作られない。

- [ ] **Step 3: Commit** — `git add .claude/skills/weekly && git commit -m "feat: /weekly スキル"`

---

### Task 7: GitHub Actions（公開と週報の手動実行）

**Files:** Create: `.github/workflows/deploy.yml`, `.github/workflows/weekly.yml`

**Interfaces:** Consumes: `npm run build`（Task 1）、`node scripts/week.ts`（Task 1）、`/weekly` スキル（Task 6）

- [ ] **Step 1: `deploy.yml`**

Astro 公式「Deploy to GitHub Pages」の構成どおり。`on: push: branches: [main]` と `workflow_dispatch`。`permissions: contents: read, pages: write, id-token: write`。build は `actions/checkout` → `withastro/action`（`node-version: 24`）。deploy は `actions/deploy-pages`。

- [ ] **Step 2: `weekly.yml`**

- `on: workflow_dispatch: inputs: week: { description: '対象週に含まれる日付 YYYY-MM-DD（空なら先週）', required: false, type: string }`
- `permissions: contents: write, pull-requests: write, id-token: write`
- 手順: `actions/checkout` → `actions/setup-node`（24）→ `npm ci` → `node scripts/week.ts "${{ inputs.week }}"` で monday/sunday を出力変数に（失敗なら終了）→ `anthropics/claude-code-action` に `prompt: /weekly ${{ inputs.week }}` と `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`、ファイルの読み書きと `node` / `npm run check` を許可（入力名と許可ツールの渡し方は action の README で確認）→ `weekly/<monday>.md` が無ければ失敗で終了 → `git switch -c weekly/<monday>`、そのファイルだけ `git add`、コミット、push → `gh pr create --base main --title "週報 <monday>〜<sunday>" --body "/weekly で自動作成。内容を確認してマージしてください。"`（`GH_TOKEN: ${{ github.token }}`）
- `inputs.week` はシェルに直接埋め込まず、`env:` 経由で渡す（コマンドインジェクション対策）

- [ ] **Step 3: 手元で最終確認**

Run: `npm run check` / Expected: テスト全件 PASS、ビルド成功

- [ ] **Step 4: Commit** — `git add .github && git commit -m "ci: 公開と週報作成のワークフロー"`

- [ ] **Step 5: 公開（ユーザーの確認後）**

ユーザーに確認してから `git push -u origin main`。ユーザーの手作業:
1. Settings → Pages で Source を「GitHub Actions」
2. Settings → Actions → General で「Allow GitHub Actions to create and approve pull requests」を有効化
3. Settings → Secrets and variables → Actions に `CLAUDE_CODE_OAUTH_TOKEN`（`claude setup-token` で取得）

Expected:
- `deploy` が成功し、`https://kjman678.github.io/what_i_learned/` で一覧・詳細・タグ・検索・この1ヶ月が動く
- Actions タブの「weekly」に [Run workflow] が出る。`week` に `2026-11-01` を入れて実行 → 日報がないので失敗し、PR は作られない
- 日報がある週で実行 → `weekly/<monday>.md` だけを含む PR ができる
