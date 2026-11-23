from datetime import date

import pytest

from wil.records import Record, RecordError, Section, _split_sections, parse_record

VALID = """\
---
tags:
  - aws
  - lambda
summary: Lambda のコールドスタート対策を調べた
---

## 学んだこと

- SnapStart
  - Java 以外でも使える条件
"""


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_record(tmp_path):
    path = write(tmp_path, "2026-11-23.md", VALID)
    record = parse_record(path)
    assert isinstance(record, Record)
    assert record.date == date(2026, 11, 23)
    assert record.path == path
    assert record.url_path == "logs/2026-11-23/"
    assert record.tags == ("aws", "lambda")
    assert record.summary == "Lambda のコールドスタート対策を調べた"
    assert record.body == (
        "\n## 学んだこと\n\n- SnapStart\n  - Java 以外でも使える条件\n"
    )


def test_summary_is_optional_and_unknown_keys_ignored(tmp_path):
    text = "---\ntags: [aws]\nhide: [navigation]\ntitle: x\n---\nbody\n"
    record = parse_record(write(tmp_path, "2026-01-05.md", text))
    assert record.summary is None
    assert record.tags == ("aws",)
    assert record.body == "body\n"


def assert_error(path, reason_part):
    with pytest.raises(RecordError) as info:
        parse_record(path)
    assert info.value.path == path
    assert reason_part in info.value.reason
    assert str(info.value) == f"{path}: {info.value.reason}"


@pytest.mark.parametrize("name", ["2026-1-5.md", "notes.md"])
def test_bad_filename(tmp_path, name):
    assert_error(
        write(tmp_path, name, VALID), "ファイル名が YYYY-MM-DD.md 形式ではありません"
    )


def test_nonexistent_date(tmp_path):
    assert_error(write(tmp_path, "2026-02-30.md", VALID), "存在しない日付です")


def test_not_utf8(tmp_path):
    path = tmp_path / "2026-11-23.md"
    path.write_bytes("---\ntags: [日本語]\n---\n".encode("shift_jis"))
    assert_error(path, "UTF-8 として読み取れません")


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("# no frontmatter\n", "frontmatter の開始/終了の `---` がありません"),
        ("---\ntags: [aws]\nbody\n", "frontmatter の開始/終了の `---` がありません"),
        ("---\ntags: [aws\n---\n", "YAML として解釈できません"),
        ("---\n- aws\n---\n", "frontmatter が YAML の mapping ではありません"),
    ],
    ids=["no-frontmatter", "no-end", "broken-yaml", "not-mapping"],
)
def test_bad_frontmatter(tmp_path, text, reason):
    assert_error(write(tmp_path, "2026-11-23.md", text), reason)


@pytest.mark.parametrize(
    ("frontmatter", "reason"),
    [
        ("summary: x", "tags がありません"),
        ("", "tags がありません"),
        ("tags: []", "tags がありません"),
        ("tags: aws", "tags はリストで書いてください"),
        ("tags: [2026]", "tags に空または文字列でない要素があります"),
        ('tags: [""]', "tags に空または文字列でない要素があります"),
        ('tags: ["  "]', "tags に空または文字列でない要素があります"),
    ],
    ids=[
        "missing",
        "empty-frontmatter",
        "empty-list",
        "string",
        "int",
        "empty-str",
        "blank-str",
    ],
)
def test_bad_tags(tmp_path, frontmatter, reason):
    text = f"---\n{frontmatter}\n---\n"
    assert_error(write(tmp_path, "2026-11-23.md", text), reason)


@pytest.mark.parametrize(
    "summary",
    ["summary: [a, b]", "summary: |\n  line1\n  line2"],
    ids=["list", "multiline"],
)
def test_bad_summary(tmp_path, summary):
    text = f"---\ntags: [aws]\n{summary}\n---\n"
    assert_error(
        write(tmp_path, "2026-11-23.md", text),
        "summary は 1 行の文字列で書いてください",
    )


def test__split_sections_by_heading_level():
    body = "## A\na1\n### B\nb1\n\n## C\n"
    assert _split_sections(body) == (
        Section(2, "A", "a1\n"),
        Section(3, "B", "b1\n\n"),
        Section(2, "C", ""),
    )


def test_hash_lines_in_code_fences_are_not_headings():
    body = "## Run\n```bash\n# comment\n```\n~~~\n# tilde\n~~~\n"
    assert _split_sections(body) == (
        Section(2, "Run", "```bash\n# comment\n```\n~~~\n# tilde\n~~~\n"),
    )


def test_text_before_first_heading_is_level_0():
    assert _split_sections("intro\n\n## A\na\n") == (
        Section(0, "", "intro\n\n"),
        Section(2, "A", "a\n"),
    )


def test_blank_leading_text_and_non_headings():
    assert _split_sections("\n## A\n#tag\n####### seven\n") == (
        Section(2, "A", "#tag\n####### seven\n"),
    )
    assert _split_sections("") == ()


def test_parse_record_fills_sections(tmp_path):
    record = parse_record(write(tmp_path, "2026-11-23.md", VALID))
    assert record.sections == (
        Section(2, "学んだこと", "\n- SnapStart\n  - Java 以外でも使える条件\n"),
    )
