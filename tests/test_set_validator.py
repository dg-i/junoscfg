"""Tests for set command validator."""

from __future__ import annotations

import tempfile
import time
from typing import TYPE_CHECKING

import pytest

from junoscfg import Format, validate_config, validate_set
from junoscfg.validate import JunosValidator, SchemaLoadError, ValidationError
from junoscfg.validate.grammar_generator import generate_lark_grammar
from junoscfg.validate.schema_node import SchemaNode
from junoscfg.validate.set_validator import SetValidator

if TYPE_CHECKING:
    from pathlib import Path

# Minimal Lark grammar for testing
MINIMAL_GRAMMAR = """\
start: SET configuration
configuration: "system" system | "interfaces" interfaces
system: "host-name" VALUE
interfaces: "description" QUOTED_OR_VALUE

SET: "set"
DEACTIVATE: "deactivate"
VALUE: /\\S+/
QUOTED: /"[^"]*"/
QUOTED_OR_VALUE: QUOTED | VALUE

%import common.WS
%ignore WS
"""


@pytest.fixture
def grammar_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lark", delete=False) as f:
        f.write(MINIMAL_GRAMMAR)
        return f.name


@pytest.fixture
def validator(grammar_path):
    return SetValidator(grammar_path)


class TestSetValidator:
    def test_valid_set_command(self, validator):
        result = validator.validate("set system host-name router1")
        assert result.valid is True

    def test_valid_multiple_lines(self, validator):
        source = "set system host-name router1\nset interfaces description test\n"
        result = validator.validate(source)
        assert result.valid is True

    def test_invalid_set_command(self, validator):
        result = validator.validate("set bogus nonexistent")
        assert result.valid is False
        assert len(result.errors) > 0
        assert result.errors[0].line == 1

    def test_deactivate_line(self, validator):
        result = validator.validate(
            "set system host-name router1\ndeactivate system host-name router1"
        )
        assert result.valid is True

    def test_comment_lines_skipped(self, validator):
        source = "# This is a comment\nset system host-name router1\n"
        result = validator.validate(source)
        assert result.valid is True

    def test_empty_lines_skipped(self, validator):
        source = "\n\nset system host-name router1\n\n"
        result = validator.validate(source)
        assert result.valid is True

    def test_no_set_prefix_error(self, validator):
        result = validator.validate("system host-name router1")
        assert result.valid is False
        assert "does not start with" in result.errors[0].message

    def test_quoted_value(self, validator):
        result = validator.validate('set interfaces description "my interface"')
        assert result.valid is True

    def test_load_error(self):
        with pytest.raises(SchemaLoadError):
            SetValidator("/nonexistent/grammar.lark")


class TestSetBracketSyntaxRejection:
    _COMMANDS = (
        "set system apply-groups [ foo bar ]",
        "delete system apply-groups [ foo bar ]",
        "deactivate system apply-groups [ foo bar ]",
        "activate system apply-groups [ foo bar ]",
        "protect system apply-groups [ foo bar ]",
        "replace system apply-groups [ foo bar ]",
    )

    def test_validation_doors_return_line_errors_without_throwing(
        self, bundled_set_validator: SetValidator, artifacts_dir: str
    ) -> None:
        line = self._COMMANDS[0]
        results = (
            bundled_set_validator.validate(line),
            validate_set(line, artifacts_dir=artifacts_dir),
            validate_config(line, format=Format.SET, artifacts_dir=artifacts_dir),
        )

        for result in results:
            assert result.valid is False
            assert result.errors == (
                ValidationError(
                    message=f"Unsupported bracket syntax in set input on line 1:\n{line}",
                    line=1,
                ),
            )

        for command in self._COMMANDS:
            result = bundled_set_validator.validate(command)
            assert result.errors[0].message == (
                f"Unsupported bracket syntax in set input on line 1:\n{command}"
            )

        accepted = bundled_set_validator.validate(
            '# ignored bracket [\nset policy-options community FOO members "64498:[2-6]....$"'
        )
        assert accepted.valid is True

        after_comment = "/* ignored */ set system apply-groups [ foo bar ]"
        result = bundled_set_validator.validate(after_comment)
        assert result.errors == (
            ValidationError(
                message=(f"Unsupported bracket syntax in set input on line 1:\n{after_comment}"),
                line=1,
            ),
        )

        multiline_comment = "/* ignored\n[ still ignored ]\n*/\nset system host-name router1"
        assert bundled_set_validator.validate(multiline_comment).valid is True

    def test_validation_collects_each_offending_line(
        self, bundled_set_validator: SetValidator
    ) -> None:
        lines = [
            "# ignored bracket [",
            "set system apply-groups [ foo bar ]",
            "set system host-name router1",
            "delete system apply-groups ]",
        ]

        result = bundled_set_validator.validate("\n".join(lines))

        assert result.valid is False
        assert [(error.line, error.message) for error in result.errors] == [
            (2, f"Unsupported bracket syntax in set input on line 2:\n{lines[1]}"),
            (4, f"Unsupported bracket syntax in set input on line 4:\n{lines[3]}"),
        ]


