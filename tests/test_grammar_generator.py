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

        grammar = _bundled_dir() / "junos-set.lark"
        lark.Lark(grammar.read_text(encoding="utf-8"), start="start")


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
        rebuilt = generate_lark_grammar(read_structure_tree(data / "junos-structure-tree.json"))
        shipped = (data / "junos-set.lark").read_text(encoding="utf-8")
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
    """A list entry name may be followed by one setting, not several.

    `set system ntp server 198.51.100.1 version 4 prefer` is a valid command
    this grammar rejects. Accepting it needs `(alts)*` where the rule has
    `(alts)?`, and that repetition makes the grammar ambiguous enough to cost
    228 ms a line against 4 ms: a 5,000-line configuration would take 19
    minutes to validate instead of 18 seconds. Rejecting a few valid lines
    beats a validator nobody can run on a real config.

    The repetition also let a bare `VALUE` absorb any run of unknown tokens,
    which is why `TestUnknownTokensInsideANamedList` passes now.

    Measured on the bundled 24.4R0 tree at 61, 244 and 976 lines. Lark's
    `~0..n` range is not a middle way: it expands combinatorially and does not
    finish compiling.
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

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "one continuation per list entry: the repetition that would accept "
            "this costs 228 ms a line against 4 ms"
        ),
    )
    def test_two_siblings_after_the_entry_name(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1 version 4 prefer")

    def test_one_setting_after_the_entry_name(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1 version 4")

    def test_entry_name_alone(self) -> None:
        assert _parses(self._tree(), "set ntp server 198.51.100.1")


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
        match = SchemaNode(name="attributes-match", is_presence=True, is_list=True)
        match.flags.update({"oneliner", "flat-entry::values-only"})
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


class TestTheApplyFixReachesARealGrammar:
    """End to end on the bundled tree, without shipping the result.

    `_fix_apply_statements` lives in `xsd_fixes.py`, which is where a schema
    correction belongs, and it reaches a user only through regenerated
    artifacts. The bundled ones are 24.4R0 from a dump that is not in this
    repository, and the 23.2R2-S7.5 dump that is to hand regresses Juniper's
    Validated Designs corpus from 217 field warnings to 3,254 -- over the
    budget `tests/test_jvd_corpus.py` enforces -- so nothing was regenerated.

    Mutating `junos-structure-tree.json` to ship it anyway was considered and
    rejected: `ARCHITECTURE.md` section 8 forbids hand-editing a generated
    artefact, and a tree carrying nodes no XSD run produced would make the
    shipped grammar and the shipped JSON schemas disagree about the same four
    statements. This test is the substitute: it proves the fix produces the
    grammar it claims to, on the real 427,978-node tree, so the next
    regeneration ships a known quantity.
    """

    @staticmethod
    def _fixed_tree() -> SchemaNode:
        from junoscfg.validate.artifact_builder import read_structure_tree
        from junoscfg.validate.xsd_fixes import ALL_FIXES

        tree = read_structure_tree(_bundled_dir() / "junos-structure-tree.json")
        fix = next(f for f in ALL_FIXES if f.id == "apply-statements")
        assert fix.apply(tree), "the bundled tree already carries them; retire the stripper"
        return tree

    def test_the_bundled_tree_does_not_carry_them_yet(self) -> None:
        from junoscfg.validate.artifact_builder import read_structure_tree

        tree = read_structure_tree(_bundled_dir() / "junos-structure-tree.json")
        assert "apply-groups" not in tree.children

    def test_the_fixed_tree_builds_a_grammar_that_takes_them(self) -> None:
        import lark

        grammar = generate_lark_grammar(self._fixed_tree())
        assert "universal_statement:" in grammar
        parser = lark.Lark(grammar, parser="earley")
        for command in (
            "set apply-groups global-vxlan",
            "set protocols bgp group G apply-groups foo",
            "set interfaces ge-0/0/0 unit 0 apply-groups foo",
            "set protocols bgp group overlay apply-flags replace",
            "set interfaces ge-0/0/0 apply-groups-except bar",
            "set policy-options policy-statement p1 apply-macro m1 key1 val1",
            'set interfaces ge-0/0/0 description "uplink to apply-groups foo"',
        ):
            parser.parse(command)

    def test_the_fixed_grammar_still_rejects_what_it_should(self) -> None:
        """The splice is four names, not a hole."""
        import lark

        parser = lark.Lark(generate_lark_grammar(self._fixed_tree()), parser="earley")
        for command in (
            "set system host-name (foo bar)",
            "set interfaces ge-0/0/0 bogus-thing 5",
            "set system host-name",
            "set system apply-nonsense foo",
        ):
            with pytest.raises(lark.exceptions.UnexpectedInput):
                parser.parse(command)
