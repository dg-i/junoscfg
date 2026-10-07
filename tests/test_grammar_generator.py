"""Tests for Lark grammar generation from SchemaNode tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from junoscfg.validate.grammar_generator import generate_lark_grammar
from junoscfg.validate.schema_node import Combinator, SchemaNode


def _make_tree() -> SchemaNode:
    """Build a test tree."""
    return SchemaNode(
        name="configuration",
        children={
            "system": SchemaNode(
                name="system",
                children={
                    "host-name": SchemaNode(name="host-name", is_leaf=True),
                    "no-remote-trace": SchemaNode(name="no-remote-trace", is_presence=True),
                },
            ),
            "interfaces": SchemaNode(
                name="interfaces",
                children={
                    "description": SchemaNode(name="description", is_leaf=True),
                },
            ),
        },
    )


class TestGenerateLarkGrammar:
    def test_has_start_rule(self):
        grammar = generate_lark_grammar(_make_tree())
        assert "start: SET configuration" in grammar

    def test_has_set_terminal(self):
        grammar = generate_lark_grammar(_make_tree())
        assert 'SET: "set"' in grammar

    def test_leaf_uses_value(self):
        grammar = generate_lark_grammar(_make_tree())
        assert '"host-name" VALUE' in grammar

    def test_presence_is_bare_keyword(self):
        grammar = generate_lark_grammar(_make_tree())
        assert '"no-remote-trace"' in grammar

    def test_quoted_fields(self):
        grammar = generate_lark_grammar(_make_tree())
        assert '"description" QUOTED_OR_VALUE' in grammar

    def test_container_generates_rule(self):
        grammar = generate_lark_grammar(_make_tree())
        assert "system:" in grammar
        assert "configuration:" in grammar

    def test_whitespace_import(self):
        grammar = generate_lark_grammar(_make_tree())
        assert "%import common.WS" in grammar
        assert "%ignore WS" in grammar


class TestSafeRuleNames:
    def test_hyphenated_names(self):
        root = SchemaNode(
            name="configuration",
            children={
                "my-element": SchemaNode(
                    name="my-element",
                    children={
                        "sub-item": SchemaNode(name="sub-item", is_leaf=True),
                    },
                ),
            },
        )
        grammar = generate_lark_grammar(root)
        assert "my_element:" in grammar

    def test_numeric_prefix(self):
        root = SchemaNode(
            name="configuration",
            children={
                "802.3ad": SchemaNode(name="802.3ad", is_leaf=True),
            },
        )
        grammar = generate_lark_grammar(root)
        # Should not start with a digit
        assert '"802.3ad"' in grammar


class TestCombinators:
    def test_choice_uses_pipe(self):
        root = SchemaNode(
            name="configuration",
            children={
                "a": SchemaNode(name="a", is_leaf=True),
                "b": SchemaNode(name="b", is_leaf=True),
            },
            combinator=Combinator.CHOICE,
        )
        grammar = generate_lark_grammar(root)
        assert "|" in grammar

    def test_sequence_uses_star(self):
        """Merged rules use (...)*  for all combinators (seq_choice semantics)."""
        root = SchemaNode(
            name="configuration",
            children={
                "a": SchemaNode(name="a", is_leaf=True),
                "b": SchemaNode(name="b", is_leaf=True),
            },
            combinator=Combinator.SEQUENCE,
        )
        grammar = generate_lark_grammar(root)
        assert "*" in grammar

    def test_seq_choice_uses_star(self):
        root = SchemaNode(
            name="configuration",
            children={
                "a": SchemaNode(name="a", is_leaf=True),
                "b": SchemaNode(name="b", is_leaf=True),
            },
            combinator=Combinator.SEQ_CHOICE,
        )
        grammar = generate_lark_grammar(root)
        assert "*" in grammar


class TestRuleNamesAreValidLark:
    """Rule names Lark will actually accept.

    Two defects shipped here. A name containing an uppercase letter is read by
    Lark as a *terminal*, and Junos has elements like
    `jnx-tel-RE-local-interfaces-stats`. And a schema element named `start`
    emitted a second `start:` rule, colliding with the grammar's own entry
    point — Junos has `start-options`, so every bundled grammar since the 24.4
    migration has been invalid.
    """

    def test_names_are_lowercased(self) -> None:
        from junoscfg.validate.grammar_generator import _safe_rule_name

        assert _safe_rule_name("jnx-tel-RE-local-interfaces-stats") == (
            "jnx_tel_re_local_interfaces_stats"
        )
        assert _safe_rule_name("MixedCase") == "mixedcase"

    def test_start_does_not_collide_with_the_entry_rule(self) -> None:
        from junoscfg.validate.grammar_generator import _safe_rule_name

        assert _safe_rule_name("start") == "start_element"
        assert _safe_rule_name("start-options") == "start_options"

    def test_every_generated_name_matches_larks_rule_pattern(self) -> None:
        import re as _re

        from junoscfg.validate.grammar_generator import _safe_rule_name

        pattern = _re.compile(r"_?[a-z][_a-z0-9]*\Z")
        for name in (
            "start",
            "ge-0/0/0",
            "802.3ad",
            "jnx-tel-RE-local",
            "ieee-802.3ad",
            "A",
            "",
        ):
            assert pattern.match(_safe_rule_name(name)), name


class TestBundledGrammarCompiles:
    """The shipped grammar must be loadable, or set validation does nothing.

    While it does not compile, `junoscfg -i set -v` reports "Error loading
    validation artifacts" and exits 0 — on a valid and an invalid config
    alike. JSON, YAML and structured validation are unaffected; they do not
    use this grammar.
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "the bundled grammar predates the _safe_rule_name fix and has two "
            "`start:` rules; regenerate the artifacts from a device dump to "
            "clear this, then delete the xfail"
        ),
    )
    def test_bundled_grammar_loads(self) -> None:
        import lark

        import junoscfg.validate as validate_pkg

        grammar = Path(validate_pkg.__file__).parent / "data" / "junos-set.lark"
        lark.Lark(grammar.read_text(encoding="utf-8"), start="start")
