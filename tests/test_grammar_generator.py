"""Tests for Lark grammar generation from SchemaNode tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from junoscfg.display import find_artifact, read_artifact_text
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
        """A leaf takes QUOTED_OR_VALUE: any Junos value may be quoted."""
        grammar = generate_lark_grammar(_make_tree())
        assert '"host-name" QUOTED_OR_VALUE' in grammar

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
    point — Junos has an element `start`, so every bundled grammar since the 24.4
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
        # Only the exact name is reserved: `start-options`, the child of the
        # colliding element, keeps its own rule name.
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


def _bundled_dir() -> Path:
    import junoscfg.validate as validate_pkg

    return Path(validate_pkg.__file__).parent / "data"


class TestBundledGrammarCompiles:
    """The shipped grammar must be loadable, or set validation does nothing.

    It did not, from the 24.4 migration until the artefact was rebuilt: both
    `junoscfg -i set -v` and `-i structured -v` reported "Error loading
    validation artifacts" on a valid and an invalid config alike, because
    JunosValidator builds StructuredValidator around the same SetValidator.
    JSON and YAML validation never used this grammar.
    """

    def test_bundled_grammar_loads(self) -> None:
        import lark

        grammar = find_artifact(_bundled_dir(), "junos-set.lark")
        lark.Lark(read_artifact_text(grammar), start="start")


class TestBundledGrammarIsReproducible:
    """The shipped grammar is what the generator makes from the shipped tree.

    `ARCHITECTURE.md` section 8 forbids hand-editing a generated artefact, so
    there has to be a way to tell. The XSD dump the artefacts came from is not
    in the repository, so the grammar is rebuilt from `junos-structure-tree
    .json` instead — which produces, on a real 25.2R2 tree, a grammar differing
    from the XSD-built one in a single token. See `read_structure_tree`.

    To rebuild it::

        from junoscfg.validate.artifact_builder import read_structure_tree
        from junoscfg.validate.grammar_generator import write_lark_grammar

        root = read_structure_tree(".../data/junos-structure-tree.json")
        write_lark_grammar(root, ".../data/junos-set.lark")
    """

    def test_bundled_grammar_matches_its_structure_tree(self) -> None:
        from junoscfg.validate.artifact_builder import read_structure_tree

        data = _bundled_dir()
        rebuilt = generate_lark_grammar(
            read_structure_tree(find_artifact(data, "junos-structure-tree.json"))
        )
        shipped = read_artifact_text(find_artifact(data, "junos-set.lark"))
        assert rebuilt.strip() == shipped.strip()


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
    """A list marked oneliner may carry several keyworded siblings."""

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
        server.flags.add("oneliner")
        return SchemaNode(
            name="configuration",
            children={"ntp": SchemaNode(name="ntp", children={"server": server})},
        )

    def test_two_siblings_after_the_entry_name(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1 version 4 prefer")

    def test_unmarked_list_does_not_repeat_siblings(self) -> None:
        tree = self._tree()
        tree.children["ntp"].children["server"].flags.remove("oneliner")
        assert not _parses(tree, "set ntp server 198.51.100.1 version 4 prefer")

    def test_one_setting_after_the_entry_name(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1 version 4")

    def test_entry_name_alone(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1")


class TestFlatPositionalContainerTakesSiblingsOnOneLine:
    """A flat positional value is consumed once before keyworded siblings."""

    @staticmethod
    def _tree() -> SchemaNode:
        limit = SchemaNode(name="limit", is_leaf=True)
        limit.flags.update({"nokeyword", "positional-key-flat"})
        maximum_prefixes = SchemaNode(
            name="maximum-prefixes",
            children={
                "limit": limit,
                "threshold": SchemaNode(name="threshold", is_leaf=True),
                "log-interval": SchemaNode(name="log-interval", is_leaf=True),
            },
        )
        return SchemaNode(
            name="configuration",
            children={
                "routing-options": SchemaNode(
                    name="routing-options",
                    children={"maximum-prefixes": maximum_prefixes},
                )
            },
        )

    def test_two_siblings_after_the_positional_value(self) -> None:
        command = "set routing-options maximum-prefixes 3000000 threshold 50 log-interval 5"
        assert _parses(self._tree(), command)

    def test_unmarked_same_named_container_does_not_repeat_siblings(self) -> None:
        marked = self._tree().children["routing-options"].children["maximum-prefixes"]
        unmarked = SchemaNode(
            name="maximum-prefixes",
            children={"ordinary": SchemaNode(name="ordinary", is_leaf=True)},
        )
        root = SchemaNode(
            name="configuration",
            children={
                "alpha": SchemaNode(
                    name="alpha",
                    children={
                        "outer": SchemaNode(name="outer", children={"maximum-prefixes": marked})
                    },
                ),
                "beta": SchemaNode(
                    name="beta",
                    children={
                        "outer": SchemaNode(name="outer", children={"maximum-prefixes": unmarked})
                    },
                ),
            },
        )
        command = "set beta outer maximum-prefixes rogue threshold 50"
        assert not _parses(root, command)


class TestUnknownTokensInsideANamedList:
    """A named list holding a nokeyword leaf rejects unknown tokens.

    The grammar is structural: a nokeyword leaf becomes a bare ``VALUE``. While
    a named list repeated its alternatives that matched any run of tokens, so
    ``set interfaces ge-0/0/0 bogus-thing 5`` parsed, because ``interface``
    holds the nokeyword leaf ``enable-disable``.

    Closed by giving a named list one continuation rather than a repetition;
    see ``TestListEntryTakesSiblingsOnOneLine`` for what that cost.
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

    def test_unknown_element_is_rejected(self) -> None:
        assert not _parses(self._tree(), "set interfaces ge-0/0/0 bogus-thing 5")


