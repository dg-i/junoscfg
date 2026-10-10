"""Tests for structured configuration validator."""

from __future__ import annotations

import tempfile

import pytest

from junoscfg.validate.set_validator import SetValidator
from junoscfg.validate.structured_validator import StructuredValidator

# Minimal Lark grammar for testing
MINIMAL_GRAMMAR = """\
start: SET configuration
configuration: "system" system | "interfaces" interfaces
system: "host-name" VALUE | "services" services
services: "ssh"
interfaces: "description" QUOTED_OR_VALUE

SET: "set"
VALUE: /\\S+/
QUOTED: /"[^"]*"/
QUOTED_OR_VALUE: QUOTED | VALUE

%import common.WS
%ignore WS
"""


@pytest.fixture
def structured_validator():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lark", delete=False) as f:
        f.write(MINIMAL_GRAMMAR)
        grammar_path = f.name
    set_validator = SetValidator(grammar_path)
    return StructuredValidator(set_validator)


class TestStructuredValidator:
    def test_valid_structured(self, structured_validator):
        config = """\
system {
    host-name router1;
}
"""
        result = structured_validator.validate(config)
        assert result.valid is True

    def test_valid_nested(self, structured_validator):
        config = """\
system {
    services {
        ssh;
    }
}
"""
        result = structured_validator.validate(config)
        assert result.valid is True

    def test_invalid_structured(self, structured_validator):
        config = """\
bogus {
    nonexistent value;
}
"""
        result = structured_validator.validate(config)
        assert result.valid is False

    def test_empty_config(self, structured_validator):
        result = structured_validator.validate("")
        assert result.valid is True