class TestTheShippedGrammarKeepsRejecting:
    """What a validator must say no to, measured against the artefact we ship.

    Every other test in this module runs against `MINIMAL_GRAMMAR`, which has
    three rules. That is why a defect in the real one shipped: a global
    `EXPRESSION` terminal was added to `QUOTED_OR_VALUE`, which the generated
    grammar writes in 11,853 value slots, so every slot in the product took a
    parenthesised run of anything. `set system host-name (foo bar)` validated.

    These assertions are deliberately negative. A validator that accepts
    everything passes every positive test there is.
    """

    def test_a_hostname_is_not_a_policy_expression(self, bundled_set_validator) -> None:
        result = bundled_set_validator.validate("set system host-name (foo bar)")
        assert result.valid is False

    def test_a_description_is_not_a_policy_expression(self, bundled_set_validator) -> None:
        result = bundled_set_validator.validate(
            "set interfaces ge-0/0/0 description (not a policy expression)"
        )
        assert result.valid is False

    def test_a_policy_expression_is_still_one_value(self, bundled_set_validator) -> None:
        result = bundled_set_validator.validate(
            "set policy-options policy-statement P term T from policy "
            "(( A && ! B ) || ( ! C && D ))"
        )
        assert result.valid is True

    def test_a_hostname_still_takes_a_plain_value(self, bundled_set_validator) -> None:
        assert bundled_set_validator.validate("set system host-name router1").valid is True

    def test_an_unknown_element_is_rejected(self, bundled_set_validator) -> None:
        result = bundled_set_validator.validate("set interfaces ge-0/0/0 bogus-thing 5")
        assert result.valid is False

    def test_a_leaf_with_no_value_is_rejected(self, bundled_set_validator) -> None:
        assert bundled_set_validator.validate("set system host-name").valid is False

    def test_a_leaf_with_three_values_is_rejected(self, bundled_set_validator) -> None:
        assert bundled_set_validator.validate("set system host-name foo bar baz").valid is False


