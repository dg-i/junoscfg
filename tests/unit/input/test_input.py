"""Tests for input normalization."""

from __future__ import annotations

import datetime

import pytest

from junoscfg.input import find_non_json_value, normalize


class TestRemoveComments:
    def test_removes_hash_comment_lines(self) -> None:
        text = "# a comment\nset system host-name foo"
        assert "set system host-name foo" in normalize(text)
        assert "# a comment" not in normalize(text)

    def test_removes_block_comments(self) -> None:
        text = "/* a comment */\nset system host-name foo"
        result = normalize(text)
        assert "set system host-name foo" in result
        assert "a comment" not in result

    def test_removes_multiline_block_comments(self) -> None:
        text = "/*\n * a comment\n */\nset system host-name foo"
        result = normalize(text)
        assert "set system host-name foo" in result

    def test_preserves_inline_content(self) -> None:
        text = "set system host-name foo  /* a comment */\nset system domain-name bar  # a comment"
        result = normalize(text)
        assert "set system host-name foo" in result


class TestCarriageReturn:
    def test_normalizes_crlf(self) -> None:
        text = "set foo\r\nset bar"
        result = normalize(text)
        assert "\r" not in result
        assert "set foo" in result
        assert "set bar" in result

    def test_normalizes_cr(self) -> None:
        text = "set foo\rset bar"
        result = normalize(text)
        assert "\r" not in result


class TestSquareBrackets:
    def test_joins_split_brackets(self) -> None:
        text = "set apply-groups [\nfoo\nbar\n];"
        result = normalize(text)
        assert "set apply-groups [ foo bar ];" in result

    def test_preserves_single_line_brackets(self) -> None:
        text = "set apply-groups [ foo bar ];"
        result = normalize(text)
        assert "set apply-groups [ foo bar ];" in result

    def test_unbalanced_open_bracket_raises(self) -> None:
        text = "set foo [\nbar"
        with pytest.raises(ValueError, match="Unclosed bracket"):
            normalize(text)

    def test_brackets_inside_quotes_ignored(self) -> None:
        """Brackets inside quoted strings don't count as bracket nesting."""
        text = 'set community members "64498:[2-6]....$"'
        result = normalize(text)
        assert 'set community members "64498:[2-6]....$"' in result

    def test_empty_input_returns_empty(self) -> None:
        assert normalize("") == ""


_SHARED: dict = {"k": "v"}
_CYCLE: dict = {}
_CYCLE["a"] = _CYCLE


class TestFindNonJsonValue:
    """The boundary yaml-new conversion and validation share (spec conversion/junos-json-yaml)."""

    def test_a_json_document_has_none(self) -> None:
        document = {"configuration": {"a": [None, True, 1, 2.5, "x", {"b": []}]}}
        assert find_non_json_value(document) is None

    @pytest.mark.parametrize(
        ("document", "found"),
        [
            ({"a": [1, {"b": datetime.date(2026, 10, 15)}]}, ("date", "a.1.b")),
            ({"a": {True: "x"}}, ("bool key", "a")),
            ({None: "x"}, ("null key", "")),
            ({"a": (1, 2)}, ("tuple", "a")),
            (b"acme", ("bytes", "")),
            ({"a": _SHARED, "b": [_SHARED]}, ("alias", "b.0")),
            (_CYCLE, ("alias", "a")),
        ],
        ids=[
            "date-in-a-list",
            "bool-key",
            "null-key-at-the-top",
            "tuple",
            "the-document",
            "shared",
            "cycle",
        ],
    )
    def test_the_first_value_json_cannot_hold(self, document: object, found: tuple) -> None:
        assert find_non_json_value(document) == found
