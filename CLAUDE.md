# what_i_learned

学んだことの記録。日報（非公開扱い）から週報を作り、週報だけを GitHub Pages に公開する。
公開先: https://kjman678.github.io/what_i_learned/

## 日報 `daily/YYYY-MM-DD.md`

- 自由書式。frontmatter もタグも不要。サイトには出ない（リポジトリは公開なので GitHub 上では読める）。
- 「学習」「気になった技術情報」などの見出しの下に、入れ子の箇条書きで書く。

## 週報 `weekly/YYYY-MM-DD.md`

- ファイル名はその週（月曜〜日曜）の**月曜の日付**。
- frontmatter は `tags`（1個以上必須）と `summary`（1行、任意）だけ。
- 本文は次の3見出し。日報にない内容は書かない。

```markdown
---
tags: [MCP, Docker]
summary: 一行のまとめ
---

## 今週学んだこと
## 気になった技術情報
## 来週やりたいこと
```

- 作り方: `/weekly [日付]`（日付を含む週。省略時は先週）。GitHub の Actions → weekly → Run workflow でも作れる（結果は PR）。
- 作り直すときは、既存の `weekly/<月曜>.md` を消してから `/weekly` を実行する。

## コマンド

- `npm run check` — テストとビルド（書式チェック込み）。push 前に実行する。
- `npm run dev` / `npm run build && npm run preview` — 確認用（検索は build 後のみ動く）。
- `node scripts/week.ts [日付]` — 対象週の `<月曜> <日曜>` を出す。
