"""Tests for JunosValidator unified facade."""

from __future__ import annotations

import json

import pytest

from junoscfg import validate_xml
from junoscfg.validate import JunosValidator, SchemaLoadError
from tests.support.paths import ARTIFACT_DIR


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

    def test_validate_yaml_as_json_uses_the_json_schema(self, artifacts_dir):
        """The yaml-new door: an Ansible meta key the YAML schema allows is an
        error, as in JSON (Test/Challenge B1)."""
        v = JunosValidator(artifacts_dir=artifacts_dir)
        yaml_str = "configuration:\n  system:\n    host-name: r1\n    _ansible_host: x\n"
        as_json = json.dumps(
            {"configuration": {"system": {"host-name": "r1", "_ansible_host": "x"}}}
        )
        result = v.validate_yaml_as_json(yaml_str)
        assert result.valid is False
        assert result.errors == v.validate_json(as_json).errors
        assert v.validate_yaml(yaml_str).valid is True

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
        with pytest.deprecated_call():
            result = v.validate_structured("system {\n    host-name r1;\n}\n")
        assert result.valid is True

    def test_schema_version(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        assert v.schema_version == "21.4R0"

    def test_generated_at(self, artifacts_dir):
        v = JunosValidator(artifacts_dir=artifacts_dir)
        assert "2026" in v.generated_at


class TestArtifactResolution:
    """What the validator does with the directory the resolver names.

    The resolution order itself (argument, override, `JUNOSCFG_ARTIFACTS`,
    bundle) is `display.resolve_artifacts_dir`'s, and its tests, the
    validator's included, are `tests/unit/display/test_artifact_resolution.py`.
    """

    def test_nonexistent_dir_raises(self):
        with pytest.raises(SchemaLoadError, match="not found"):
            JunosValidator(artifacts_dir="/nonexistent/path")

    def test_default_bundled(self):
        # Should use bundled artifacts without error
        v = JunosValidator()
        assert v.schema_version is not None


class TestValidateXmlNeedsACleanedXsd:
    """``validate_xml`` needs ``junos-validated.xsd``, which nothing produces.

    The name is the point: a *validated* XSD is a cleaned one. A raw NETCONF
    dump does not compile. Measured on a real 163 MB dump at Junos 23.2R2,
    lxml refuses it with::

        Element 'xsd:element', attribute 'name': 'openconfig-lldp:lldp' is
        not a valid value of the atomic type 'xs:NCName'

    85 element names carry OpenConfig prefixes containing a colon, and that is
    only the first error lxml reports. `schema generate` briefly wrote the raw
    extract under this name; it was reverted, because a 156 MB file that does
    not compile is worse than an honest absence. Cleaning the XSD is real work
    and is not yet done. That `schema generate` writes no XSD is
    `tests/unit/cli/test_schema_command.py::TestSchemaGenerate`.
    """

    def test_raises_when_the_xsd_is_absent(self, artifacts_dir: str) -> None:
        xml = "<configuration><system><host-name>router1</host-name></system></configuration>"
        with pytest.raises(SchemaLoadError, match="XSD not found"):
            validate_xml(xml, artifacts_dir=artifacts_dir)

    def test_the_bundled_artifacts_ship_no_xsd(self) -> None:
        """Intended: the XSD is per-device and per-release, not per-wheel."""
        assert ARTIFACT_DIR.is_dir()
        assert list(ARTIFACT_DIR.glob("*.xsd*")) == []
