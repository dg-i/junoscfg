"""Tests for input normalization."""

from __future__ import annotations

import datetime

import pytest
import yaml

from junoscfg.input import find_non_json_value, normalize
from tests.support.aliases import (
    ANCHORED_BESIDE,
    CYCLE,
    NESTED_ONCE,
    SHARED_BLOCK,
    alias_bomb_yaml,
    alias_chain_yaml,
    hosts_sharing_contents,
    nested_ir,
    nested_yaml,
)

_TOO_DEEP = "is nested deeper than 64 levels"


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
            {"a": _SHARED, "b": [_SHARED], "c": {"d": {"e": "f"}}},
            yaml.safe_load(SHARED_BLOCK),
            {"a": _SHARED, "b": {"c": _SHARED}, "d": [_LIST, _LIST]},
            yaml.safe_load(
                "configuration:\n  system:\n    d: &d {services: {ssh: [null]}}\n"
                "    e:\n      <<: *d\n      x: 1\n"
            ),
        ],
        ids=["shared-twice", "a-yaml-anchor", "two-blocks-at-two-depths", "a-merge-key"],
    )
    def test_a_shared_block_is_walked_where_it_is_reached(self, document: object) -> None:
        """JSON has no aliases: a mapping or list reached again stands for a copy
        of itself, which JSON holds (owner ruling on PO-2/SC-1)."""
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
        "source",
        [
            ANCHORED_BESIDE,
            NESTED_ONCE,
            hosts_sharing_contents(11),
            "configuration:\n  h: &h {name: a, contents: &c [x, y, z]}\n  i: *h\n  j: *c\n",
            "configuration: {a: &x [1], b: *x, c: *x, e: *x, f: *x, system: {host-name: r1}}",
            alias_bomb_yaml(5, 4),
            alias_bomb_yaml(6, 10),
        ],
        ids=[
            "anchored-beside-the-configuration",
            "nested-anchors",
            "eleven-hosts",
            "a-block-reached-three-times",
            "one-block-five-times",
            "four-to-the-fifth",
            "ten-to-the-sixth",
        ],
    )
    def test_a_block_reused_any_number_of_times_is_walked_written_out(self, source: str) -> None:
        """No size bound and no parsed-depth bound: junoscfg assumes its YAML
        input is not hostile, so a block is expanded however often and wherever
        it is reused (owner rulings 2026-10-15 on SC-2, SC-A, SC-C). Each row
        was refused by one of the old bounds."""
        assert find_non_json_value(yaml.safe_load(source)) is None

    @pytest.mark.parametrize(
        "document",
        [
            yaml.safe_load(nested_yaml(61)),
            {"configuration": nested_ir(63)},
            nested_ir(63, [None]),
            yaml.safe_load(alias_chain_yaml(3, 20)),
        ],
        ids=["lists", "mappings", "a-flag-at-64", "an-alias-chain-to-61"],
    )
    def test_a_document_64_levels_deep_passes(self, document: object) -> None:
        """A value 64 path steps below the root is the deepest accepted; the
        list holding the flag's `null` is the 64th step (owner ruling on SC-A)."""
        assert find_non_json_value(document) is None

    @pytest.mark.parametrize(
        ("document", "path"),
        [
            (yaml.safe_load(nested_yaml(62)), "configuration.system.x" + ".0" * 62),
            ({"configuration": nested_ir(64)}, "configuration" + ".a" * 64),
            (nested_ir(64, [None]), "a" + ".a" * 63 + ".0"),
            (yaml.safe_load(alias_chain_yaml()), "s3" + ".0" * 64),
            (yaml.safe_load(nested_yaml(400)), "configuration.system.x" + ".0" * 62),
            (nested_ir(5000), "a" + ".a" * 64),
            ({"a": [1, {"b": nested_ir(70, datetime.date(2026, 10, 15))}]}, "a.1.b" + ".a" * 62),
        ],
        ids=[
            "lists",
            "mappings",
            "a-flag-at-65",
            "an-alias-chain",
            "four-hundred-deep",
            "five-thousand-deep",
            "before-a-value-json-cannot-hold",
        ],
    )
    def test_a_value_past_64_levels_is_refused_at_its_path(
        self, document: object, path: str
    ) -> None:
        """The first value more than 64 path steps below the root is refused at
        its own path, kind `value`, never a `RecursionError`, however deep the
        document goes (owner ruling on SC-A): junoscfg's own recursive stages
        then never meet more than 65 levels."""
        found = find_non_json_value(document)
        assert found is not None
        assert (found.kind, found.path, found.reason) == ("value", path, _TOO_DEEP)
        assert len(found.path.split(".")) == 65

    def test_a_cycle_closing_at_step_65_is_a_cycle(self) -> None:
        """The cycle test comes first: a mapping 64 steps deep that holds itself
        is a cycle where it is reached again, not a value too deep."""
        loop: dict = {}
        loop["x"] = loop
        found = find_non_json_value(nested_ir(64, loop))
        assert found is not None
        assert (found.kind, found.path) == ("cycle", "a" + ".a" * 63 + ".x")

    @pytest.mark.parametrize(
        ("document", "found"),
        [
            ({"a": [1, {"b": datetime.date(2026, 10, 15)}], 1: (2, b"x")}, None),
            (yaml.safe_load(CYCLE), ("cycle", "configuration.system.x")),
            (
                {1: datetime.date(2026, 10, 15), "x": nested_ir(65)},
                ("value", "x" + ".a" * 64),
            ),
        ],
        ids=["yaml-scalars-and-keys", "a-cycle", "too-deep"],
    )
    def test_without_scalars_only_a_cycle_or_depth_is_refused(
        self, document: object, found: tuple | None
    ) -> None:
        """The `yaml` reader's IR holds dates and other YAML scalars: with
        `scalars=False` only what junoscfg's own recursion cannot walk is refused
        (owner ruling on C5)."""
        result = find_non_json_value(document, scalars=False)
        assert (tuple(result)[:2] if result else None) == found
