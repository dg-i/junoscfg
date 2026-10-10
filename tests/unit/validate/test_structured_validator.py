"""Tests for structured configuration validator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from junoscfg.validate import SetValidator, StructuredValidator
from tests.support.artifacts import make_artifacts_dir

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def structured_validator(tmp_path: Path) -> StructuredValidator:
    """Around a `SetValidator` on the minimal grammar, as `JunosValidator` builds it."""
    return StructuredValidator(SetValidator(make_artifacts_dir(tmp_path).grammar))


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
