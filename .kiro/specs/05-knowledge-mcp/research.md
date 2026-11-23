# Research & Design Decisions

## Summary
- **Feature**: `knowledge-mcp`
- **Discovery Scope**: New Feature（グリーンフィールド。リポジトリにはまだコードが無く、上流 daily-log-page の設計のみが存在する）→ Full discovery
- **Key Findings**:
  - MCP Python SDK は 2026-07 に 2.0 GA となり、同梱の `FastMCP` は `MCPServer` に改名された（`mcp.server.fastmcp` は 2.x で import 不可）。brief・tech.md の「FastMCP」は、この公式 SDK 同梱サーバー API の旧名を指すものとして扱い、`mcp>=2.3,<3` の `MCPServer` で設計する
  - Claude Code は stdio サーバーの作業ディレクトリを保証しない。`CLAUDE_PROJECT_DIR` は「作業中のプロジェクト」を指すため、他プロジェクトから使う本機能のログ置き場所には使えない。登録コマンドを `uv run --directory <リポジトリの絶対パス>` にして作業ディレクトリをリポジトリルートに固定する
  - 日本語の困りごとは空白で区切られないため、空白分割だけでは一致しない。標準ライブラリの正規表現で「英数字の語・カタカナ連続・漢字連続（3 文字以上は 2-gram も追加）」を取り出し、ひらがな（助詞・送り仮名）を捨てる素朴な方法で、依存を増やさずに 1.4 を満たす

## Research Log

### MCP Python SDK の現行 API（2026-11 時点）
- **Context**: brief は「MCP Python SDK（FastMCP）」を指定。現行 API を公式ドキュメントで確認する必要があった
- **Sources Consulted**:
  - https://pypi.org/pypi/mcp/json（最新 2.3.0、2026-10-02。1.x 系も 1.30.0 まで保守継続）
  - https://py.sdk.modelcontextprotocol.io/migration/ ・ /whats-new/（2.x の破壊的変更）
  - https://py.sdk.modelcontextprotocol.io/servers/tools/ ・ /servers/structured-output/ ・ /servers/handling-errors/
  - https://py.sdk.modelcontextprotocol.io/run/ ・ /get-started/testing/ ・ /get-started/real-host/ ・ /get-started/installation/
  - https://github.com/modelcontextprotocol/python-sdk（README）
- **Findings**:
  - import: `from mcp.server import MCPServer`（`from mcp.server.mcpserver import MCPServer` も可）。生成は `MCPServer("name", instructions=...)`。`name` 以外はキーワード引数で渡す（位置引数の並びが変わったため）
  - ツール定義: `@server.tool()`。型ヒントから入力 JSON Schema、docstring から説明、デフォルト無し引数は必須。`Annotated[T, Field(description=...)]` で引数説明を付けられる。同期関数はスレッドで実行される
  - 戻り値: dataclass / TypedDict / pydantic モデル / `dict[str, ...]` は `structured_content` にそのまま入り、テキスト `content` も併せて返る。戻り値注釈が `output_schema` になり、出力は検証される
  - エラー: `from mcp.server.mcpserver.exceptions import ToolError`。`ToolError("msg")` は `is_error=True`、本文「Error executing tool <name>: msg」でモデルに見える。それ以外の例外はメッセージが隠される（「Error executing tool <name>」のみ）。エラー文字列を通常の戻り値で返すと `is_error=False` になる
  - 実行: `server.run()` の既定トランスポートは stdio。stdout はプロトコル専用。ログは `logging`（stderr）に出す
  - Python: PyPI 上は `>=3.10`、ドキュメントは 3.11+。どちらでも 3.12 で問題ない
  - `mcp[cli]` extra は `mcp dev` 等の CLI 用で、自前で `run()` を呼ぶサーバーには不要（明記はないが extra の内容から導出）
  - テスト: `Client(server)` でトランスポート無しのインプロセス呼び出しができる（`async with Client(server, raise_exceptions=True) as c: await c.call_tool(...)`）。v1 の `create_connected_server_and_client_session` は削除。anyio の pytest プラグイン（`@pytest.mark.anyio` + `anyio_backend` fixture）を使う
