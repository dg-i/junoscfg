"""Tests for validate package shared types."""

from __future__ import annotations

from junoscfg.validate import SchemaLoadError, ValidationError, ValidationResult


class TestValidationError:
    def test_basic(self):
        err = ValidationError(message="bad config")
        assert err.message == "bad config"
        assert err.line is None
        assert err.path is None

    def test_with_location(self):
        err = ValidationError(message="unknown element", line=42, path="system/host-name")
        assert err.line == 42
        assert err.path == "system/host-name"

    def test_frozen(self):
        err = ValidationError(message="test")
        try:
            err.message = "other"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestValidationResult:
    def test_valid(self):
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == ()
        assert result.warnings == ()

    def test_invalid(self):
        errs = (ValidationError(message="err1"), ValidationError(message="err2"))
        result = ValidationResult(valid=False, errors=errs)
        assert result.valid is False
        assert len(result.errors) == 2

    def test_with_warnings(self):
        warns = (ValidationError(message="warn1"),)
        result = ValidationResult(valid=True, warnings=warns)
        assert result.valid is True
        assert len(result.warnings) == 1


class TestSchemaLoadError:
    def test_is_exception(self):
        assert issubclass(SchemaLoadError, Exception)

    def test_message(self):
        err = SchemaLoadError("artifacts not found")
        assert str(err) == "artifacts not found"
