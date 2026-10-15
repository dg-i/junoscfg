"""Tests for input normalization."""

from __future__ import annotations

import datetime

import pytest
import yaml

from junoscfg.input import find_non_json_value, normalize
from tests.support.aliases import CYCLE, SHARED_BLOCK, alias_bomb, alias_bomb_yaml


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
_LIST: list = ["v", {"k": "v"}]
_CYCLE: dict = {}
_CYCLE["a"] = _CYCLE
_LIST_CYCLE: list = []
_LIST_CYCLE.append({"x": _LIST_CYCLE})


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
        ],
        ids=[
            "date-in-a-list",
            "bool-key",
            "null-key-at-the-top",
            "tuple",
            "the-document",
        ],
    )
    def test_the_first_value_json_cannot_hold(self, document: object, found: tuple) -> None:
        assert tuple(find_non_json_value(document) or ())[:2] == found

    @pytest.mark.parametrize(
        "document",
        [
            {"a": _SHARED, "b": [_SHARED]},
            yaml.safe_load(SHARED_BLOCK),
            {"a": _SHARED, "b": {"c": _SHARED}, "d": [_LIST, _LIST]},
        ],
        ids=["shared-twice", "a-yaml-anchor", "two-blocks-at-two-depths"],
    )
    def test_a_shared_block_is_walked_where_it_is_reached(self, document: object) -> None:
        """JSON has no aliases: a mapping or list reached again stands for a copy
        of itself, which JSON holds (owner ruling on PO-2/SC-1). Every document
        reaching each value at most twice passes the bound."""
        assert find_non_json_value(document) is None

    def test_a_value_in_a_shared_block_is_found_where_first_reached(self) -> None:
        block = {"d": datetime.date(2026, 10, 15)}
        assert tuple(find_non_json_value({"a": block, "b": block}))[:2] == ("date", "a.d")

    @pytest.mark.parametrize(
        ("document", "path"),
        [(_CYCLE, "a"), (_LIST_CYCLE, "0.x"), (yaml.safe_load(CYCLE), "configuration.system.x")],
        ids=["a-mapping", "through-a-list", "a-yaml-anchor"],
    )
    def test_a_cycle_is_refused_where_it_is_reached_again(
        self, document: object, path: str
    ) -> None:
        found = find_non_json_value(document)
        assert found is not None
        assert (found.kind, found.path, found.reason) == ("cycle", path, "has no JSON spelling")

    @pytest.mark.parametrize(
        "document",
        [yaml.safe_load(alias_bomb_yaml()), alias_bomb(), yaml.safe_load(alias_bomb_yaml(200, 2))],
        ids=["billion-laughs", "two-to-the-64", "two-to-the-200"],
    )
    def test_an_alias_bomb_is_refused_in_linear_time(self, document: object) -> None:
        """The walk stops within twice the parsed document: it returns at all
        (an unbounded walk of 2**200 values never would), naming the alias."""
        found = find_non_json_value(document)
        assert found is not None
        assert found.kind == "alias"
        assert found.reason == "expands the document past twice its size"
        assert found.path

    def test_the_bound_is_twice_the_parsed_document(self) -> None:
        """Parsed: the root, the block and its scalar, one more scalar: 4 values.
        Reaching the 2-value block three times writes out 1 + 6 + 1 = 8 values,
        twice the parsed 4, and passes; a fourth reach writes out 10 and is
        refused at its place."""
        block = {"k": "v"}
        at_the_bound = {"a": block, "b": block, "c": "x", "d": block}
        assert find_non_json_value(at_the_bound) is None
        found = find_non_json_value({**at_the_bound, "e": block})
        assert found is not None
        assert (found.kind, found.path) == ("alias", "e")
