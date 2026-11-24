# what_i_learned

日々の学習ログを GitHub Pages で公開するサイト。この README は `content/` の外にあるため公開されない。

## ログの書き方

- 置き場所: `content/logs/YYYY-MM-DD.md`（1 日 1 ファイル。例: `content/logs/2026-11-23.md`）
- ファイル名は暦上存在する日付の `YYYY-MM-DD.md` にする。文字コードは UTF-8
- 先頭に frontmatter を書く。`tags` は必須（1 個以上のリスト）、`summary` は任意（1 行）

```markdown
---
tags:
  - aws
  - lambda
summary: Lambda のコールドスタート対策を調べた
---

## 学んだこと

- SnapStart
  - Java 以外でも使える条件
```

- `tags` は単一の文字列では書けない（検証で不可になる）

```yaml
tags: aws        # 不可
tags: [aws]      # 可
```

- 見出しは `##` 以下を推奨（`#` を書くとページのタイトルが日付から置き換わる）

## 確認と公開

| 目的 | コマンド |
|------|----------|
| プレビュー | `uv run zensical serve` |
| ログの検証 | `uv run python -m wil.records [パス ...]`（省略時は `content/` 全体） |
| コミット前検査を全件に実行 | `uv run pre-commit run --all-files` |
| ビルド（検証込み、`site/` に出力） | `./scripts/build.sh` |

公開は `main` に push するだけ。GitHub Actions がテスト・ビルドのあと GitHub Pages にデプロイする。途中で失敗した場合、公開内容は前回のまま。

## オーナーの初回作業

1. 依存を入れる: `uv sync`
2. コミット前検査を有効にする: `uv run pre-commit install`
3. GitHub のリポジトリ設定 → Pages → Source を「GitHub Actions」に切り替える
4. `scripts/build.sh` を実行権付きでコミットする。`git add` 後に `git ls-files -s scripts/build.sh` が `100755` で始まることを確認し、違えば `git update-index --chmod=+x scripts/build.sh`
