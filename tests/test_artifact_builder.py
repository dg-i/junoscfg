"""Tests for ArtifactBuilder pipeline."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from junoscfg.validate.artifact_builder import ArtifactBuilder

SAMPLE_XSD = """\
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:junos="http://xml.juniper.net/junos/21.4R0/junos"
            elementFormDefault="qualified">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice minOccurs="0" maxOccurs="unbounded">
          <xsd:element name="system" minOccurs="0">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:choice minOccurs="0" maxOccurs="unbounded">
                  <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
                  <xsd:element name="services" minOccurs="0">
                    <xsd:complexType>
                      <xsd:sequence>
                        <xsd:choice minOccurs="0" maxOccurs="unbounded">
                          <xsd:element name="ssh" minOccurs="0">
                            <xsd:complexType/>
                          </xsd:element>
                        </xsd:choice>
                      </xsd:sequence>
                    </xsd:complexType>
                  </xsd:element>
                </xsd:choice>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:choice>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>"""

SAMPLE_NETCONF = f"""\
<rpc-reply>
{SAMPLE_XSD}
</rpc-reply>
"""


class TestArtifactBuilder:
    def test_build_from_xsd_creates_all_artifacts(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)

            assert "json-schema" in artifacts
            assert "yaml-schema" in artifacts
            assert "lark-grammar" in artifacts
            assert "metadata" in artifacts

            for path in artifacts.values():
                assert Path(path).exists()

    def test_json_schema_is_valid_json(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            with open(artifacts["json-schema"]) as f:
                schema = json.load(f)
            assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
            assert "configuration" in schema["properties"]

    def test_yaml_schema_has_pattern_properties(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            with open(artifacts["yaml-schema"]) as f:
                schema = json.load(f)
            config = schema["properties"]["configuration"]
            assert "patternProperties" in config

    def test_lark_grammar_has_start_rule(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            grammar = Path(artifacts["lark-grammar"]).read_text()
            assert "start:" in grammar
            assert "SET" in grammar

    def test_metadata_has_stats(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            with open(artifacts["metadata"]) as f:
                meta = json.load(f)
            assert "junos_version" in meta
            assert "stats" in meta
            assert meta["stats"]["total_nodes"] > 0

    def test_build_from_netconf_dump(self):
        builder = ArtifactBuilder()
        # Write NETCONF dump to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_NETCONF)
            netconf_path = f.name
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build(netconf_path, tmpdir)
            assert len(artifacts) == 5
            for path in artifacts.values():
                assert Path(path).exists()

    def test_output_dir_created_if_missing(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "subdir" / "deep"
            artifacts = builder.build_from_xsd(SAMPLE_XSD, new_dir)
            assert new_dir.exists()
            assert len(artifacts) == 5