class TestFreeformNokeywordKeepsItsKeyword:
    """`freeform-nk` carries `nokeyword` for validation, not for syntax.

    `_fix_freeform_nk_keys` sets it on `vlan-id` and `vlan-name`, which "have
    the nk flag for freeform validation but should be treated as normal
    keywords in conversion". Reading the bare `nokeyword` rejected
    `set interfaces ge-0/0/1 unit 0 vlan-id 100` — every VLAN-bearing config,
    and a line of `examples/router1.set`.
    """

    @staticmethod
    def _tree(freeform: bool) -> SchemaNode:
        vlan = SchemaNode(name="vlan-id", is_leaf=True)
        vlan.flags.add("nokeyword")
        if freeform:
            vlan.flags.add("freeform-nk")
        unit = SchemaNode(name="unit", is_list=True, children={"vlan-id": vlan})
        return SchemaNode(name="configuration", children={"unit": unit})

    def test_freeform_nk_leaf_takes_its_keyword(self) -> None:
        assert _parses(self._tree(freeform=True), "set unit 0 vlan-id 100")

    def test_plain_nokeyword_leaf_does_not(self) -> None:
        """Control: without the flag the keyword is suppressed, as before."""
        assert not _parses(self._tree(freeform=False), "set unit 0 vlan-id 100")
        assert _parses(self._tree(freeform=False), "set unit 0 100")


