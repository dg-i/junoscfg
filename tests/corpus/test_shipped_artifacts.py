"""What the shipped artifacts accept and reject, and that they are what they claim.

Every other test of the grammar runs on a minimal or a synthetic one, and that
is how a defect in the real one shipped: a global `EXPRESSION` terminal went
into `QUOTED_OR_VALUE`, which the generated grammar writes in 11,853 value
slots, so every slot took a parenthesised run of anything and `set system
host-name (foo bar)` validated. The assertions here are deliberately negative
as well as positive: a validator that accepts everything passes every
positive test there is.

Lines whose verdict every validation door must share (keyed entries, compact
siblings, bracket shorthand) are in `tests/contract/test_every_door.py`; the
set corpus is `test_set_corpus.py`.
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest

from junoscfg import Format, convert_config

# The regeneration evidence needs the pipeline stages, which the named surfaces
# expose only composed, as `schema generate` from an XSD the repository does
# not hold. An exception in `tools/check_test_doors.py`.
from junoscfg.validate import ALL_FIXES, SchemaNode, generate_lark_grammar, read_structure_tree
from tests.support.artifacts import shipped, shipped_text

APPLY_STATEMENTS = ("apply-groups", "apply-groups-except", "apply-flags", "apply-macro")


@pytest.fixture(scope="module")
def shipped_schema_tree() -> SchemaNode:
    """The shipped structure tree as the generator reads it, once per module."""
    return read_structure_tree(shipped("junos-structure-tree.json"))


class TestTheShippedGrammarIsTheGeneratorsOutput:
    """The shipped grammar loads, and is what the generator makes from the shipped tree."""

    def test_the_shipped_grammar_loads(self, bundled_set_validator: Any) -> None:
        """Set validation does nothing if it cannot load its grammar.

        It could not, from the 24.4 migration until the artefact was rebuilt:
        both `junoscfg -i set -v` and `-i structured -v` reported "Error loading
        validation artifacts" on a valid and an invalid config alike, because
        JunosValidator builds StructuredValidator around the same SetValidator.
        JSON and YAML validation never used this grammar.
        """
        assert bundled_set_validator.validate("set system host-name router1").valid

    def test_the_shipped_grammar_matches_its_structure_tree(
        self, shipped_schema_tree: SchemaNode
    ) -> None:
        """`ARCHITECTURE.md` section 8 forbids hand-editing a generated artefact.

        The XSD dump the artefacts came from is not in the repository, so the
        grammar is rebuilt from `junos-structure-tree.json` instead, which is
        how `ArtifactBuilder` builds it too. To rebuild it::

            from junoscfg.validate import read_structure_tree, write_lark_grammar

            root = read_structure_tree(".../data/junos-structure-tree.json")
            write_lark_grammar(root, ".../data/junos-set.lark")
        """
        rebuilt = generate_lark_grammar(shipped_schema_tree)
        assert rebuilt.strip() == shipped_text("junos-set.lark").strip()


#: The probe's policy term (QFX5120 25.2R2-S1.5, D2): the device takes `then
#: community = | + | -` and prints it so; the grammar took the rule-name escapes
#: instead (SET-LITERAL-KEYWORDS-001, change device-probe-fixes).
_THEN = "set policy-options policy-statement JUNOSCFG-PROBE term t1 then"
_ESCAPES = ("eq_literal", "plus_literal", "minus_literal")


class TestTheShippedGrammarKeepsRejecting:
    """A value slot takes one value, and an unknown element is no element. A
    container the XSD marks `oneliner` takes its leaves and flags on one line,
    as the device takes `hold-time up 0 down 0` (probe D1,
    SET-COMPACT-LEAVES-001); a container it does not mark takes one a line.
    Neither the chassis flags no device showed nor the rule-name escapes are
    statements."""

    @pytest.mark.parametrize(
        "line",
        [
            "set system host-name router1",
            "set policy-options policy-statement P term T from policy "
            "(( A && ! B ) || ( ! C && D ))",
            'set interfaces ge-0/0/0 description "uplink to sw1 \\"core\\""',
            'set system host-name "abc\\"',
            'set interfaces ge-0/0/0 description "a b\\"',
            *(f"{_THEN} community {symbol} JUNOSCFG-C1" for symbol in "=+-"),
            "set interfaces ge-0/0/1 hold-time up 0 down 0",
            "set interfaces ge-0/0/1 hold-time down 0 up 0",
            "set protocols ospf traceoptions file ospf.log size 10m files 3",
        ],
        ids=[
            "a-hostname-takes-a-plain-value",
            "a-policy-expression-is-one-value",
            "an-escaped-quote-is-part-of-its-value",
            "a-word-ending-in-a-backslash",
            "a-quoted-value-ending-in-a-backslash",
            "community-equals",
            "community-plus",
            "community-minus",
            "a-oneliner-container-on-one-line",
            "a-oneliner-container-in-either-order",
            "a-oneliner-file-list-as-before",
        ],
    )
    def test_accepted(self, bundled_set_validator: Any, line: str) -> None:
        assert bundled_set_validator.validate(line).valid is True, line

    @pytest.mark.parametrize(
        "line",
        [
            "set system host-name (foo bar)",
            "set interfaces ge-0/0/0 description (not a policy expression)",
            "set interfaces ge-0/0/0 bogus-thing 5",
            "set system host-name",
            "set system host-name foo bar baz",
            'set interfaces ge-0/0/0 description "uplink to sw1 "core""',
            'set system host-name "a\\\\" b"',
            *(f"{_THEN} community {escape} JUNOSCFG-C1" for escape in _ESCAPES),
            "set chassis debugger-on-panic",
            "set chassis debugger-on-break",
            "set system host-name router1 domain-name example.net",
            "set interfaces ge-0/0/1 hold-time up 0 bogus 1",
            "set interfaces ge-0/0/1 hold-time up 0 down",
        ],
        ids=[
            "a-hostname-is-not-a-policy-expression",
            "a-description-is-not-a-policy-expression",
            "an-unknown-element",
            "a-leaf-with-no-value",
            "a-leaf-with-three-values",
            "bare-inner-quotes-end-the-value",
            "an-escaped-backslash-ends-before-the-quote",
            *(f"community-{escape}" for escape in _ESCAPES),
            "a-chassis-flag-no-device-showed",
            "another-chassis-flag-no-device-showed",
            "two-leaves-of-a-container-the-xsd-does-not-mark-oneliner",
            "an-unknown-sibling-in-a-oneliner-container",
            "a-oneliner-sibling-without-its-value",
        ],
    )
    def test_rejected(self, bundled_set_validator: Any, line: str) -> None:
        assert bundled_set_validator.validate(line).valid is False, line


class TestJunoscfgsOwnSetOutputValidates:
    """Whatever junoscfg writes validates with the grammar it ships.

    The set reader, the set writer and the shipped grammar agree on a quoted
    value (Test/Challenge SC2, interim ruling): an inner `"` is escaped, a
    backslash is written as is, a value ending in one stays accepted.
    """

    @pytest.mark.parametrize(
        "value",
        ['uplink to sw1 "core"', "abc\\", "a b\\", "Authorized use only.\\nAll", 'say "hi"; {x}'],
        ids=[
            "an-escaped-quote",
            "a-word-ending-in-a-backslash",
            "a-trailing-backslash",
            "a-backslash-n",
            "delimiters",
        ],
    )
    def test_the_written_line_validates(self, bundled_set_validator: Any, value: str) -> None:
        config = {"interfaces": {"interface": [{"name": "ge-0/0/0", "description": value}]}}
        line = convert_config(
            json.dumps({"configuration": config}), from_format=Format.JSON, to_format=Format.SET
        )
        assert bundled_set_validator.validate(line).valid is True, line


class TestTheShippedArtifactsModelTheApplyStatements:
    """The four `apply-*` statements validate wherever Junos allows them.

    `xsd_fixes._fix_apply_statements` declares them on the root with the
    `universal` flag and the grammar splices them into every rule. Until 0.8.0
    the bundled tree predated the fix and the validator cut them off the line
    before parsing; the 25.2R2 artifacts carry the four nodes, so the proof is
    the artifact itself: the nodes are there with their flag, the fix has
    nothing left to add, and the grammar takes them at depth, at the top, on a
    deactivate line and inside a quoted value the old bridge cut in half. Raw
    bracket shorthand has its own contract, in `tests/contract/test_every_door.py`.
    """

    def test_the_four_nodes_carry_the_flag(self, shipped_schema_tree: SchemaNode) -> None:
        for name in APPLY_STATEMENTS:
            assert "universal" in shipped_schema_tree.children[name].flags, name

    def test_the_fix_has_nothing_left_to_add(self, shipped_schema_tree: SchemaNode) -> None:
        (fix,) = [f for f in ALL_FIXES if f.id == "apply-statements"]
        assert not fix.apply(shipped_schema_tree)

    @pytest.mark.parametrize(
        "line",
        [
            "set apply-groups foo",
            "set apply-groups global-vxlan",
            "set system apply-groups-except foo",
            "set protocols bgp group G apply-groups foo",
            "set protocols bgp group overlay apply-flags replace",
            # The device's own line (group GR-OMIT of the synthetic oracle
            # captures, vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5), and the top.
            "set groups GR-OMIT system apply-flags omit",
            "set apply-flags omit",
            "set interfaces ge-0/0/0 apply-macro m1",
            "set interfaces ge-0/0/0 unit 0 apply-groups foo",
            "set interfaces ge-0/0/0 apply-groups-except bar",
            "set policy-options policy-statement p1 apply-macro m1 key1 val1",
            'set interfaces ge-0/0/0 description "uplink to apply-groups foo"',
            # The bridge ran on deactivate lines as well; the grammar path does.
            "deactivate protocols bgp group G apply-groups foo",
        ],
    )
    def test_an_apply_statement_validates(self, bundled_set_validator: Any, line: str) -> None:
        assert bundled_set_validator.validate(line).valid is True, line

    @pytest.mark.parametrize(
        "line",
        [
            # Under a keyword container. After a list entry name a bare token
            # is taken as a value, which is the grammar's general looseness.
            "set system apply-groups",
            # The splice is four names, not a hole.
            "set system apply-nonsense foo",
            # `apply-flags` holds its flags, not any value: the device writes
            # `omit` as a flag (`<apply-flags><omit/></apply-flags>`). Any
            # word passed while the tree had it as a leaf (DEV-V2).
            "set system apply-flags bogus",
            # A bare `apply-flags` names no flag (0.17.0 rejected it too).
            "set system apply-flags",
            "set apply-flags",
            # No universal statement inside another: `apply-flags` holds flags.
            "set system apply-flags apply-groups G1",
            "set system apply-flags apply-flags omit",
        ],
        ids=[
            "apply-groups-needs-its-group",
            "only-the-four-names",
            "apply-flags-takes-its-flags",
            "apply-flags-needs-a-flag",
            "apply-flags-needs-a-flag-at-the-top",
            "no-universal-statement-inside-apply-flags",
            "no-apply-flags-inside-apply-flags",
        ],
    )
    def test_an_apply_statement_is_rejected(self, bundled_set_validator: Any, line: str) -> None:
        assert bundled_set_validator.validate(line).valid is False, line


class TestCompactSiblingsParseInPracticalTime:
    """Compact sibling commands cost what their expanded forms cost, not more.

    Spec: validation/set-command-validation, "Sibling validation has bounded
    parse cost". A grammar that repeats sibling alternatives can make the
    Earley parser's work grow with every sibling on the line; these commands
    are the shapes that would show it.
    """

    COMPACT = (
        "set system ntp server 198.51.100.1 version 4 prefer routing-instance mgmt_junos",
        "set routing-options maximum-prefixes 3000000 threshold 50 log-interval 5",
    )
    EXPANDED = (
        "set system ntp server 198.51.100.1 version 4\n"
        "set system ntp server 198.51.100.1 prefer\n"
        "set system ntp server 198.51.100.1 routing-instance mgmt_junos",
        "set routing-options maximum-prefixes 3000000\n"
        "set routing-options maximum-prefixes threshold 50\n"
        "set routing-options maximum-prefixes log-interval 5",
    )

    @staticmethod
    def _seconds(validator: Any, source: str) -> float:
        """The best of three runs: the least disturbed by whatever else the host does."""
        best = float("inf")
        for _ in range(3):
            started = time.perf_counter()
            assert validator.validate(source).valid is True
            best = min(best, time.perf_counter() - started)
        return best

    def test_compact_siblings_keep_practical_parse_time(self, bundled_set_validator: Any) -> None:
        """The spec's bound: 100 compact commands within five seconds.

        They take about 0.1 s on a developer machine, so the bound is some
        fifty times the cost and only a change in kind trips it, not a slow
        or busy runner. The relative test below is the sharper guard.
        """
        elapsed = self._seconds(bundled_set_validator, "\n".join(self.COMPACT * 50))
        assert elapsed < 5.0, f"100 compact sibling commands took {elapsed:.2f}s"

    def test_compact_siblings_cost_no_more_than_their_expanded_form(
        self, bundled_set_validator: Any
    ) -> None:
        """Relative to the same content written out, so the host's speed cancels.

        The compact form is the cheaper of the two, fewer lines carrying the
        same settings (about 0.4 of the expanded cost when this was written);
        twice the expanded cost leaves a factor of five for noise while still
        catching a cost that grows with the siblings on a line.
        """
        compact = self._seconds(bundled_set_validator, "\n".join(self.COMPACT * 50))
        expanded = self._seconds(bundled_set_validator, "\n".join(self.EXPANDED * 50))
        assert compact <= 2 * expanded, f"compact {compact:.3f}s, expanded {expanded:.3f}s"
