"""Tests for XSD → SchemaNode parser."""

from __future__ import annotations

import pytest

from junoscfg.validate.xsd_parser import parse_xsd


def _minimal_xsd(body: str) -> str:
    """Wrap element definitions in a minimal XSD schema."""
    return f"""\
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:junos="http://xml.juniper.net/junos/21.4R0/junos"
            elementFormDefault="qualified">
  {body}
</xsd:schema>"""


class TestParseBasic:
    def test_simple_leaf(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        assert root.name == "configuration"
        hn = root.children.get("host-name")
        assert hn is not None
        assert hn.is_leaf is True

    def test_presence_container(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="no-remote-trace" minOccurs="0">
                  <xsd:complexType/>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        nrt = root.children.get("no-remote-trace")
        assert nrt is not None
        assert nrt.is_presence is True

    def test_no_configuration_raises(self):
        xsd = _minimal_xsd("""
        <xsd:element name="other">
          <xsd:complexType/>
        </xsd:element>
        """)
        with pytest.raises(ValueError, match="configuration"):
            parse_xsd(xsd)


class TestFlags:
    def test_identifier_flag(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="name">
                  <xsd:annotation>
                    <xsd:appinfo>
                      <flag>identifier</flag>
                      <identifier/>
                    </xsd:appinfo>
                  </xsd:annotation>
                  <xsd:simpleType>
                    <xsd:restriction base="xsd:string"/>
                  </xsd:simpleType>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        name = root.children.get("name")
        assert name is not None
        assert name.is_key is True
        assert "identifier" in name.flags

    def test_mandatory_flag(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="required-field">
                  <xsd:annotation>
                    <xsd:appinfo>
                      <flag>mandatory</flag>
                    </xsd:appinfo>
                  </xsd:annotation>
                  <xsd:simpleType>
                    <xsd:restriction base="xsd:string"/>
                  </xsd:simpleType>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        rf = root.children.get("required-field")
        assert rf is not None
        assert rf.is_mandatory is True

    def test_nokeyword_flag(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="filename" minOccurs="0">
                  <xsd:annotation>
                    <xsd:appinfo>
                      <flag>nokeyword</flag>
                    </xsd:appinfo>
                  </xsd:annotation>
                  <xsd:simpleType>
                    <xsd:restriction base="xsd:string"/>
                  </xsd:simpleType>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        fn = root.children.get("filename")
        assert fn is not None
        assert "nokeyword" in fn.flags


class TestEnumsAndPatterns:
    def test_enumerations(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="level" minOccurs="0">
                  <xsd:simpleType>
                    <xsd:restriction base="xsd:string">
                      <xsd:enumeration value="error"/>
                      <xsd:enumeration value="warning"/>
                      <xsd:enumeration value="info"/>
                    </xsd:restriction>
                  </xsd:simpleType>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        level = root.children.get("level")
        assert level is not None
        assert level.enums == ["error", "warning", "info"]

    def test_match_pattern(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="host-name" minOccurs="0">
                  <xsd:annotation>
                    <xsd:appinfo>
                      <match>
                        <pattern>^[a-z]+$</pattern>
                        <message>Must be lowercase</message>
                      </match>
                    </xsd:appinfo>
                  </xsd:annotation>
                  <xsd:simpleType>
                    <xsd:restriction base="xsd:string"/>
                  </xsd:simpleType>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        hn = root.children.get("host-name")
        assert hn is not None
        assert hn.pattern == "^[a-z]+$"
        assert hn.pattern_negated is False

    def test_negated_pattern(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="filename" minOccurs="0">
                  <xsd:annotation>
                    <xsd:appinfo>
                      <match>
                        <pattern>![/ %]</pattern>
                      </match>
                    </xsd:appinfo>
                  </xsd:annotation>
                  <xsd:simpleType>
                    <xsd:restriction base="xsd:string"/>
                  </xsd:simpleType>
                </xsd:element>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        fn = root.children.get("filename")
        assert fn is not None
        assert fn.pattern == "[/ %]"
        assert fn.pattern_negated is True


class TestTypeResolution:
    def test_named_complex_type(self):
        xsd = _minimal_xsd("""
        <xsd:complexType name="my-system-type">
          <xsd:sequence>
            <xsd:choice minOccurs="0" maxOccurs="unbounded">
              <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
              <xsd:element name="domain-name" type="xsd:string" minOccurs="0"/>
            </xsd:choice>
          </xsd:sequence>
        </xsd:complexType>
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="system" type="my-system-type" minOccurs="0"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        system = root.children.get("system")
        assert system is not None
        assert system.type_ref == "my-system-type"
        assert "host-name" in system.children
        assert "domain-name" in system.children

    def test_string_wrapper_type_is_leaf(self):
        xsd = _minimal_xsd("""
        <xsd:complexType name="hostname">
          <xsd:simpleContent>
            <xsd:extension base="xsd:string"/>
          </xsd:simpleContent>
        </xsd:complexType>
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="domain-name" type="hostname" minOccurs="0"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        dn = root.children.get("domain-name")
        assert dn is not None
        assert dn.is_leaf is True
        assert dn.type_ref == "hostname"


class TestCardinality:
    def test_unbounded_is_list(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="interfaces" minOccurs="0" maxOccurs="unbounded"
                             type="xsd:string"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        ifaces = root.children.get("interfaces")
        assert ifaces is not None
        assert ifaces.is_list is True

    def test_default_not_list(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="system" type="xsd:string" minOccurs="0"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        system = root.children.get("system")
        assert system is not None
        assert system.is_list is False


class TestSkipElements:
    def test_skips_undocumented_ref(self):
        xsd = _minimal_xsd("""
        <xsd:element name="undocumented">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:any namespace="##any" processContents="skip"/>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element ref="undocumented" minOccurs="0"/>
                <xsd:element name="system" type="xsd:string" minOccurs="0"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        assert "undocumented" not in root.children
        assert "system" in root.children

    def test_skips_apply_advanced(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="apply-advanced" type="xsd:string" minOccurs="0"/>
                <xsd:element name="system" type="xsd:string" minOccurs="0"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        assert "apply-advanced" not in root.children
        assert "system" in root.children


class TestDollarPrefix:
    def test_dollar_prefix_is_leaf(self):
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="$junos-interface-ifd-name" type="xsd:string"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        node = root.children.get("$junos-interface-ifd-name")
        assert node is not None
        assert node.is_leaf is True