class TestAnyLeafValueMayBeQuoted:
    """Junos quotes any value holding a space, not a known list of fields.

    A real device configuration puts a nested `set` command inside
    `event-options policy <n> then change-configuration commands "..."`. The
    generator used to give `QUOTED_OR_VALUE` only to 13 hard-coded names, so
    every other quoted value was unparseable — `VALUE` is `/\\S+/`.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        return SchemaNode(
            name="configuration",
            children={
                "system": SchemaNode(
                    name="system",
                    children={"host-name": SchemaNode(name="host-name", is_leaf=True)},
                )
            },
        )

    def test_a_quoted_value_with_a_space_parses(self) -> None:
        assert _parses(self._tree(), 'set system host-name "a b"')

    def test_an_unquoted_value_still_parses(self) -> None:
        assert _parses(self._tree(), "set system host-name r1")


class TestPolicyExpressionIsOneValue:
    """`from policy (( A && ! B ) || ( ! C && D ))` is a single value.

    A device carries it as one opaque string --
    ``"policy": ["(( A && ! B ) || ( ! C && D ))"]`` -- and junoscfg converts
    it to exactly that, so conversion was already right. Only the grammar was
    wrong: ``VALUE`` is ``/\\S+/`` and stops at the first space, so 33 of the
    75 lines still rejected across three real devices were this one shape.

    Confirmed against the device's own ``| display json``, which is the only
    thing that could settle whether Junos keeps the expression opaque or
    structured.

    The expression alternative belongs to the slot, not to the grammar. It
    first went into ``QUOTED_OR_VALUE``, which the shipped grammar writes in
    11,853 places, so every value slot took a parenthesised run of anything --
    see ``TestExpressionsAreScopedToPolicyAlgebra``. The key is the XSD type
    reference ``policy-algebra``, carried on 7,636 nodes of the bundled
    structure tree and on none of the rest.
    """

    @staticmethod
    def _tree(*, typed: bool = True) -> SchemaNode:
        policy = SchemaNode(
            name="policy",
            is_leaf=True,
            type_ref="policy-algebra" if typed else "xsd:string",
        )
        term = SchemaNode(
            name="term",
            is_list=True,
            children={"from": SchemaNode(name="from", children={"policy": policy})},
        )
        statement = SchemaNode(name="policy-statement", is_list=True, children={"term": term})
        return SchemaNode(
            name="configuration",
            children={
                "policy-options": SchemaNode(
                    name="policy-options", children={"policy-statement": statement}
                )
            },
        )

    def test_an_expression_parses(self) -> None:
        assert _parses(
            self._tree(),
            "set policy-options policy-statement P term T from policy "
            "(( A && ! B ) || ( ! C && D ))",
        )

    def test_a_plain_name_still_parses(self) -> None:
        assert _parses(
            self._tree(), "set policy-options policy-statement P term T from policy PLAIN"
        )

    def test_the_same_leaf_untyped_rejects_the_expression(self) -> None:
        """Only the type reference opens the slot, not the element name."""
        assert not _parses(
            self._tree(typed=False),
            "set policy-options policy-statement P term T from policy "
            "(( A && ! B ) || ( ! C && D ))",
        )


class TestExpressionsAreScopedToPolicyAlgebra:
    """A parenthesised run is a value in 159 slots, not in all 11,853.

    ``EXPRESSION`` was added to ``QUOTED_OR_VALUE``, the terminal every value
    slot in the generated grammar writes. That made
    ``set system host-name (anything at all goes here)`` and
    ``set interfaces ge-0/0/0 description (not a policy expression)`` validate
    against the shipped grammar; a hostname holds neither a space nor a
    parenthesis. ``_value_token`` now hands ``ALGEBRA_OR_VALUE`` to the nodes
    whose ``type_ref`` is ``policy-algebra`` and ``QUOTED_OR_VALUE`` to the
    rest.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        return SchemaNode(
            name="configuration",
            children={
                "system": SchemaNode(
                    name="system",
                    children={
                        "host-name": SchemaNode(
                            name="host-name", is_leaf=True, type_ref="host-name-type"
                        ),
                    },
                ),
            },
        )

    def test_a_plain_leaf_rejects_a_parenthesised_run(self) -> None:
        assert not _parses(self._tree(), "set system host-name (foo bar)")

    def test_a_plain_leaf_still_takes_its_value(self) -> None:
        assert _parses(self._tree(), "set system host-name router1")

    def test_the_shared_terminal_no_longer_offers_expression(self) -> None:
        grammar = generate_lark_grammar(self._tree())
        assert "QUOTED_OR_VALUE: QUOTED | VALUE" in grammar
        assert "ALGEBRA_OR_VALUE: QUOTED | EXPRESSION | VALUE" in grammar


class TestFlattenedRenderingsTakeARunOfValues:
    """`flat-dict` and `flat-entry` mark where the tree is not the syntax.

    `trigger {"after": [null], "count": 1}` is written `trigger after 1`, and
    an `attributes-match` entry is written `<attribute> matches <regex>` with
    no key. The generator read neither flag, so every `attributes-match` line
    and `within <n> trigger after <n>` was rejected — 20 of the 42 lines still
    failing across three real devices.

    24.4R0 carries nine conversion-hint flags and the generator read four of
    them. `positional-key`, `positional-key-flat` and `transparent-list-key`
    are still unread; nothing in the corpora reaches them yet.
    """

    @staticmethod
    def _flat_dict_tree() -> SchemaNode:
        trigger = SchemaNode(
            name="trigger",
            children={
                "after": SchemaNode(name="after", is_presence=True),
                "count": SchemaNode(name="count", is_leaf=True),
            },
        )
        trigger.flags.add("flat-dict")
        within = SchemaNode(name="within", is_list=True, children={"trigger": trigger})
        return SchemaNode(name="configuration", children={"within": within})

    @staticmethod
    def _flat_entry_tree() -> SchemaNode:
        # Keyed by its three identifiers (identifier-key-fields), which
        # replaced the retired `flat-entry::values-only` flag.
        fields = ("from-event-attribute", "condition", "to-event-attribute-value")
        match = SchemaNode(
            name="attributes-match",
            is_list=True,
            children={
                name: SchemaNode(name=name, is_leaf=True, flags={"nokeyword"}) for name in fields
            },
            key_fields=fields,
        )
        match.flags.add("oneliner")
        policy = SchemaNode(name="policy", is_list=True, children={"attributes-match": match})
        return SchemaNode(name="configuration", children={"policy": policy})

    def test_a_flat_dict_takes_the_flattened_run(self) -> None:
        assert _parses(self._flat_dict_tree(), "set within 1800 trigger after 1")

    def test_a_flat_entry_takes_its_values(self) -> None:
        assert _parses(
            self._flat_entry_tree(),
            'set policy P attributes-match ping.test-owner matches "^uptime$"',
        )


