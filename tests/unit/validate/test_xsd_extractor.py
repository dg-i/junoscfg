"""Tests for XSD extraction from NETCONF dumps."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from junoscfg.validate.xsd_extractor import extract_xsd

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
    def test_extracts_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_NETCONF)
            f.flush()
            result = extract_xsd(Path(f.name))
        assert "<xsd:schema" in result
        assert "configuration" in result

    def test_no_schema_in_file_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<rpc-reply><ok/></rpc-reply>")
            f.flush()
            with pytest.raises(ValueError, match="No <xsd:schema>"):
                extract_xsd(Path(f.name))
