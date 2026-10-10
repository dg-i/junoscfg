"""Tests for JunosValidator unified facade."""

from __future__ import annotations

import json

import pytest

from junoscfg.validate import SchemaLoadError
from junoscfg.validate.validator import JunosValidator


class TestJunosValidator:
    def test_validate_json(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        data = json.dumps({"configuration": {"system": {"host-name": "r1"}}})
        result = v.validate_json(data)
        assert result.valid is True

    def test_validate_json_invalid(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        data = json.dumps({"configuration": {"bogus": "value"}})
        result = v.validate_json(data)
        assert result.valid is False

    def test_validate_yaml(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        yaml_str = "configuration:\n  system:\n    host-name: r1\n"
        result = v.validate_yaml(yaml_str)
        assert result.valid is True

    def test_validate_set(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        result = v.validate_set("set system host-name r1")
        assert result.valid is True

    def test_validate_set_invalid(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        result = v.validate_set("set bogus nonexistent")
        assert result.valid is False

    def test_validate_structured(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        result = v.validate_structured("system {\n    host-name r1;\n}\n")
        assert result.valid is True

    def test_schema_version(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        assert v.schema_version == "21.4R0"

    def test_generated_at(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        assert "2026" in v.generated_at


class TestArtifactResolution:
    def test_explicit_dir(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        assert v.schema_version == "21.4R0"

    def test_env_var(self, artifacts_dir, monkeypatch):
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", artifacts_dir)
        v = JunosValidator()
        assert v.schema_version == "21.4R0"

    def test_nonexistent_dir_raises(self):
        with pytest.raises(SchemaLoadError, match="not found"):
            JunosValidator(artifacts_dir="/nonexistent/path")

    def test_default_bundled(self):
        # Should use bundled artifacts without error
        v = JunosValidator()
        assert v.schema_version is not None