class TestUniversalStatementsAreSplicedEverywhere:
    """`apply-groups` and its three siblings are valid at every level.

    No NETCONF XSD models them -- not as an element, not as a ref, in 21.4R0,
    23.2R2, 23.4R2 or 25.2R2 -- so `junoscfg` compensated in six modules, the
    set validator with three regexes that stripped the statement off the line
    before parsing it. The schema declares them once now, as root children
    flagged `universal`, and this generator emits one rule that every other
    rule references.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        groups = SchemaNode(name="apply-groups", is_leaf=True, is_list=True)
        groups.flags.add("universal")
        unit = SchemaNode(
            name="unit",
            is_list=True,
            children={"mtu": SchemaNode(name="mtu", is_leaf=True)},
        )
        interfaces = SchemaNode(name="interfaces", children={"unit": unit})
        return SchemaNode(
            name="configuration",
            children={"interfaces": interfaces, "apply-groups": groups},
        )

    def test_one_rule_holds_them(self) -> None:
        grammar = generate_lark_grammar(self._tree())
        assert 'universal_statement: "apply-groups" QUOTED_OR_VALUE' in grammar

    def test_a_nested_container_takes_one(self) -> None:
        assert _parses(self._tree(), "set interfaces apply-groups foo")

    def test_a_list_entry_takes_one(self) -> None:
        assert _parses(self._tree(), "set interfaces unit 0 apply-groups foo")

    def test_the_top_level_takes_one(self) -> None:
        assert _parses(self._tree(), "set apply-groups foo")

    def test_an_ordinary_root_child_is_not_spliced(self) -> None:
        """Only the `universal` flag opens the splice, not being a root child."""
        assert not _parses(self._tree(), "set interfaces interfaces")


class TestTheBundledTreeCarriesTheApplyStatements:
    """The shipped artifacts are what `_fix_apply_statements` produces.

    Until 0.8.0 the bundled tree predated the fix, and a substitute test
    applied it to the tree in memory to prove the grammar it would produce.
    The 25.2R2 artifacts carry the four nodes, so the proof is the artifact
    itself: the nodes are there with their flag, the fix has nothing left to
    add, and the shipped grammar takes and rejects what the substitute pinned.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        from junoscfg.validate.artifact_builder import read_structure_tree

        return read_structure_tree(find_artifact(_bundled_dir(), "junos-structure-tree.json"))

    def test_the_four_nodes_carry_the_flag(self) -> None:
        tree = self._tree()
        for name in ("apply-groups", "apply-groups-except", "apply-flags", "apply-macro"):
            assert "universal" in tree.children[name].flags, name

    def test_the_fix_has_nothing_left_to_add(self) -> None:
        from junoscfg.validate.xsd_fixes import ALL_FIXES

        fix = next(f for f in ALL_FIXES if f.id == "apply-statements")
        assert not fix.apply(self._tree())

    def test_the_shipped_grammar_takes_them(self, bundled_set_validator) -> None:
        for command in (
            "set apply-groups global-vxlan",
            "set protocols bgp group G apply-groups foo",
            "set interfaces ge-0/0/0 unit 0 apply-groups foo",
            "set protocols bgp group overlay apply-flags replace",
            "set interfaces ge-0/0/0 apply-groups-except bar",
            "set policy-options policy-statement p1 apply-macro m1 key1 val1",
            'set interfaces ge-0/0/0 description "uplink to apply-groups foo"',
        ):
            bundled_set_validator._parser.parse(command)  # noqa: SLF001

    def test_the_shipped_grammar_still_rejects_what_it_should(self, bundled_set_validator) -> None:
        """The splice is four names, not a hole."""
        import lark

        for command in (
            "set system host-name (foo bar)",
            "set interfaces ge-0/0/0 bogus-thing 5",
            "set system host-name",
            "set system apply-nonsense foo",
        ):
            with pytest.raises(lark.exceptions.UnexpectedInput):
                bundled_set_validator._parser.parse(command)  # noqa: SLF001


