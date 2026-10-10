"""Tests for XSD extraction from NETCONF dumps."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from junoscfg.validate import extract_xsd

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_NETCONF = """<?xml version="1.0"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <capabilities><capability>urn:ietf:params:netconf:base:1.0</capability></capabilities>
</hello>
]]>]]>
<rpc-reply>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="system" type="xsd:string"/>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>
</rpc-reply>
"""


class TestExtractXsdFromString:
    def test_extracts_schema(self):
        result = extract_xsd(SAMPLE_NETCONF)
        assert result.startswith("<xsd:schema")
        assert result.endswith("</xsd:schema>")
        assert "configuration" in result

    def test_no_schema_raises(self):
        with pytest.raises(ValueError, match="No <xsd:schema>"):
            extract_xsd("<rpc-reply><ok/></rpc-reply>")

    def test_unclosed_schema_raises(self):
        with pytest.raises(ValueError, match="No closing"):
            extract_xsd("<xsd:schema><xsd:element name='x'/>")


class TestExtractXsdFromFile:
    def test_extracts_from_file(self, tmp_path: Path) -> None:
        dump = tmp_path / "dump.xml"
        dump.write_text(SAMPLE_NETCONF, encoding="utf-8")
        result = extract_xsd(dump)
        assert "<xsd:schema" in result
        assert "configuration" in result

    def test_no_schema_in_file_raises(self, tmp_path: Path) -> None:
        dump = tmp_path / "dump.xml"
        dump.write_text("<rpc-reply><ok/></rpc-reply>", encoding="utf-8")
        with pytest.raises(ValueError, match="No <xsd:schema>"):
            extract_xsd(dump)