- **Implications**:
  - 依存は `mcp>=2.3,<3`（extra なし）。`mcp.server.fastmcp` を前提にしたサンプルを流用しない
  - 不正ログ・入力誤りなど呼び出し側に見せたい失敗は必ず `ToolError` に変換する（素の例外ではメッセージが隠れ、5.3・5.4 の「理由を示す」を満たせない）
  - 戻り値は dataclass にし、構造化出力（2.5）を SDK に任せる
- **未確認（実装時に確認）**: `Client` の正確な import パス（`from mcp import Client` と推定）、`server.run(transport="stdio")` の明示指定可否（既定値で足りるため使わない）、`Client(server, raise_exceptions=True)` でツールエラーが結果（`is_error=True`）として返るか例外として送出されるか（送出される場合はエラー経路のテストではこの引数を外す。タスク 1.1 で確認）

### 単体の `fastmcp` パッケージとの関係
- **Context**: 「FastMCP」という名前が PyPI の別パッケージ（PrefectHQ/fastmcp）も指しうる
- **Sources Consulted**: https://pypi.org/pypi/fastmcp/json（4.2.5）、https://gofastmcp.com/getting-started/welcome
- **Findings**: FastMCP 1.0 が 2024 年に公式 SDK に取り込まれ、その後継が SDK 同梱の `MCPServer`。単体 `fastmcp` は別 API（`from fastmcp import FastMCP`）で依存も大きい
- **Implications**: 公式 SDK の `MCPServer` を採用し、単体 `fastmcp` は採用しない（依存最小の steering に合致）

### Claude Code への登録と作業ディレクトリ
- **Context**: サーバーは `wil.records.CONTENT_DIR`（作業ディレクトリ基準の `content`）と `zensical.toml` を読む。作業ディレクトリがリポジトリルートである必要がある
- **Sources Consulted**: https://code.claude.com/docs/en/mcp 、https://py.sdk.modelcontextprotocol.io/get-started/real-host/
- **Findings**:
  - 構文: `claude mcp add [options] <name> -- <command> [args...]`。`--` 以降はサーバーにそのまま渡る。スコープは local（既定）/ project（`.mcp.json`）/ user（`~/.claude.json`）
  - stdio サーバーの作業ディレクトリは文書化されていない。SDK ドキュメントは「ホストは自分の作業ディレクトリでサーバーを起動する」「相対パスが最も多い失敗原因」と警告
  - Claude Code はサーバー環境に `CLAUDE_PROJECT_DIR`（作業中プロジェクトのルート）を設定する
- **Implications**:
  - 他プロジェクトでの作業中にも使う（7.1）ため user スコープで登録し、`CLAUDE_PROJECT_DIR` は使わない（作業中の別プロジェクトを指してしまう）
  - 登録コマンド: `claude mcp add --scope user --transport stdio wil-knowledge -- uv run --directory <リポジトリの絶対パス> python -m wil.knowledge_mcp`。`uv run --directory` はコマンド実行前に作業ディレクトリを移す（公式 MCP 文書の推奨ではなく uv の機能。実装時に `uv run --help` で確認）
  - 作業ディレクトリが誤っている場合に空の結果を返して誤解させないよう、`content/logs` の存在を毎回確認し、無ければ登録コマンドの確認を促すエラーにする（5.4）
  - 公開リポジトリのため、手順書の例はプレースホルダを使う（7.2）

### 上流 `wil.records` の契約
- **Context**: パースを再実装しない（steering / brief）
- **Sources Consulted**: `.kiro/specs/01-daily-log-page/design.md`（Records、Data Contracts）
- **Findings**:
  - `load_records(content_dir=CONTENT_DIR) -> list[Record]`（日付昇順）。不正が 1 件でもあれば全件の `RecordError` を持つ `RecordsInvalid` を送出。0 件なら空リスト。`content_dir/logs` が無くても空リストになる（＝誤設定を検出できない）
  - `Record(date, path, url_path, tags, summary, body, sections)`、`Section(level, title, body)`。level 0 は最初の見出しより前（title ""）。tags は書かれたとおり（正規化なし）
  - 公開 URL は `zensical.toml` の `[project].site_url` と `Record.url_path` の連結（上流の「下流 spec の利用方法」）
  - daily-log-page の design は現時点で未承認（`approvals.design.approved: false`）。コードも未実装
