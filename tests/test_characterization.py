"""Characterization tests pinning the public surface (onboarding phase 3).

These record what junoscfg does today, including behaviour that is wrong.  A
characterization test is not an assertion that the behaviour is correct; it is
a record that it was this before an agent touched the code.  Each test here was
seen to fail against a deliberate mutation before being committed.

Three of these pin defects.  The fix for each is a separate change, and that
change is expected to rewrite the test rather than delete it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from junoscfg import validate_xml
from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.validate import SchemaLoadError

SIMPLE_XML = "<configuration><system><host-name>router1</host-name></system></configuration>"

MINIMAL_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="system" minOccurs="0">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>
"""


class TestValidateXmlNeedsAnXsdNobodyShips:
    """``validate_xml`` is in ``__all__`` but cannot run on bundled artifacts.

    It requires ``junos-validated.xsd`` in the artifacts directory
    (``validate/validator.py:77``).  No such file exists under
    ``src/junoscfg/validate/data/``, which ships five JSON/lark artifacts and
    no XSD, so every call that does not point at a caller-supplied directory
    raises.  Pinned as a defect on the declared beta ``api`` surface.
    """

    def test_raises_without_a_validated_xsd(self, artifacts_dir: str) -> None:
        with pytest.raises(SchemaLoadError, match="XSD not found"):
            validate_xml(SIMPLE_XML, artifacts_dir=artifacts_dir)

    def test_bundled_artifacts_ship_no_xsd(self) -> None:
        import junoscfg.validate as validate_pkg

        data = Path(validate_pkg.__file__).parent / "data"
        assert data.is_dir()
        assert list(data.glob("*.xsd")) == []


class TestSchemaMakedocIsDead:
    """``junoscfg schema makedoc`` imports a module that has never existed.

    ``cli.py:726`` does ``from junoscfg.validate.schema_doc import
    generate_doc``; there is no ``schema_doc.py`` in the tree or anywhere in
    git history.  The command is documented in ``docs/guide/cli.md`` with
    worked examples and is listed in the help test, which is why nothing has
    caught it.  Its ``-o`` write path is unreachable for the same reason.
    """

    def test_makedoc_raises_module_not_found(self, tmp_path: Path) -> None:
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)

        runner = CliRunner()
        result = runner.invoke(main, ["schema", "makedoc", str(xsd)])

        assert result.exit_code != 0
        assert isinstance(result.exception, ModuleNotFoundError)
        assert "schema_doc" in str(result.exception)


class TestSchemaGenerateWritesOutsideTheRepo:
    """``schema generate -o DIR`` creates the directory and overwrites in it.

    This is the reachable file-writing surface, and it is intended: the caller
    names the directory.  Pinned so that a change to what gets written, or to
    the silent overwrite, is visible.
    """

    def test_creates_dir_and_writes_five_artifacts(self, tmp_path: Path) -> None:
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)
        out = tmp_path / "does-not-exist-yet"

        runner = CliRunner()
        result = runner.invoke(main, ["schema", "generate", str(xsd), "-o", str(out)])

        assert result.exit_code == 0
        assert out.is_dir()
        assert {p.name for p in out.iterdir()} == {
            "junos-structure-tree.json",
            "junos-json-schema.json",
            "junos-yaml-schema.json",
            "junos-set.lark",
            "junos-schema-meta.json",
        }

    def test_existing_artifacts_are_overwritten_without_prompt(self, tmp_path: Path) -> None:
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)
        out = tmp_path / "artifacts"
        out.mkdir()
        stale = out / "junos-schema-meta.json"
        stale.write_text("STALE")

        runner = CliRunner()
        result = runner.invoke(main, ["schema", "generate", str(xsd), "-o", str(out)])

        assert result.exit_code == 0
        assert stale.read_text() != "STALE"


class TestNetworksAutoNoOpsThroughThePythonApi:
    """``networks=["auto"]`` silently does nothing through the Python API.

    ``cli.py:331`` attaches ``_source_text`` dynamically with a ``type:
    ignore``; ``anonymize/rules/ip.py:108`` reads it back through ``hasattr``.
    A caller using the documented Python API never sets it, so auto-detection
    is dropped with no error and no warning.  Pinned as a defect.
    """

    def test_auto_is_dropped_silently(self) -> None:
        ir = {
            "configuration": {
                "system": {"host-name": "router1"},
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "203.0.114.1/24"}]}},
                                }
                            ],
                        }
                    ]
                },
            }
        }
        config = AnonymizeConfig(ips=True, networks=["auto"], salt="pin-salt")
        config.expand_all()

        assert not hasattr(config, "_source_text")
        result = anonymize(ir, config)
        assert result is not None


