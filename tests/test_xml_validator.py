"""Tests for XML validator."""

from __future__ import annotations

import tempfile

import pytest

from junoscfg.validate import SchemaLoadError
from junoscfg.validate.xml_validator import XmlValidator

# Minimal XSD for testing
MINIMAL_XSD = """\
<?xml version="1.0" encoding="UTF-8"?>
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
</xsd:schema>"""


@pytest.fixture
def xsd_path():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xsd", delete=False) as f:
        f.write(MINIMAL_XSD)
        return f.name


@pytest.fixture
def validator(xsd_path):
    return XmlValidator(xsd_path)


class TestXmlValidator:
    def test_valid_xml(self, validator):
        xml = "<configuration><system><host-name>router1</host-name></system></configuration>"
        result = validator.validate(xml)
        assert result.valid is True

    def test_invalid_xml_element(self, validator):
        xml = "<configuration><bogus/></configuration>"
        result = validator.validate(xml)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_xml_syntax_error(self, validator):
        result = validator.validate("<not<valid>")
        assert result.valid is False
        assert "syntax" in result.errors[0].message.lower()

    def test_empty_configuration(self, validator):
        xml = "<configuration/>"
        result = validator.validate(xml)
        assert result.valid is True

    def test_rpc_reply_unwrapped(self, validator):
        # rpc-reply without default namespace on inner elements
        xml = (
            "<rpc-reply>"
            "<configuration><system><host-name>r1</host-name></system></configuration>"
            "</rpc-reply>"
        )
        result = validator.validate(xml)
        assert result.valid is True

    def test_load_error(self):
        with pytest.raises(SchemaLoadError):
            XmlValidator("/nonexistent/path.xsd")