- **Implications**: `load_records` と `CONTENT_DIR` / `LOGS_SUBDIR` だけを使う。ログ置き場所の存在確認は本機能で行う。site_url は標準ライブラリ `tomllib` で読む

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| 純粋ロジック + 薄いサーバー（採用） | 検索・取得を `list[Record]` を受ける純関数群に置き、MCP 層はロード・エラー変換・ツール登録だけを行う | ロジックを MCP なしで単体テストできる。brief の境界候補（ツール定義 / 検索ロジック）と一致 | ファイルが 2 つになる | ponytail 観点でも分離は 1 つだけ |
| 1 モジュールに全部 | サーバーと検索を同一ファイルに置く | ファイル最少 | ロジックのテストが MCP の import に依存。境界がコード上で見えない | 不採用 |
| 起動時インデックス + ファイル監視 | 起動時に転置インデックスを作り、変更を監視 | 大規模ログで高速 | 監視の複雑さ、5.2 の最新性で不整合リスク。ログ数（年 365 件程度）では不要 | 不採用（毎回ロード） |

## Design Decisions

### Decision: SDK は公式 `mcp` 2.x の `MCPServer`
- **Context**: brief・tech.md は「FastMCP」を指定。2.x で改名済み
- **Alternatives Considered**:
  1. `mcp<2` に固定して `mcp.server.fastmcp.FastMCP` を使う
  2. 単体 `fastmcp` パッケージ
  3. `mcp>=2.3,<3` の `MCPServer`
- **Selected Approach**: 3
- **Rationale**: 公式 SDK の現行主系統で、旧 FastMCP の直系。1 は新規コードで旧系統に縛られ、2 は依存が大きく別 API
- **Trade-offs**: 2.x の Web 上のサンプルがまだ少ない。tech.md の「FastMCP」表記が古くなる
- **Follow-up**: steering（tech.md の Key Libraries）の表記更新は本 spec の範囲外。`/kiro-steering` での同期を推奨

### Decision: 関連度は標準ライブラリの語句一致（埋め込み検索は採用しない）
- **Context**: 1.1〜1.5。日本語の文でも一致させたい。依存は増やしたくない
- **Alternatives Considered**:
  1. 空白分割の語句一致
  2. 文字 2-gram のみ
  3. 正規表現で英数字語・カタカナ連続・漢字連続を抽出（漢字 3 文字以上は 2-gram も追加）、ひらがなは捨てる。tags 一致を最優先、次に区間内で一致した語句の種類数
  4. 形態素解析（janome 等）や埋め込み（sentence-transformers 等）
- **Selected Approach**: 3
- **Rationale**: 1 は日本語の文で一致しない。2 は助詞を含む 2-gram（「のコ」等）がノイズになる。4 は重い依存・モデル取得（ネットワーク）を伴い、brief の制約に反する。3 は数十行の標準ライブラリで、カタカナ技術語・英字の技術名・漢字熟語を拾える
- **Trade-offs**: 同義語・言い換え（「遅い」と「レイテンシ」）は拾えない。ひらがな表記の語は拾えない（ひらがなのみの困りごとは全体を 1 語として扱う）
- **Follow-up**: 呼び出し側の Claude に「主要な語句を渡す」よう説明で促す（7.3）。不足が実際に示されたら、埋め込みまたは形態素解析を別途検討する（上限と移行先は design の Performance に記載）

### Decision: tags 一致は辞書式順序で最優先
- **Context**: 1.2「tags と一致する区間を本文のみに一致する区間より高い関連度として扱う」
- **Alternatives Considered**: 1. 重み付き加算（tags ×3 + 本文 ×1）2. 並び順キー（tags 一致数, 本文一致語数, 日付）の辞書式比較
- **Selected Approach**: 2
- **Rationale**: 加算では本文の多数一致が tags 一致を上回り、1.2 を厳密に満たせない。辞書式なら常に満たし、説明も単純
- **Trade-offs**: tags が一致したログのうち本文に一致しない区間をどう返すかが問題になる → そのログの「本文が空でない最初の区間」を 1 件だけ候補にする（全区間を返すと結果が埋まる）