class TestEdityamlSurfaceTheCollectionDrives:
    """``rename-root`` and ``ansibilize`` are driven by the Ansible collection.

    ``dg-i/ansible-collection-junos-config`` documents both in its group_vars
    pipelines, so their output shape is part of the declared ``cli`` surface.
    """

    @staticmethod
    def _yaml_config(tmp_path: Path) -> Path:
        from junoscfg import Format, convert_config

        src = Path("examples/router1.conf").read_text()
        out = tmp_path / "router1.yaml"
        out.write_text(convert_config(src, from_format=Format.STRUCTURED, to_format=Format.YAML))
        return out

    def test_rename_root_renames_and_sorts_keys(self, tmp_path: Path) -> None:
        """The new root is emitted first and its children come out sorted."""
        cfg = self._yaml_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "rename-root", "--to", "junos_config", str(cfg)])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines[0] == "junos_config:"
        # Characterization: children are reordered alphabetically, not kept in
        # configuration order.  firewall sorts before system.
        children = [
            ln.strip().rstrip(":") for ln in lines if ln.startswith("  ") and ln.endswith(":")
        ]
        assert children[0] == "firewall"

    def test_ansibilize_emits_host_vars_then_group_vars(self, tmp_path: Path) -> None:
        """Output is host_vars, a '---' separator, then templated group_vars."""
        cfg = self._yaml_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "-p",
                "hostname:configuration.system.host-name",
                str(cfg),
            ],
        )

        assert result.exit_code == 0
        assert result.output.startswith("hostname: router1\n")
        assert "\n---\n" in result.output


class TestXmlAndStructuredInputDisagreeOnTheIr:
    """The same configuration yields two different IRs depending on input format.

    Surfaced by ``examples/router1.*``, which are three renderings of one
    configuration.  ``set``-side rendering hides both divergences — XML and
    structured both produce byte-identical ``.set`` output — so only the JSON
    IR shows them.  Both are pinned as defects.

    1. ``KEY_ALIASES`` (``display/constants.py:82``) is applied only in
       ``convert/input/set_input.py``.  The XML path never consults it, so
       ``<ieee-802.3ad>`` stays ``ieee-802.3ad`` where the structured path
       normalises to ``802.3ad``.
    2. Numeric leaves come back as ``int`` from XML and ``str`` from
       structured, at eleven sites in this fixture alone.
    """

    @staticmethod
    def _irs() -> tuple[dict, dict]:
        import json

        from junoscfg import Format, convert_config

        conf = Path("examples/router1.conf").read_text()
        xml = Path("examples/router1.xml").read_text()
        return (
            json.loads(convert_config(conf, from_format=Format.STRUCTURED, to_format=Format.JSON)),
            json.loads(convert_config(xml, from_format=Format.XML, to_format=Format.JSON)),
        )

    def test_key_alias_not_applied_on_the_xml_path(self) -> None:
        from_conf, from_xml = self._irs()
        conf_eo = from_conf["configuration"]["interfaces"]["interface"][2]["ether-options"]
        xml_eo = from_xml["configuration"]["interfaces"]["interface"][2]["ether-options"]
        assert list(conf_eo) == ["802.3ad"]
        assert list(xml_eo) == ["ieee-802.3ad"]

    def test_numeric_leaves_are_int_from_xml_and_str_from_structured(self) -> None:
        from_conf, from_xml = self._irs()
        conf_uid = from_conf["configuration"]["system"]["login"]["user"][0]["uid"]
        xml_uid = from_xml["configuration"]["system"]["login"]["user"][0]["uid"]
        assert conf_uid == "2000" and isinstance(conf_uid, str)
        assert xml_uid == 2000 and isinstance(xml_uid, int)

    def test_set_output_hides_both_divergences(self) -> None:
        """Both paths still render identical set output, which is why this
        went unnoticed."""
        from junoscfg import Format, convert_config

        conf = Path("examples/router1.conf").read_text()
        xml = Path("examples/router1.xml").read_text()
        assert convert_config(
            conf, from_format=Format.STRUCTURED, to_format=Format.SET
        ) == convert_config(xml, from_format=Format.XML, to_format=Format.SET)