# ── identifier-key-fields: a keyed entry takes exactly its key values ──
#
# Spec: openspec/changes/identifier-key-fields/specs/validation/
# set-command-validation. The grammar is generated by `ArtifactBuilder` from
# a synthetic XSD shaped like the dump's types, and lines go through the
# public `validate_set`, so the tests hold however the generator is written.

_PS = "set policy-options policy-statement SAMPLE-POLICY"
_T1 = f"{_PS} term T1"
_EVENT = "set event-options policy SAMPLE-EVENT-POLICY attributes-match"


@pytest.fixture(scope="module")
def keyed_artifacts(tmp_path_factory: pytest.TempPathFactory) -> Path:
    from tests.keyed_entries import KEYED_XSD, build_artifacts

    return build_artifacts(KEYED_XSD, tmp_path_factory.mktemp("keyed"))


@pytest.fixture(scope="module")
def keyed_parser(keyed_artifacts: Path):
    import lark

    text = read_artifact_text(find_artifact(keyed_artifacts, "junos-set.lark"))
    return lark.Lark(text, start="start", parser="earley")


def _valid(parser, line: str) -> bool:
    import lark

    try:
        parser.parse(line)
    except lark.exceptions.UnexpectedInput:
        return False
    return True


class TestKeyedEntryTakesExactlyItsKeys:
    def test_two_keys_are_taken_in_order(self, keyed_parser, keyed_artifacts: Path) -> None:
        from junoscfg import validate_set

        lines = [
            f"{_T1} from as-path-neighbors as-list SAMPLE-AS-LIST",
            f"{_T1} from as-path-origins as-list-group SAMPLE-AS-LIST-GROUP",
            f"{_PS} from as-path-neighbors as-list SAMPLE-AS-LIST",
            f"{_T1} from as-path-neighbors as-list as-list",
            f'{_T1} from as-path-neighbors as-list "SAMPLE AS LIST"',
            f"{_T1} from route-filter 198.51.100.0/24 exact",
            f"{_T1} from route-filter 198.51.100.0/24 orlonger accept",
            f'{_EVENT} ping.test-owner matches "^uptime$"',
            f'{_EVENT} ping.test-owner matches "^up time$"',
            "set system ntp server 198.51.100.10 version 4 prefer",
        ]
        for line in lines:
            assert _valid(keyed_parser, line), line
        result = validate_set("\n".join(lines), artifacts_dir=str(keyed_artifacts))
        assert result.valid, result.errors

    @pytest.mark.parametrize(
        "line",
        [
            f"{_T1} from as-path-neighbors",
            f"{_T1} from as-path-neighbors as-list",
            f"{_T1} from as-path-neighbors SAMPLE-AS-LIST",
            f"{_T1} from as-path-neighbors as-list SAMPLE-AS-LIST SAMPLE-EXTRA",
            f"{_T1} from route-filter 198.51.100.0/24",
            f"{_T1} from route-filter 198.51.100.0/24 accept",
            f"{_T1} from route-filter 198.51.100.0/24 exact SAMPLE-EXTRA",
            f"{_T1} then community add",
            f"{_T1} then community add SAMPLE-COMM SAMPLE-EXTRA",
            f"{_EVENT} ping.test-owner matches",
            f'{_EVENT} ping.test-owner matches "^uptime$" SAMPLE-EXTRA',
        ],
    )
    def test_a_missing_or_further_value_is_rejected(
        self, keyed_parser, keyed_artifacts: Path, line: str
    ) -> None:
        from junoscfg import validate_set

        assert not _valid(keyed_parser, line)
        assert not validate_set(line, artifacts_dir=str(keyed_artifacts)).valid

    def test_a_key_name_is_not_a_keyword(self, keyed_parser, keyed_artifacts: Path) -> None:
        for line in (
            f"{_T1} from as-path-neighbors list-type as-list list-name SAMPLE-AS-LIST",
            f"{_T1} from as-path-neighbors as-list list-name SAMPLE-AS-LIST",
            f"{_T1} from route-filter address 198.51.100.0/24 exact",
            f"{_T1} then community add community-name SAMPLE-COMM",
            f"{_EVENT} from-event-attribute ping.test-owner condition matches "
            'to-event-attribute-value "^uptime$"',
            "set system ntp server address 198.51.100.10",
        ):
            assert not _valid(keyed_parser, line), line
        grammar = read_artifact_text(find_artifact(keyed_artifacts, "junos-set.lark"))
        for key in (
            '"list-type"',
            '"list-name"',
            '"address"',
            '"community-name"',
            '"from-event-attribute"',
            '"to-event-attribute-value"',
        ):
            assert key not in grammar, key

    def test_a_key_keyword_goes_either_side(self, keyed_parser) -> None:
        """A key given by its keyword stands before or after the positional
        values, whatever the declared order; children that are not keys come
        only after them (device probe rounds 3 and 4, vMX 23.2R2-S7.5)."""
        for line in (
            f"{_T1} then community add SAMPLE-COMM",
            f"{_T1} then community SAMPLE-COMM add",
            f"{_T1} then community delete SAMPLE-COMM",
            f"{_T1} then community SAMPLE-COMM delete",
            f"{_T1} from route-filter 198.51.100.0/24 exact",
            f"{_T1} from route-filter exact 198.51.100.0/24",
            f"{_T1} from route-filter exact 198.51.100.0/24 accept",
        ):
            assert _valid(keyed_parser, line), line
        for line in (
            f"{_T1} then community add SAMPLE-COMM delete",
            f"{_T1} then community add delete SAMPLE-COMM",
            # An action before the keys (not probed; consistent with `flag`).
            f"{_T1} from route-filter accept 198.51.100.0/24 exact",
        ):
            assert not _valid(keyed_parser, line), line

    def test_an_unknown_sibling_after_two_keys_is_rejected(self, keyed_parser) -> None:
        assert _valid(keyed_parser, f"{_T1} from route-filter 198.51.100.0/24 exact accept")
        for line in (
            f"{_T1} from as-path-neighbors as-list SAMPLE-AS-LIST bogus-thing 5",
            f"{_T1} from route-filter 198.51.100.0/24 exact bogus-thing 5",
            f'{_EVENT} ping.test-owner matches "^uptime$" bogus-thing 5',
        ):
            assert not _valid(keyed_parser, line), line

    def test_a_numeric_list_type_is_rejected(self, keyed_parser, keyed_artifacts: Path) -> None:
        """A key value takes its own leaf's type: `list-type`'s enum, though the
        XSD's union also names `xsd:unsignedLong`. The device rejected
        `as-path-neighbors 1 ...` at `set` (round-1 probe, vMX 23.2R2-S7.5).
        Owner answer 8."""
        from junoscfg import validate_set

        line = f"{_T1} from as-path-neighbors 1 SAMPLE-AS-LIST"
        assert not _valid(keyed_parser, line)
        assert not validate_set(line, artifacts_dir=str(keyed_artifacts)).valid

    def test_name_keyed_grammar_is_byte_identical(self, tmp_path: Path) -> None:
        """What 0.14.0 generated for `name`-keyed lists, to the byte.

        Two lines differ by owner decision: `data__list` (phase 5) and
        `universal_statement`, where `apply-macro` takes one to three values,
        as the device does (phase-6 fix pass, device probe, vMX 23.2R2-S7.5).
        """
        from tests.keyed_entries import NAME_KEYED_XSD, build_artifacts

        directory = build_artifacts(NAME_KEYED_XSD, tmp_path)
        grammar = read_artifact_text(find_artifact(directory, "junos-set.lark"))
        pinned = Path(__file__).resolve().parent / "data" / "name-keyed.lark"
        # The generator ends with a blank line; the file keeps one newline,
        # as the end-of-file hook wants, so the comparison adds the other.
        assert grammar == pinned.read_text(encoding="utf-8") + "\n"
