"""ログ形式の唯一の定義: 型・パース・検証。"""

import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

CONTENT_DIR = Path("content")
LOGS_SUBDIR = "logs"
_LOG_PATTERN = r"logs/\d{4}-\d{2}-\d{2}\.md"
# content からの相対 POSIX パスに対する正規表現（fullmatch）。公開ファイルの種類の唯一の定義
ALLOWED_PATTERNS: tuple[str, ...] = (r"index\.md", _LOG_PATTERN)


@dataclass(frozen=True)
class Section:
    level: int  # 0 = 最初の見出しより前の本文, 1..6 = ATX 見出しの階層
    title: str  # 見出し文字列。level 0 は ""
    body: str  # 次の見出し行の直前までの本文


@dataclass(frozen=True)
class Record:
    date: date
    path: Path
    url_path: str
    tags: tuple[str, ...]
    summary: str | None
    body: str
    sections: tuple[Section, ...]


HEADING = re.compile(r"(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*")
FENCE = re.compile(r"(`{3,}|~{3,})")


def _split_sections(body: str) -> tuple[Section, ...]:
    sections: list[Section] = []
    level, title, chunk = 0, "", []
    fence = ""  # 開いているフェンスの記号列。空なら外側
    for line in body.splitlines(keepends=True):
        f = FENCE.match(line)
        if f:
            if not fence:
                fence = f[1]
            elif f[1][0] == fence[0] and len(f[1]) >= len(fence):
                fence = ""
        m = None if fence else HEADING.fullmatch(line.rstrip("\r\n"))
        if m is None:
            chunk.append(line)
            continue
        if level or "".join(chunk).strip():
            sections.append(Section(level, title, "".join(chunk)))
        level, title, chunk = len(m[1]), m[2] or "", []
    if level or "".join(chunk).strip():
        sections.append(Section(level, title, "".join(chunk)))
    return tuple(sections)


class RecordError(Exception):
    def __init__(self, path: Path, reason: str):
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


def parse_record(path: Path) -> Record:
    def fail(reason: str):
        raise RecordError(path, reason)

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", path.name):
        fail("ファイル名が YYYY-MM-DD.md 形式ではありません")
    try:
        day = date.fromisoformat(path.stem)
    except ValueError:
        fail("存在しない日付です")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail("UTF-8 として読み取れません")
    except OSError as e:
        fail(f"ファイルを読み取れません（{e.strerror}）")

    lines = text.splitlines(keepends=True)
    fences = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == "---"]
    if not fences or fences[0] != 0 or len(fences) < 2:
        fail("frontmatter の開始/終了の `---` がありません")
    end = fences[1]
    try:
        meta = yaml.safe_load("".join(lines[1:end]))
    except yaml.YAMLError:
        fail("frontmatter が YAML として解釈できません")
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        fail("frontmatter が YAML の mapping ではありません")

    tags = meta.get("tags")
    if tags is None or tags == []:
        fail("frontmatter に tags がありません")
    if not isinstance(tags, list):
        fail("tags はリストで書いてください")
    if not all(isinstance(t, str) and t.strip() for t in tags):
        fail("tags に空または文字列でない要素があります")

    summary = meta.get("summary")
    if summary is not None and (not isinstance(summary, str) or "\n" in summary):
        fail("summary は 1 行の文字列で書いてください")

    body = "".join(lines[end + 1 :])
    return Record(
        date=day,
        path=path,
        url_path=f"logs/{day.isoformat()}/",
        tags=tuple(tags),
        summary=summary,
        body=body,
        sections=_split_sections(body),
    )


class RecordsInvalid(Exception):
    def __init__(self, errors: Iterable[RecordError]):
        self.errors = tuple(sorted(errors, key=lambda e: e.path))
        super().__init__("\n".join(str(e) for e in self.errors))


def load_records(content_dir: Path = CONTENT_DIR) -> list[Record]:
    records: list[Record] = []
    errors: list[RecordError] = []
    for path in sorted((content_dir / LOGS_SUBDIR).glob("*.md")):
        if path.name.startswith("."):
            continue
        try:
            records.append(parse_record(path))
        except RecordError as e:
            errors.append(e)
    if errors:
        raise RecordsInvalid(errors)
    return sorted(records, key=lambda r: r.date)


def check_paths(
    paths: Iterable[Path], content_dir: Path = CONTENT_DIR
) -> list[RecordError]:
    # シンボリックリンクをたどらずに位置を判定する（resolve すると、content 内の
    # リンクの実体が外にあるとき「公開ディレクトリ外」として素通りしてしまう）
    root = Path(os.path.abspath(content_dir))
    errors: list[RecordError] = []
    for path in paths:
        try:
            rel = Path(os.path.abspath(path)).relative_to(root)
        except ValueError:
            continue  # 公開ディレクトリ外
        if any(part.startswith(".") for part in rel.parts):
            continue  # ドットファイル・ドットディレクトリ
        if any(
            (root.joinpath(*rel.parts[: i + 1])).is_symlink()
            for i in range(len(rel.parts))
        ):
            errors.append(
                RecordError(path, "シンボリックリンクは公開ディレクトリに置けません")
            )
            continue
        if not path.is_file():
            continue  # 削除済み・ディレクトリ
        name = rel.as_posix()
        if not any(re.fullmatch(p, name) for p in ALLOWED_PATTERNS):
            errors.append(
                RecordError(
                    path,
                    "公開ディレクトリに置けないファイルです"
                    "（wil.records.ALLOWED_PATTERNS を参照）",
                )
            )
        elif re.fullmatch(_LOG_PATTERN, name):
            try:
                parse_record(path)
            except RecordError as e:
                errors.append(e)
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args and not CONTENT_DIR.is_dir():
        # 実行場所が違うと何も検査せずに成功してしまうので、失敗にする
        print(
            f"{CONTENT_DIR}: 公開ディレクトリが見つかりません"
            "（リポジトリルートで実行してください）",
            file=sys.stderr,
        )
        return 1
    paths = [Path(a) for a in args] if args else sorted(CONTENT_DIR.rglob("*"))
    errors = check_paths(paths)
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
