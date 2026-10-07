"""Tests for set command validator."""

from __future__ import annotations

import tempfile

import pytest

from junoscfg.validate import SchemaLoadError
from junoscfg.validate.set_validator import SetValidator, _strip_apply_groups

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

    def test_apply_groups_stripped(self, validator):
        result = validator.validate("set system host-name router1 apply-groups mygroup")
        assert result.valid is True

    def test_quoted_value(self, validator):
        result = validator.validate('set interfaces description "my interface"')
        assert result.valid is True

    def test_load_error(self):
        with pytest.raises(SchemaLoadError):
            SetValidator("/nonexistent/grammar.lark")


class TestStripApplyGroups:
    def test_strip_simple(self, validator):
        result = validator.validate("set system host-name r1 apply-groups foo")
        assert result.valid is True

    def test_strip_bracket(self, validator):
        result = validator.validate("set system host-name r1 apply-groups [foo bar]")
        assert result.valid is True

    def test_strip_except(self, validator):
        result = validator.validate("set system host-name r1 apply-groups-except foo")
        assert result.valid is True


class TestApplyGroupsStrippingStopsAtQuotes:
    """A description that mentions apply-groups is not an apply-groups.

    The stripper removes a trailing `apply-groups`/`apply-flags`/`apply-macro`
    before parsing, because none of them is in the schema. It reached inside a
    quoted value too, cutting the closing quote off
    `description "uplink to apply-groups foo"` and leaving something that could
    never parse. Found on a real device.
    """

    def test_a_description_mentioning_apply_groups_survives(self) -> None:
        line = 'set interfaces ge-0/0/0 description "uplink to apply-groups foo"'
        assert _strip_apply_groups(line) == line

    def test_a_real_apply_groups_is_still_stripped(self) -> None:
        assert (
            _strip_apply_groups("set protocols bgp group G apply-groups foo")
            == "set protocols bgp group G"
        )


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
