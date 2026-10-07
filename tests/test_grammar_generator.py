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
    validation artifacts" — on a valid and an invalid config alike. Structured
    input is affected too: JunosValidator builds StructuredValidator around the
    same SetValidator. JSON and YAML validation are unaffected; they do not use
    this grammar.
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


def _parses(root: SchemaNode, command: str) -> bool:
    """Generate a grammar from ``root`` and report whether ``command`` parses."""
    import lark

    parser = lark.Lark(generate_lark_grammar(root), parser="earley")
    try:
        parser.parse(command)
    except lark.exceptions.UnexpectedInput:
        return False
    return True


class TestNamedListKeysSurviveRuleMerging:
    """A named list must keep its key slot even when the name is reused.

    ``_collect_rules`` merges rules by name across the whole tree. It used to
    merge a list and a plain container under one rule, and the merged rule lost
    the entry-name slot: one non-list node named ``user`` stripped it from
    every ``user`` list, and every line addressing a list entry stopped
    parsing — ``interfaces ge-0/0/0``, ``system login user``,
    ``protocols bgp group``. List nodes now get their own rule.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        """``user`` as a named list under system/login, and a container under snmp."""
        return SchemaNode(
            name="configuration",
            children={
                "system": SchemaNode(
                    name="system",
                    children={
                        "login": SchemaNode(
                            name="login",
                            children={
                                "user": SchemaNode(
                                    name="user",
                                    is_list=True,
                                    children={"uid": SchemaNode(name="uid", is_leaf=True)},
                                )
                            },
                        )
                    },
                ),
                "snmp": SchemaNode(
                    name="snmp",
                    children={
                        "user": SchemaNode(
                            name="user",
                            children={"name": SchemaNode(name="name", is_leaf=True)},
                        )
                    },
                ),
            },
        )

    def test_unmerged_list_keeps_its_key(self) -> None:
        """Control: with no competing ``user``, the key slot is emitted."""
        tree = self._tree()
        del tree.children["snmp"]
        assert _parses(tree, "set system login user admin uid 2000")

    def test_merged_list_keeps_its_key(self) -> None:
        assert _parses(self._tree(), "set system login user admin uid 2000")


class TestTransparentListChildrenAreSpliced:
    """A nokeyword list child must contribute its own children to the parent.

    ``interfaces`` holds a nokeyword ``interface`` list, so a set command names
    no ``interface``: ``set interfaces ge-0/0/0 mtu 9192``. The generator used
    to emit the keyword anyway, leaving ``interfaces`` offering a bare
    ``VALUE`` with nothing allowed after the name. 24.4R0 has 534 nokeyword
    non-leaf nodes. The fix keys on ``nokeyword``, not on the ``transparent:``
    flag, which often names a child the node does not have.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        interface = SchemaNode(
            name="interface",
            is_list=True,
            children={"mtu": SchemaNode(name="mtu", is_leaf=True)},
        )
        interface.flags.add("nokeyword")
        interfaces = SchemaNode(name="interfaces", children={"interface": interface})
        interfaces.flags.add("transparent:interface")
        return SchemaNode(name="configuration", children={"interfaces": interfaces})

    def test_leaf_under_transparent_list_parses(self) -> None:
        assert _parses(self._tree(), "set interfaces ge-0/0/0 mtu 9192")


class TestContainerMayBeSetBare:
    """`set <path> <container>` is a complete command.

    A container is brought into being by naming it, with nothing under it:
    `set system services netconf ssh` names a container that also holds `port`
    and `connection-limit`. The generator used to require content after every
    container, which rejected the bare form.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        ssh = SchemaNode(
            name="ssh",
            children={"port": SchemaNode(name="port", is_leaf=True)},
        )
        return SchemaNode(
            name="configuration",
            children={"services": SchemaNode(name="services", children={"ssh": ssh})},
        )

    def test_bare_container(self) -> None:
        assert _parses(self._tree(), "set services ssh")

    def test_container_with_content(self) -> None:
        assert _parses(self._tree(), "set services ssh port 830")


class TestListEntryTakesSiblingsOnOneLine:
    """Several settings may follow one list entry name on a single line.

    `set system ntp server 198.51.100.1 version 4 prefer` is one command, so a
    named list repeats its alternatives rather than accepting just one.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        server = SchemaNode(
            name="server",
            is_list=True,
            children={
                "version": SchemaNode(name="version", is_leaf=True),
                "prefer": SchemaNode(name="prefer", is_presence=True),
            },
        )
        return SchemaNode(
            name="configuration",
            children={"ntp": SchemaNode(name="ntp", children={"server": server})},
        )

    def test_two_siblings_after_the_entry_name(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1 version 4 prefer")

    def test_entry_name_alone(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1")


class TestUnknownTokensInsideANamedList:
    """A named list holding a nokeyword leaf accepts unknown tokens.

    The grammar is structural: a nokeyword leaf becomes a bare ``VALUE``, and
    inside a named list's repetition that matches any run of tokens. So
    ``set interfaces ge-0/0/0 bogus-thing 5`` parses, because ``interface``
    holds the nokeyword leaf ``enable-disable``.

    This is the cost of the repetition that
    ``TestListEntryTakesSiblingsOnOneLine`` needs. Hoisting the bare value to a
    single optional slot closes most of it, but rejected two commands the
    project's own corpus treats as valid, so it is recorded rather than taken.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        bare = SchemaNode(name="enable-disable", is_leaf=True)
        bare.flags.add("nokeyword")
        iface = SchemaNode(
            name="interface",
            is_list=True,
            children={"mtu": SchemaNode(name="mtu", is_leaf=True), "enable-disable": bare},
        )
        iface.flags.add("nokeyword")
        return SchemaNode(
            name="configuration",
            children={"interfaces": SchemaNode(name="interfaces", children={"interface": iface})},
        )

    def test_known_element_still_parses(self) -> None:
        assert _parses(self._tree(), "set interfaces ge-0/0/0 mtu 9192")

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "a nokeyword leaf becomes a bare VALUE, and a named list's "
            "repetition lets it match any run of unknown tokens"
        ),
    )
    def test_unknown_element_is_rejected(self) -> None:
        assert not _parses(self._tree(), "set interfaces ge-0/0/0 bogus-thing 5")