### Decision: 不正ログがあれば全体をエラーにする
- **Context**: 5.3。`load_records` は不正が 1 件でもあると `RecordsInvalid` を送出し、正常分を返さない
- **Alternatives Considered**: 1. `RecordsInvalid` をそのままエラーにする 2. `parse_record` をファイルごとに呼び、正常分の結果 + 警告を返す
- **Selected Approach**: 1
- **Rationale**: 上流の「不正なログを黙って除外しない」と同じ振る舞いで、上流のファイル走査を再実装しない。pre-commit で不正ログはコミットされないため、発生するのは書きかけの作業ツリーに限られる
- **Trade-offs**: 書きかけのログが 1 件壊れていると検索全体が止まる
- **Follow-up**: 運用上困る場合は 2 に切り替える（`wil.records` に「正常分 + 誤り」を返す関数を追加するのが筋。上流の変更になる）

### Decision: 毎回ロード（キャッシュなし）
- **Context**: 5.2 の最新性、5.6 の 1,000 件 2 秒以内
- **Selected Approach**: ツール呼び出しごとに `load_records()` と `zensical.toml` を読む
- **Rationale**: 再起動なしで変更が反映され、キャッシュ無効化の論点が消える。1 件数 KB × 1,000 件の YAML + 区間分割は 1 秒未満の見込み
- **Follow-up**: 1,000 件の一時ログでの計測をテストに含める

### Decision: 抜粋は区間本文の先頭から
- **Context**: 2.4
- **Alternatives Considered**: 1. 区間本文の先頭 300 文字 2. 最初の一致位置を中心に 300 文字
- **Selected Approach**: 1
- **Rationale**: 見出し単位で既に局所化されている。正規化（NFKC）後の位置と原文の位置の対応を取る処理が不要
- **Trade-offs**: 長い区間の後半で一致した場合、抜粋に一致箇所が含まれないことがある。全文は `get_log` で取れる

### Synthesis（一般化・採用/自作・簡素化）
- **一般化**: 3 機能はすべて「ログ一覧を読み → `Record` を結果の形に写す」。共通部分は `_load()`（ロード + 存在確認 + site_url）と `LogSummary` への写像の 2 つだけに集約し、汎用のクエリ層は作らない
- **採用/自作**: MCP プロトコル・入力スキーマ・構造化出力・エラー表現は SDK を採用。検索は既存ライブラリ（Whoosh、SQLite FTS5 など）も検討したが、FTS5 の既定トークナイザは日本語を分割せず、Whoosh は保守停止。数十行の自作が最小
- **簡素化**: 起動時インデックス、ファイル監視、設定ファイル、ログ単位の結果集約、タグ絞り込み付き検索、件数上限のスキーマ二重定義（検証はロジック側 1 か所）を削った

## Risks & Mitigations
- 上流 daily-log-page の設計が未承認・未実装 — `Record` / `load_records` / `url_path` / `site_url` の変更を Revalidation Trigger とし、実装は daily-log-page の `wil.records` 完成後に行う
- `mcp` 2.x の API 変化（2.x は 2026-07 GA で若い）— `<3` で上限を固定し、`uv.lock` で版を固定。インプロセスのサーバーテストで API 破損を検出する
- 作業ディレクトリ誤設定で空結果になる — `content/logs` の存在確認と、登録コマンドを示すエラー（5.4）
- stdout への出力でプロトコルが壊れる — `print` を使わない。ログは `logging`（stderr）のみ
- 語句一致の検索品質が不足する — 呼び出し側 Claude への説明で語句抽出を促す。不足が示されたら形態素解析・埋め込みを再検討

## References
- [mcp on PyPI](https://pypi.org/project/mcp/) — 版と依存
- [MCP Python SDK docs](https://py.sdk.modelcontextprotocol.io/) — `MCPServer`、ツール、構造化出力、エラー、テスト、移行ガイド
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) — README
- [Claude Code MCP](https://code.claude.com/docs/en/mcp) — `claude mcp add`、スコープ、`.mcp.json`
- [FastMCP (standalone)](https://gofastmcp.com/getting-started/welcome) — 単体パッケージとの関係
- `.kiro/specs/01-daily-log-page/design.md` — `wil.records` の契約