class TestTheShippedGrammarAcceptsMultipleSiblings:
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
    SHIPPED_ONLY = (
        "set protocols bgp traceoptions file bgp-log size 10m files 10",
        "set protocols bgp traceoptions file bgp-log\n"
        "set protocols bgp traceoptions file size 10m\n"
        "set protocols bgp traceoptions file files 10",
    )

    @staticmethod
    def _tree() -> SchemaNode:
        server = SchemaNode(
            name="server",
            is_list=True,
            children={
                "version": SchemaNode(name="version", is_leaf=True),
                "prefer": SchemaNode(name="prefer", is_presence=True),
                "routing-instance": SchemaNode(name="routing-instance", is_leaf=True),
            },
        )
        server.flags.add("oneliner")
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
                "system": SchemaNode(
                    name="system",
                    children={"ntp": SchemaNode(name="ntp", children={"server": server})},
                ),
                "routing-options": SchemaNode(
                    name="routing-options",
                    children={"maximum-prefixes": maximum_prefixes},
                ),
            },
        )

    def test_compact_and_expanded_forms_validate(
        self, bundled_set_validator: SetValidator, tmp_path: Path
    ) -> None:
        for source in (*self.COMPACT, *self.EXPANDED, *self.SHIPPED_ONLY):
            assert bundled_set_validator.validate(source).valid is True, source

        grammar_path = tmp_path / "junos-set.lark"
        grammar_path.write_text(generate_lark_grammar(self._tree()), encoding="utf-8")
        validators = (
            SetValidator(grammar_path).validate,
            JunosValidator(artifacts_dir=str(tmp_path)).validate_set,
            lambda source: validate_set(source, artifacts_dir=str(tmp_path)),
            lambda source: validate_config(source, format="set", artifacts_dir=str(tmp_path)),
        )
        for validate in validators:
            for source in (*self.COMPACT, *self.EXPANDED):
                assert validate(source).valid is True, source

    def test_unknown_sibling_is_rejected(self, bundled_set_validator: SetValidator) -> None:
        commands = (
            "set system ntp server 198.51.100.1 bogus-option 5",
            "set routing-options maximum-prefixes 3000000 bogus-option 5",
            "set snmp traceoptions file rogue size 1",
        )
        for command in commands:
            assert bundled_set_validator.validate(command).valid is False, command

    def test_compact_siblings_keep_practical_parse_time(
        self, bundled_set_validator: SetValidator
    ) -> None:
        source = "\n".join(self.COMPACT * 50)
        started = time.perf_counter()
        result = bundled_set_validator.validate(source)
        elapsed = time.perf_counter() - started
        assert result.valid is True
        assert elapsed < 5.0, f"100 compact sibling commands took {elapsed:.2f}s"


class TestTheShippedGrammarModelsTheApplyStatements:
    """The four `apply-*` statements validate wherever Junos allows them.

    `xsd_fixes._fix_apply_statements` declares them on the root with the
    `universal` flag and the grammar splices them into every rule. Until the
    artifacts were regenerated the validator cut them off the line before
    parsing -- a bridge with two tests that went red together on the day the
    shipped tree carried the four nodes, which was 0.8.0. These replace them:
    the statements at depth and at the top, and quoted values the bridge once
    cut in half. Raw bracket shorthand has its own negative contract tests.
    """

    @pytest.mark.parametrize(
        "line",
        [
            "set protocols bgp group G apply-groups foo",
            "set system apply-groups-except foo",
            "set protocols bgp group overlay apply-flags replace",
            "set interfaces ge-0/0/0 apply-macro m1",
            "set apply-groups foo",
        ],
    )
    def test_an_apply_statement_validates(self, bundled_set_validator, line: str) -> None:
        assert bundled_set_validator.validate(line).valid is True, line

    def test_a_description_mentioning_apply_groups_survives(self, bundled_set_validator) -> None:
        line = 'set interfaces ge-0/0/0 description "uplink to apply-groups foo"'
        assert bundled_set_validator.validate(line).valid is True

    def test_a_deactivate_line_takes_them_too(self, bundled_set_validator) -> None:
        """The bridge ran on deactivate lines as well; the grammar path does."""
        line = "deactivate protocols bgp group G apply-groups foo"
        assert bundled_set_validator.validate(line).valid is True

    def test_an_apply_groups_needs_its_group(self, bundled_set_validator) -> None:
        """Under a keyword container; after a list entry name a bare token is
        taken as a value, which is the grammar's general looseness, not this."""
        assert bundled_set_validator.validate("set system apply-groups").valid is False


# ── identifier-key-fields: the shipped grammar and keyed entries ─────
#
# Spec: openspec/changes/identifier-key-fields/specs/validation/
# set-command-validation, "A keyed entry takes exactly its key values". The
# lines are those a vMX on 23.2R2-S7.5 accepted and rejected, with the
# probe's synthetic names.

_PROBE_T = "set policy-options policy-statement SAMPLE-POLICY term T1 from"
_PROBE_THEN = "set policy-options policy-statement SAMPLE-POLICY term T1 then"
_PROBE_EVENT = "set event-options policy SAMPLE-EVENT-POLICY attributes-match"


