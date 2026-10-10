"""Tests for XSD → SchemaNode parser."""

from __future__ import annotations

import pytest

from junoscfg.validate import parse_xsd


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

    def test_a_numeric_max_occurs_is_list(self):
        """Any `maxOccurs` but 1 is a list, as the XSD states.

        `forwarding-classes class` is `maxOccurs="16"` and `commit peers`
        `maxOccurs="3"`; read as single containers, a second entry replaced
        the first without a word (phase-6 review, challenge A).
        """
        xsd = _minimal_xsd("""
        <xsd:element name="configuration">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:choice minOccurs="0" maxOccurs="unbounded">
                <xsd:element name="class" minOccurs="0" maxOccurs="16">
                  <xsd:complexType>
                    <xsd:sequence>
                      <xsd:element name="name" type="xsd:string">
                        <xsd:annotation><xsd:appinfo>
                          <flag>identifier</flag><flag>nokeyword</flag>
                        </xsd:appinfo></xsd:annotation>
                      </xsd:element>
                      <xsd:element name="queue-num" type="xsd:string" minOccurs="0"/>
                    </xsd:sequence>
                  </xsd:complexType>
                </xsd:element>
                <xsd:element name="source-port" minOccurs="0" maxOccurs="32"
                             type="xsd:string"/>
                <xsd:element name="host-name" minOccurs="0" maxOccurs="1"
                             type="xsd:string"/>
              </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        """)
        root = parse_xsd(xsd)
        assert root.children["class"].is_list is True
        assert root.children["source-port"].is_list is True
        assert root.children["host-name"].is_list is False


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


def _entry_keys(found: dict) -> tuple:
    """The kernel's answer, imported late so a missing helper fails one assertion."""
    from junoscfg.display import entry_keys

    return entry_keys(found)


class TestEveryDeclaredChildIsKept:
    """The parser keeps every element a sequence declares, in declared order.

    `_build_from_complex_type` kept a sequence's first choice and dropped the
    rest: the identifier elements -- `list-type` and `list-name` among them,
    which left `as-path-neighbors` a childless presence list -- and any second
    choice, route-filter's actions among them. Spec:
    `openspec/changes/identifier-key-fields/specs/schema-pipeline/entry-key-fields`.
    Observed through the structure tree the parsed XSD is written as, so the
    tests hold whatever the parser stores the keys in.
    """

    @staticmethod
    def _tree(tmp_path) -> dict:
        from tests.support.keyed_entries import KEYED_XSD, structure_tree

        return structure_tree(KEYED_XSD, tmp_path)

    def test_two_identifiers_beside_a_comment_only_choice(self, tmp_path) -> None:
        from tests.support.keyed_entries import node

        tree = self._tree(tmp_path)
        for slot in ("as-path-neighbors", "as-path-origins"):
            for parent in (("from",), ("term", "from")):
                found = node(tree, "policy-options", "policy-statement", *parent, slot)
                assert list(found["c"]) == ["list-type", "list-name"], (parent, slot)
                assert found["k"] == ["list-type", "list-name"]
                assert found.get("L") is True
                assert "p" not in found, "still a childless presence list"
                assert _entry_keys(found) == ("list-type", "list-name")
                list_type = found["c"]["list-type"]
                assert tree["_enums"][list_type["e"]] == ["as-list", "as-list-group"]

    def test_one_identifier_other_than_name(self, tmp_path) -> None:
        from tests.support.keyed_entries import node

        server = node(self._tree(tmp_path), "system", "ntp", "server")
        assert list(server["c"]) == ["address", "version", "prefer"]
        assert server["k"] == ["address"]
        assert "name" not in server["c"]
        assert _entry_keys(server) == ("address",)

    def test_name_is_a_key_child(self, tmp_path) -> None:
        from tests.support.keyed_entries import node

        tree = self._tree(tmp_path)
        for path in (
            ("policy-options", "policy-statement"),
            ("policy-options", "policy-statement", "term"),
            ("policy-options", "community"),
            ("event-options", "policy"),
        ):
            found = node(tree, *path)
            assert next(iter(found["c"])) == "name", path
            assert found["c"]["name"].get("l") is True
            assert "k" not in found, f"{path}: `k` is omitted where the key is name"
            assert _entry_keys(found) == ("name",)

    def test_a_second_choice_is_kept(self, tmp_path) -> None:
        from tests.support.keyed_entries import node

        tree = self._tree(tmp_path)
        route_filter = node(
            tree, "policy-options", "policy-statement", "term", "from", "route-filter"
        )
        assert list(route_filter["c"]) == ["address", "exact", "orlonger", "accept", "reject"]
        for action in ("accept", "reject"):
            assert route_filter["c"][action].get("p") is True

    def test_an_identifier_choice_is_one_key_field(self, tmp_path) -> None:
        from tests.support.keyed_entries import node

        tree = self._tree(tmp_path)
        term = ("policy-options", "policy-statement", "term")
        route_filter = node(tree, *term, "from", "route-filter")
        assert route_filter["k"] == ["address", ["exact", "orlonger"]]
        assert _entry_keys(route_filter) == ("address", ("exact", "orlonger"))

        community = node(tree, *term, "then", "community")
        assert list(community["c"]) == ["add", "delete", "community-name"]
        assert community["k"] == [["add", "delete"], "community-name"]
        assert _entry_keys(community) == (("add", "delete"), "community-name")

        match = node(tree, "event-options", "policy", "attributes-match")
        assert list(match["c"]) == ["from-event-attribute", "condition", "to-event-attribute-value"]
        assert match["k"] == ["from-event-attribute", "condition", "to-event-attribute-value"]
        assert tree["_enums"][match["c"]["condition"]["e"]] == ["equals", "starts-with", "matches"]

    def test_a_simple_content_key_keeps_anonymization_type_only(self, tmp_path) -> None:
        from tests.support.keyed_entries import node

        route_address = node(
            self._tree(tmp_path),
            "policy-options",
            "policy-statement",
            "term",
            "from",
            "route-filter",
            "address",
        )
        assert route_address["atr"] == "ipprefix"
        assert "tr" not in route_address
