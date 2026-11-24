from datetime import date
from pathlib import Path

import pytest

from wil.records import (
    ALLOWED_PATTERNS,
    Record,
    RecordError,
    RecordsInvalid,
    Section,
    _split_sections,
    check_paths,
    load_records,
    main,
    parse_record,
)

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


def make_content(tmp_path):
    content = tmp_path / "content"
    (content / "logs").mkdir(parents=True)
    return content


def test_load_records_ascending(tmp_path):
    content = make_content(tmp_path)
    for name in ["2026-11-23.md", "2026-01-05.md", "2026-03-10.md"]:
        write(content / "logs", name, VALID)
    records = load_records(content)
    assert [r.date for r in records] == [
        date(2026, 1, 5),
        date(2026, 3, 10),
        date(2026, 11, 23),
    ]


def test_load_records_empty(tmp_path):
    assert load_records(make_content(tmp_path)) == []
    assert load_records(tmp_path / "missing") == []


def test_load_records_skips_dot_files(tmp_path):
    logs = make_content(tmp_path) / "logs"
    write(logs, "2026-11-23.md", VALID)
    write(logs, ".draft.md", "not a log")
    assert [r.date for r in load_records(logs.parent)] == [date(2026, 11, 23)]


def test_load_records_reports_all_errors(tmp_path):
    logs = make_content(tmp_path) / "logs"
    write(logs, "2026-11-23.md", VALID)
    bad_date = write(logs, "2026-02-30.md", VALID)
    no_tags = write(logs, "2026-01-01.md", "---\nsummary: x\n---\n")
    with pytest.raises(RecordsInvalid) as info:
        load_records(logs.parent)
    errors = info.value.errors
    assert [e.path for e in errors] == [no_tags, bad_date]
    assert "tags がありません" in errors[0].reason
    assert "存在しない日付です" in errors[1].reason
    assert str(info.value) == "\n".join(str(e) for e in errors)


def test_allowed_patterns():
    assert {r"index\.md", r"logs/\d{4}-\d{2}-\d{2}\.md"} <= set(ALLOWED_PATTERNS)


def test_check_paths_valid_files(tmp_path):
    content = make_content(tmp_path)
    paths = [
        write(content, "index.md", "# top\n"),
        write(content / "logs", "2026-11-23.md", VALID),
    ]
    assert check_paths(paths, content) == []


def test_check_paths_reports_disallowed_and_invalid(tmp_path):
    content = make_content(tmp_path)
    foo = write(content, "foo.txt", "x")
    outside_logs = write(content, "2026-11-23.md", VALID)
    bad_log = write(content / "logs", "2026-02-30.md", VALID)
    errors = check_paths([foo, outside_logs, bad_log], content)
    assert [e.path for e in errors] == [foo, outside_logs, bad_log]
    not_allowed = (
        "公開ディレクトリに置けないファイルです（wil.records.ALLOWED_PATTERNS を参照）"
    )
    assert errors[0].reason == not_allowed
    assert errors[1].reason == not_allowed
    assert "存在しない日付です" in errors[2].reason


def test_check_paths_ignores_dot_outside_and_deleted(tmp_path):
    content = make_content(tmp_path)
    (content / ".obsidian").mkdir()
    paths = [
        write(content, ".DS_Store", "x"),
        write(content / ".obsidian", "x.md", "x"),
        write(tmp_path, "outside.txt", "x"),
        content / "logs" / "2026-11-24.md",  # 削除済み
        content / "logs",  # ディレクトリ
    ]
    assert check_paths(paths, content) == []


def test_check_paths_accepts_relative_paths(tmp_path, monkeypatch):
    content = make_content(tmp_path)
    write(content, "foo.txt", "x")
    monkeypatch.chdir(tmp_path)
    errors = check_paths([Path("content/foo.txt")], Path("content"))
    assert [e.path for e in errors] == [Path("content/foo.txt")]


def test_main_reports_errors_and_exits_1(tmp_path, monkeypatch, capsys):
    content = make_content(tmp_path)
    write(content, "index.md", "# top\n")
    write(content, "foo.txt", "x")
    write(content / "logs", "2026-02-30.md", VALID)
    monkeypatch.chdir(tmp_path)
    args = ["content/index.md", "content/foo.txt", "content/logs/2026-02-30.md"]
    assert main(args) == 1
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("content/foo.txt: 公開ディレクトリに置けない")
    assert lines[1].startswith("content/logs/2026-02-30.md: 存在しない日付です")


def test_main_valid_files_exit_0(tmp_path, monkeypatch, capsys):
    content = make_content(tmp_path)
    write(content, "index.md", "# top\n")
    write(content / "logs", "2026-11-23.md", VALID)
    monkeypatch.chdir(tmp_path)
    assert main(["content/index.md", "content/logs/2026-11-23.md"]) == 0
    assert capsys.readouterr().err == ""


def test_main_without_args_checks_whole_content(tmp_path, monkeypatch, capsys):
    content = make_content(tmp_path)
    write(content, "index.md", "# top\n")
    write(content, ".DS_Store", "x")
    write(content / "logs", "2026-11-23.md", VALID)
    write(content / "logs", "2026-02-30.md", VALID)
    monkeypatch.chdir(tmp_path)
    assert main([]) == 1
    lines = capsys.readouterr().err.splitlines()
    assert lines == ["content/logs/2026-02-30.md: 存在しない日付です"]
    (content / "logs" / "2026-02-30.md").unlink()
    assert main([]) == 0


def test_main_on_real_content_exits_0(monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    assert main([]) == 0


def test_main_without_args_fails_when_content_dir_is_missing(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 1
    assert "公開ディレクトリが見つかりません" in capsys.readouterr().err


def test_check_paths_rejects_symlinks_even_when_target_is_outside(tmp_path):
    content = make_content(tmp_path)
    outside = write(tmp_path, "secret.md", VALID)
    link = content / "logs" / "2026-11-24.md"
    link.symlink_to(outside)
    errors = check_paths([link], content)
    assert [e.reason for e in errors] == [
        "シンボリックリンクは公開ディレクトリに置けません"
    ]


def test_check_paths_rejects_files_under_a_symlinked_directory(tmp_path):
    content = make_content(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    write(elsewhere, "2026-11-24.md", VALID)
    (content / "linked").symlink_to(elsewhere, target_is_directory=True)
    errors = check_paths([content / "linked" / "2026-11-24.md"], content)
    assert len(errors) == 1


def test_unreadable_log_is_a_record_error_not_an_oserror(tmp_path):
    content = make_content(tmp_path)
    (content / "logs" / "2026-11-24.md").mkdir()
    with pytest.raises(RecordsInvalid) as info:
        load_records(content)
    assert "読み取れません" in info.value.errors[0].reason


def test_fence_closes_only_with_same_marker_and_length():
    body = "## A\n````md\n```\n# not heading\n```\n# still inside\n````\n## B\n"
    sections = _split_sections(body)
    assert [(s.level, s.title) for s in sections] == [(2, "A"), (2, "B")]


def test_closing_hashes_are_not_part_of_the_title():
    assert _split_sections("## Foo ##\nx\n") == (Section(2, "Foo", "x\n"),)
    assert _split_sections("# C#\n") == (Section(1, "C#", ""),)