class TestTheShippedGrammarTakesKeyedEntries:
    ACCEPTED = (
        f"{_PROBE_T} as-path-neighbors as-list SAMPLE-AS-LIST",
        "set policy-options policy-statement SAMPLE-POLICY from as-path-neighbors as-list "
        "SAMPLE-AS-LIST",
        f"{_PROBE_T} as-path-origins as-list-group SAMPLE-AS-LIST-GROUP",
        f"{_PROBE_T} as-path-transits as-list SAMPLE-AS-LIST-2",
        f"{_PROBE_T} as-path-neighbors as-list-group SAMPLE-AS-LIST",
        f"{_PROBE_T} route-filter 198.51.100.0/24 exact accept",
        f"{_PROBE_T} route-filter 198.51.100.0/24 orlonger",
        f"{_PROBE_T} source-address-filter 198.51.100.0/24 exact accept",
        f"{_PROBE_THEN} community add SAMPLE-COMM",
        f"{_PROBE_THEN} community delete SAMPLE-COMM",
        f"{_PROBE_THEN} community set SAMPLE-COMM",
        f"{_PROBE_THEN} community SAMPLE-COMM add",
        f'{_PROBE_EVENT} snmp_trap_link_down.interface-name matches "^xe-"',
        f'{_PROBE_EVENT} ping.test-owner matches "^uptime$"',
        "set groups SAMPLE-GROUP policy-options policy-statement <*> term T1 from "
        "as-path-neighbors as-list SAMPLE-AS-LIST",
        "set logical-systems SAMPLE-LS policy-options policy-statement SAMPLE-POLICY term T1 "
        "from as-path-neighbors as-list SAMPLE-AS-LIST",
    )
    REJECTED = (
        f"{_PROBE_T} as-path-neighbors as-list",
        f"{_PROBE_T} as-path-neighbors",
        f"{_PROBE_T} as-path-neighbors SAMPLE-AS-LIST",
        f"{_PROBE_T} as-path-neighbors as-list SAMPLE-AS-LIST SAMPLE-EXTRA",
        f"{_PROBE_T} route-filter 198.51.100.0/24 next-policy",
        f"{_PROBE_T} route-filter 198.51.100.0/24 exact SAMPLE-EXTRA",
        f'{_PROBE_EVENT} snmp_trap_link_down.interface-name matches "^xe-" SAMPLE-EXTRA',
        "set apply-groups SAMPLE-GROUP SAMPLE-GROUP-2",
    )

    def test_device_probe_lines(self, bundled_set_validator) -> None:
        import lark

        for line in self.ACCEPTED:
            bundled_set_validator._parser.parse(line)  # noqa: SLF001
        rejected_by_parser = []
        for line in self.REJECTED:
            try:
                bundled_set_validator._parser.parse(line)  # noqa: SLF001
            except lark.exceptions.UnexpectedInput:
                rejected_by_parser.append(line)
        assert rejected_by_parser == list(self.REJECTED)

        validator = JunosValidator()
        assert validator.validate_set("\n".join(self.ACCEPTED)).valid
        for line in self.REJECTED:
            assert not validator.validate_set(line).valid, line
        assert validate_config("\n".join(self.ACCEPTED), format=Format.SET).valid
        assert not validate_set(self.REJECTED[0]).valid

    def test_a_numeric_list_type_is_rejected(self, bundled_set_validator) -> None:
        """A key value takes its own leaf's type: `list-type` is `as-list` or
        `as-list-group`. The XSD's union also names `xsd:unsignedLong`, but the
        device rejected `as-path-neighbors 1 ...` at `set` with "syntax error,
        expecting <flag-value> or <attribute-value>." (round-1 probe, vMX
        23.2R2-S7.5). Owner answer 8, identifier-key-fields phase 4."""
        import lark

        with pytest.raises(lark.exceptions.UnexpectedInput):
            bundled_set_validator._parser.parse(  # noqa: SLF001
                f"{_PROBE_T} as-path-neighbors 1 SAMPLE-AS-LIST"
            )
        assert not validate_set(f"{_PROBE_T} as-path-neighbors 1 SAMPLE-AS-LIST").valid
