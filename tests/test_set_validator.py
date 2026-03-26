"""Tests for set command validator."""

from __future__ import annotations

import tempfile

import pytest

from junoscfg.validate import SchemaLoadError
from junoscfg.validate.set_validator import SetValidator

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
