# 学んだことの記録サイト Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `records/YYYY-MM-DD.md` に書いた1日分の記録を、年度別一覧・詳細・タグ・全文検索・直近30日ページを持つ静的サイトとして GitHub Pages に公開する。

**Architecture:** Astro の Content Collection（glob loader）で `records/` を読み、Zod スキーマとファイル名チェックで書式を厳しく検証する。日付・年度・タグ・30日集計の計算は `src/lib/records-logic.ts` の純粋関数に集め、Node 標準のテストで検証する。ビルド後に Pagefind で検索索引を作り、GitHub Actions で Pages に公開する。

**Tech Stack:** Astro（インストール時点の最新安定版）、Pagefind、Node 24（`node --test` と型ストリップで TS テストを実行）、GitHub Actions（`withastro/action` + `actions/deploy-pages`）

**Spec:** `docs/superpowers/specs/2026-11-15-what-i-learned-site-design.md`

## Global Constraints

- 公開 URL: `https://kjman678.github.io/what_i_learned/`。`astro.config.mjs` は `site: 'https://kjman678.github.io'`、`base: '/what_i_learned'`。
- 記録の置き場所: リポジトリ直下 `records/YYYY-MM-DD.md`。ファイル名が日付。frontmatter に日付は書かない。
- frontmatter: `tags`（文字列配列、1個以上必須）、`summary`（文字列、任意）。
- 書式違反（`tags` なし/空、ファイル名が `YYYY-MM-DD` でない、実在しない日付、YAML 破損）はビルドを失敗させる。
- 年度は4月始まり（4〜12月はその年、1〜3月は前年）。
- 「この1ヶ月」= 今日（Asia/Tokyo）を含む直近30日間。ブラウザ側で集計する。
- UI フレームワーク・CSS ライブラリは入れない。素の CSS、ライト/ダーク両対応、`<html lang="ja">`。
- 依存の追加は `astro` と `pagefind` のみ。テストは `node --test`（追加のテストランナーなし）。
- サイト内リンクはすべて `base` 付き（`/what_i_learned/...`）。

## Review Focus

1. **1〜3月の記録** — 前年度に入る（2026-03-31 は 2025年度、2026-04-01 は 2026年度）。→ Task 1 のテスト。
2. **30日の境界とタイムゾーン** — 今日と29日前は含み、30日前と未来日は含まない。「今日」は JST。→ Task 1 のテスト。
3. **記号・日本語・大小違いのタグ** — `C#` / `C++` / `C` / `CI/CD` / `猫見守り` が衝突しない URL になり、`AWS` と `aws` は同じタグページにまとまる。→ Task 1 のテスト。
4. **実在しない日付のファイル名** — `2026-02-30.md` や `2026-11-5.md` でビルドが失敗する。→ Task 1 のテスト + Task 2 の確認。
5. **base 抜けのリンク** — `/records/...` や `/tags/...` のように base なしのリンクが1つも出力されない。→ Task 3 の確認。

---

### Task 1: プロジェクト骨組みと記録ロジック

**Files:**
- Create: `package.json`, `astro.config.mjs`, `tsconfig.json`, `.gitignore`
- Create: `src/lib/records-logic.ts`
- Test: `src/lib/records-logic.test.ts`

**Interfaces:**
- Produces（すべて `src/lib/records-logic.ts` から export）:
  - `type RecordSummary = { id: string; tags: string[]; summary?: string }` — `id` は `YYYY-MM-DD`
  - `isValidRecordId(id: string): boolean`
  - `fiscalYear(id: string): number`
  - `groupByFiscalYear<T extends { id: string }>(records: T[]): [number, T[]][]` — 年度降順、各年度内は `id` 降順
  - `tagSlug(tag: string): string`
  - `countRecent(records: { id: string; tags: string[] }[], today: string, days?: number): { recordedDays: number; tags: [string, number][] }` — `days` 既定 30。`tags` は回数降順、同数は表記の昇順。表示名は最初に見つかった表記
  - `todayInTokyo(now?: Date): string` — `YYYY-MM-DD`
- npm scripts: `"dev": "astro dev"`, `"build": "astro build && pagefind --site dist"`, `"preview": "astro preview"`, `"test": "node --test src/lib/*.test.ts"`, `"check": "npm test && npm run build"`

