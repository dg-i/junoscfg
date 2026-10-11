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
        with pytest.deprecated_call():
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
        with pytest.deprecated_call():
            result = structured_validator.validate(config)
        assert result.valid is True

    def test_invalid_structured(self, structured_validator):
        config = """\
bogus {
    nonexistent value;
}
"""
        with pytest.deprecated_call():
            result = structured_validator.validate(config)
        assert result.valid is False

    def test_empty_config(self, structured_validator):
        with pytest.deprecated_call():
            result = structured_validator.validate("")
        assert result.valid is True


class TestTheStructuredDoorsAreDeprecated:
    """Spec: validation/structured-validation, "The validate package's structured doors are
    deprecated".

    The package may not import `junoscfg.convert` (`tach.toml`), so these
    doors cannot reach the conversion walk that splits a one-line statement;
    `junoscfg.validate_structured` composes it. Makeover run 2026-10-11,
    change structured-one-line-blocks (NEW-B5, OPEN-10).
    """

    def test_each_warns_and_keeps_its_schema_free_route(
        self, structured_validator: StructuredValidator, artifacts_dir: str
    ) -> None:
        from junoscfg.validate import JunosValidator

        config = "system {\n    host-name router1;\n}\n"
        with pytest.deprecated_call(match="junoscfg.validate_structured"):
            assert structured_validator.validate(config).valid is True
        with pytest.deprecated_call(match="junoscfg.validate_structured"):
            facade = JunosValidator(artifacts_dir=artifacts_dir).validate_structured(config)
        assert facade.valid is True
        with pytest.deprecated_call(match="junoscfg.validate_structured"):
            assert (
                structured_validator.validate("bogus {\n    nonexistent value;\n}\n").valid is False
            )

    def test_the_new_lexer_changes_a_verdict(
        self, structured_validator: StructuredValidator
    ) -> None:
        """Test/Challenge F6: the route stays schema-free and the lexer is the
        new one. A block on one line read as nothing and validated; now its
        statement is read, and the grammar rejects it."""
        with pytest.deprecated_call(match="junoscfg.validate_structured"):
            assert structured_validator.validate("system { bogus-statement 1; }").valid is False
