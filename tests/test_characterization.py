"""Characterization tests pinning the public surface (onboarding phase 3).

These record what junoscfg does today, including behaviour that is wrong.  A
characterization test is not an assertion that the behaviour is correct; it is
a record that it was this before an agent touched the code.  Each test here was
seen to fail against a deliberate mutation before being committed.

One of these still pins a defect: networks=["auto"].  A fix is a separate
change, and it rewrites the pin rather than deleting it -- as happened to
makedoc, validate_xml, rename-root ordering and the XML/structured IR
divergence, each of which now pins working behaviour instead.
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


class TestValidateXmlWorksOnGeneratedArtifacts:
    """``validate_xml`` needs ``junos-validated.xsd``, which is not bundled.

    That is deliberate and documented: the XSD comes from a NETCONF dump off a
    real device, and ``docs/guide/validation.md`` says so. What was broken is
    that the workflow it points at -- ``junoscfg schema generate`` -- wrote five
    artifacts and not the XSD, so following the documentation still left XML
    validation unusable. Fixed by openspec/changes/validate-xml-promise.
    """

    def test_raises_with_a_usable_message_when_the_xsd_is_absent(self, artifacts_dir: str) -> None:
        with pytest.raises(SchemaLoadError, match="XSD not found"):
            validate_xml(SIMPLE_XML, artifacts_dir=artifacts_dir)

    def test_bundled_artifacts_still_ship_no_xsd(self) -> None:
        """Unchanged and intended: the XSD is per-device, not per-release."""
        import junoscfg.validate as validate_pkg

        data = Path(validate_pkg.__file__).parent / "data"
        assert data.is_dir()
        assert list(data.glob("*.xsd")) == []

    def test_schema_generate_produces_what_validate_xml_needs(self, tmp_path: Path) -> None:
        """The documented workflow now actually works, end to end."""
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)
        out = tmp_path / "artifacts"

        runner = CliRunner()
        assert runner.invoke(main, ["schema", "generate", str(xsd), "-o", str(out)]).exit_code == 0
        assert (out / "junos-validated.xsd").is_file()

        assert validate_xml(SIMPLE_XML, artifacts_dir=str(out)).valid
        bad = validate_xml(
            "<configuration><system><bogus>x</bogus></system></configuration>",
            artifacts_dir=str(out),
        )
        assert not bad.valid


class TestSchemaMakedocIsGone:
    """``junoscfg schema makedoc`` was removed; it had never worked.

    ``cli.py`` imported ``junoscfg.validate.schema_doc``, a module that never
    existed in the tree or in git history, so every invocation raised
    ModuleNotFoundError while ``docs/guide/cli.md`` documented the command with
    worked examples. Removed by openspec/changes/remove-dead-makedoc as a
    declared ``cli`` surface break. This test replaces the one that pinned the
    crash, and fails against the merge base, where the command still exists.
    """

    def test_makedoc_is_not_a_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "makedoc", "--help"])

        assert result.exit_code != 0
        assert "No such command" in result.output

    def test_schema_help_does_not_offer_it(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "--help"])

        assert result.exit_code == 0
        assert "makedoc" not in result.output
        # the commands that do work are still there
        assert "generate" in result.output
        assert "info" in result.output


class TestSchemaGenerateWritesOutsideTheRepo:
    """``schema generate -o DIR`` creates the directory and overwrites in it.

    This is the reachable file-writing surface, and it is intended: the caller
    names the directory.  Pinned so that a change to what gets written, or to
    the silent overwrite, is visible.
    """

    def test_creates_dir_and_writes_its_artifacts(self, tmp_path: Path) -> None:
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
            "junos-validated.xsd",
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

    def test_rename_root_preserves_key_order(self, tmp_path: Path) -> None:
        """The new root is emitted first and configuration order is kept.

        This pinned the opposite until openspec/changes/yaml-key-order:
        cli.py called yaml.dump without sort_keys=False, so every edityaml
        command alphabetised its output while the code right above it said
        "Preserve key order by rebuilding dict".
        """
        cfg = self._yaml_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "rename-root", "--to", "junos_config", str(cfg)])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines[0] == "junos_config:"
        children = [
            ln.strip().rstrip(":") for ln in lines if ln.startswith("  ") and ln.endswith(":")
        ]
        # system comes first in examples/router1.conf; firewall is last.
        assert children[0] == "system"
        assert children.index("system") < children.index("firewall")

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


class TestXmlAndStructuredInputAgreeOnTheIr:
    """The same configuration gives one IR, whichever format it arrived in.

    It did not until openspec/changes/xml-ir-parity. ``KEY_ALIASES`` was
    consulted only in ``convert/input/set_input.py``, so ``<ieee-802.3ad>``
    stayed ``ieee-802.3ad`` where the structured path gave ``802.3ad``; and
    numeric leaves came back ``int`` from XML and ``str`` from structured.
    Set-side rendering hid both, which is why it went unnoticed.
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

    def test_the_two_irs_are_identical(self) -> None:
        from_conf, from_xml = self._irs()
        assert from_conf == from_xml

    def test_key_aliases_are_applied_on_the_xml_path(self) -> None:
        from_conf, from_xml = self._irs()
        conf_eo = from_conf["configuration"]["interfaces"]["interface"][2]["ether-options"]
        xml_eo = from_xml["configuration"]["interfaces"]["interface"][2]["ether-options"]
        assert list(conf_eo) == ["802.3ad"]
        assert list(xml_eo) == ["802.3ad"]

    def test_numeric_leaves_are_strings_from_both_paths(self) -> None:
        """Junos JSON is string-valued; the IR follows it."""
        from_conf, from_xml = self._irs()
        conf_uid = from_conf["configuration"]["system"]["login"]["user"][0]["uid"]
        xml_uid = from_xml["configuration"]["system"]["login"]["user"][0]["uid"]
        assert conf_uid == "2000" and isinstance(conf_uid, str)
        assert xml_uid == "2000" and isinstance(xml_uid, str)

    def test_set_output_still_agrees(self) -> None:
        from junoscfg import Format, convert_config

        conf = Path("examples/router1.conf").read_text()
        xml = Path("examples/router1.xml").read_text()
        assert convert_config(
            conf, from_format=Format.STRUCTURED, to_format=Format.SET
        ) == convert_config(xml, from_format=Format.XML, to_format=Format.SET)
