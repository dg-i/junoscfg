"""Tests for XML validator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from junoscfg.validate import SchemaLoadError, XmlValidator
from tests.support.artifacts import MINIMAL_XSD

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def xsd_path(tmp_path: Path) -> Path:
    path = tmp_path / "minimal.xsd"
    path.write_text(MINIMAL_XSD, encoding="utf-8")
    return path


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