- [ ] **Step 1: 骨組みを作る**

`package.json`（`"type": "module"`、上の scripts）を書き、`npm install astro` と `npm install -D pagefind`。`tsconfig.json` は `{"extends": "astro/tsconfigs/strict"}`。`astro.config.mjs` に Global Constraints の `site` と `base`。`.gitignore` は `node_modules/`, `dist/`, `.astro/`。

- [ ] **Step 2: 失敗するテストを書く**

```ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isValidRecordId, fiscalYear, groupByFiscalYear, tagSlug, countRecent, todayInTokyo } from './records-logic.ts';

test('isValidRecordId', () => {
  assert.equal(isValidRecordId('2026-11-15'), true);
  assert.equal(isValidRecordId('2024-02-29'), true);
  assert.equal(isValidRecordId('2026-02-30'), false);
  assert.equal(isValidRecordId('2026-11-5'), false);
  assert.equal(isValidRecordId('memo'), false);
});

test('fiscalYear: 4月始まり', () => {
  assert.equal(fiscalYear('2026-03-31'), 2025);
  assert.equal(fiscalYear('2026-04-01'), 2026);
  assert.equal(fiscalYear('2026-11-15'), 2026);
});

test('groupByFiscalYear: 年度降順・日付降順', () => {
  const r = groupByFiscalYear([{ id: '2026-03-31' }, { id: '2026-11-15' }, { id: '2026-04-01' }]);
  assert.deepEqual(r, [
    [2026, [{ id: '2026-11-15' }, { id: '2026-04-01' }]],
    [2025, [{ id: '2026-03-31' }]],
  ]);
});

test('tagSlug: 衝突しない・大小同一視', () => {
  const slugs = ['C#', 'C++', 'C', 'CI/CD'].map(tagSlug);
  assert.equal(new Set(slugs).size, 4);
  assert.equal(tagSlug('AWS'), tagSlug('aws'));
  assert.equal(tagSlug('猫見守り'), '猫見守り');
  assert.doesNotMatch(tagSlug('CI/CD'), /\//);
});

test('countRecent: 今日と29日前を含み、30日前と未来を含まない', () => {
  const r = countRecent([
    { id: '2026-11-15', tags: ['AWS', 'MCP'] },
    { id: '2026-10-17', tags: ['aws'] },   // 29日前
    { id: '2026-10-16', tags: ['FBC'] },   // 30日前
    { id: '2026-11-16', tags: ['FBC'] },   // 未来
  ], '2026-11-15');
  assert.equal(r.recordedDays, 2);
  assert.deepEqual(r.tags, [['AWS', 2], ['MCP', 1]]);
});

test('todayInTokyo: UTC 15:00 は JST の翌日', () => {
  assert.equal(todayInTokyo(new Date('2026-11-15T15:00:00Z')), '2026-11-16');
});
```

- [ ] **Step 3: 失敗を確認**

Run: `npm test`
Expected: FAIL（`records-logic.ts` が無い）

- [ ] **Step 4: `src/lib/records-logic.ts` を実装**

`isValidRecordId` は正規表現 `^\d{4}-\d{2}-\d{2}$` に加え、UTC で `Date` を作り直して年月日が一致するかで実在を判定。`tagSlug` は小文字化 → `#`→`sharp`、`+`→`plus` に置換 → `\p{L}\p{N}` 以外の連続を `-` に → 前後の `-` を除去。`countRecent` のタグ集計キーは `tagSlug`。`todayInTokyo` は `toLocaleDateString('sv-SE', { timeZone: 'Asia/Tokyo' })`。

- [ ] **Step 5: 通過を確認**

