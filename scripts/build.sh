#!/bin/sh
# 唯一のビルド手順（手元・CI 共通）。リポジトリルートで ./scripts/build.sh を実行する
set -eu

# 1. 検証: 公開ディレクトリ全体
uv run python -m wil.records

# 2. 生成
# --- pre-build generation: 後続 spec がここに生成コマンドを追加する ---

# 3. ビルド
uv run zensical build --clean --strict
