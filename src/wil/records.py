"""ログ形式の唯一の定義: 型・パース・検証。"""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml


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


HEADING = re.compile(r"(#{1,6})(?:[ \t]+(.*?))?[ \t]*")


def _split_sections(body: str) -> tuple[Section, ...]:
    sections: list[Section] = []
    level, title, chunk = 0, "", []
    in_fence = False
    for line in body.splitlines(keepends=True):
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
        m = None if in_fence else HEADING.fullmatch(line.rstrip("\r\n"))
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