Run: `npm test`
Expected: 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json astro.config.mjs tsconfig.json .gitignore src/lib docs/superpowers
git commit -m "feat: プロジェクト骨組みと記録ロジック"
```

---

### Task 2: 記録コレクションと書式チェック

**Files:**
- Create: `src/content.config.ts`
- Create: `src/lib/records.ts`
- Create: `records/2026-11-15.md`
- Create: `CLAUDE.md`

**Interfaces:**
- Consumes: `isValidRecordId`, `RecordSummary`（Task 1）
- Produces: `getRecords(): Promise<CollectionEntry<'records'>[]>`（`src/lib/records.ts`）— 全記録を `id` 降順で返す。`id` が `isValidRecordId` を満たさない記録があれば `Error('Invalid record filename: records/<id>.md (expected YYYY-MM-DD.md)')` を投げる

- [ ] **Step 1: コレクションを定義**

`src/content.config.ts` に `records` コレクション。`glob({ pattern: '*.md', base: './records' })`、スキーマ `z.object({ tags: z.array(z.string().min(1)).min(1), summary: z.string().optional() })`。

- [ ] **Step 2: `getRecords` を実装**

`getCollection('records')` → 各 `id` を `isValidRecordId` で検査 → `id` 降順でソート。

- [ ] **Step 3: 初期記録を置く**

`records/2026-11-15.md`。frontmatter は `tags: [MCP, Docker, AWS, FBC]`、`summary: MCP本を読んだ / 猫見守りの開発環境を整えた`。本文はユーザーの例（「学習」「気になった技術情報」の入れ子箇条書き、「〜〜」はそのまま）。

- [ ] **Step 4: `CLAUDE.md` に記録の書き方を書く**

置き場所（`records/YYYY-MM-DD.md`）、frontmatter（`tags` 必須・`summary` 任意）、本文の型（「学習」「気になった技術情報」の入れ子箇条書き）、push 前に `npm run check`。10〜20行。

- [ ] **Step 5: 書式チェックが効くことを確認**

仮のページ `src/pages/index.astro` で `getRecords()` を呼び件数を出す（Task 3 で置き換える）。そのうえで以下を1つずつ試し、確認後に削除する。

| 置くファイル | Expected（`npm run build`） |
|---|---|
| なし（初期記録のみ） | 成功 |
| `records/2026-11-14.md`（`tags: []`） | 失敗、`tags` のエラー |
| `records/2026-11-13.md`（frontmatter なし） | 失敗、`tags` のエラー |
| `records/2026-11-12.md`（`tags: [a` で YAML 破損） | 失敗 |
| `records/2026-02-30.md`（正しい frontmatter） | 失敗、`Invalid record filename` |
| `records/memo.md`（正しい frontmatter） | 失敗、`Invalid record filename` |

- [ ] **Step 6: Commit**

```bash
git add src/content.config.ts src/lib/records.ts records CLAUDE.md src/pages/index.astro
git commit -m "feat: 記録コレクションと書式チェック"
```

---

### Task 3: レイアウト・一覧・詳細・タグページ

**Files:**
- Create: `src/layouts/Base.astro`
- Create: `src/lib/url.ts`
- Create: `src/components/RecordList.astro`
- Modify: `src/pages/index.astro`（Task 2 の仮ページを置き換え）
- Create: `src/pages/records/[id].astro`
- Create: `src/pages/tags/[tag].astro`

**Interfaces:**
- Consumes: `getRecords`（Task 2）、`groupByFiscalYear`, `tagSlug`（Task 1）
- Produces:
  - `url(path: string): string`（`src/lib/url.ts`）— `import.meta.env.BASE_URL` を前置。`url('records/2026-11-15/')` → `/what_i_learned/records/2026-11-15/`
  - `Base.astro` props: `{ title: string }`。`<html lang="ja">`、ヘッダーに「一覧」（`url('')`）と「この1ヶ月」（`url('recent/')`）、`<slot />`、`<slot name="head" />`。CSS 変数で配色、`prefers-color-scheme: dark` で切替
  - `RecordList.astro` props: `{ records: CollectionEntry<'records'>[] }` — `groupByFiscalYear` で「YYYY年度」見出し + 各行「MM/DD・summary（あれば）・タグ（タグページへのリンク）」

- [ ] **Step 1: `url.ts` と `Base.astro` を作る**

- [ ] **Step 2: 一覧 `index.astro`**

`Base` + 全タグ一覧（`tagSlug` で重複除去、リンク付き）+ `<div id="search"></div>`（Task 4 で使う）+ `RecordList`。

- [ ] **Step 3: 詳細 `records/[id].astro`**

`getStaticPaths` は `getRecords()` から `{ params: { id }, props: { entry } }`。`render(entry)` で本文を描画。見出しは `YYYY/MM/DD`、タグはタグページへのリンク。本文を囲む要素に `data-pagefind-body`。

- [ ] **Step 4: タグ `tags/[tag].astro`**

`getStaticPaths` は全タグの `tagSlug` ごとに1ページ。props はそのスラッグを持つ記録と表示名（最初に見つかった表記）。中身は見出し `#表示名` + `RecordList`。

- [ ] **Step 5: ビルド出力を確認**

Run: `npm run build && ls dist dist/records/2026-11-15 dist/tags`
Expected: `dist/index.html`, `dist/records/2026-11-15/index.html`, `dist/tags/mcp/index.html` などが存在する

Run: `grep -rhoE 'href="/(records|tags|recent)[^"]*"' dist | head`
Expected: 出力なし（base 抜けのリンクがない）

- [ ] **Step 6: 見た目を確認**

Run: `npm run preview`
Expected: `http://localhost:4321/what_i_learned/` で「2026年度」見出しの下に 11/15 の行、クリックで詳細、タグクリックでタグページ。ダークモードでも読める。

- [ ] **Step 7: Commit**

```bash
git add src
git commit -m "feat: 一覧・詳細・タグページ"
```

---

### Task 4: 全文検索

**Files:**
- Modify: `src/pages/index.astro`

**Interfaces:**
- Consumes: `url`（Task 3）、Task 3 の `#search` 要素と `data-pagefind-body`

- [ ] **Step 1: Pagefind UI を読み込む**

`index.astro` の `head` スロットに `url('pagefind/pagefind-ui.css')`、本文末尾に `<script is:inline src={url('pagefind/pagefind-ui.js')}>` と `new PagefindUI({ element: '#search', showSubResults: true })`。

- [ ] **Step 2: 日本語で検索できることを確認**

Run: `npm run build && npm run preview`
Expected: build ログに Pagefind の索引作成（1 page）。`http://localhost:4321/what_i_learned/` で「猫見守り」と「MCP」を検索すると 2026-11-15 がヒットし、リンク先が `/what_i_learned/records/2026-11-15/`

- [ ] **Step 3: Commit**

```bash
git add src/pages/index.astro
git commit -m "feat: Pagefind による全文検索"
```

---

### Task 5: 「この1ヶ月」ページ

**Files:**
- Create: `src/pages/recent.astro`

**Interfaces:**
- Consumes: `getRecords`（Task 2）、`countRecent`, `todayInTokyo`, `tagSlug`（Task 1）、`url`（Task 3）

- [ ] **Step 1: ページを作る**

ビルド時に `getRecords()` から `{ id, tags }[]` を `<script type="application/json" id="records-data">` に埋め込む。クライアント `<script>`（Astro がバンドル）で `countRecent(data, todayInTokyo())` を計算し、「記録した日数: N日 / 30日」と、タグ別回数の表（多い順、タグ名は `url('tags/' + tagSlug(tag) + '/')` へのリンク）を描画する。記録が0件なら「この30日の記録はありません」。JS 無効時は `<noscript>` で一言。

- [ ] **Step 2: 確認**

Run: `npm run build && npm run preview`
Expected: `http://localhost:4321/what_i_learned/recent/` に「記録した日数: 1日 / 30日」と MCP / Docker / AWS / FBC が各1回（今日が 2026-12-14 以前の場合）

- [ ] **Step 3: Commit**

```bash
git add src/pages/recent.astro
git commit -m "feat: この1ヶ月ページ"
```

---

### Task 6: GitHub Pages への公開

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: ワークフローを書く**

Astro 公式ドキュメント「Deploy to GitHub Pages」の構成どおり。`on: push: branches: [main]` と `workflow_dispatch`、`permissions: contents: read, pages: write, id-token: write`。build ジョブは `actions/checkout` → `withastro/action`（`node-version: 24`。`npm run build` が走るので Pagefind も実行される）。deploy ジョブは `actions/deploy-pages`。各 action はドキュメント記載の最新メジャー版。

- [ ] **Step 2: 手元で最終確認**

Run: `npm run check`
Expected: テスト全件 PASS、ビルド成功

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: GitHub Pages へのデプロイ"
```

- [ ] **Step 4: 公開（ユーザーの確認後）**

ユーザーに確認してから `git push -u origin main`。ユーザーがリポジトリの Settings → Pages で Source を「GitHub Actions」に設定する。

Expected: Actions の deploy が成功し、`https://kjman678.github.io/what_i_learned/` で一覧・詳細・タグ・検索・この1ヶ月が動く。
