"""Keyed-entry inputs every layer shares: the as-list, route-filter and community shapes.

Synthetic values only, as AGENTS.md names them: AS 64496-64511, `SAMPLE-*`
names, 198.51.100.0/24. The shapes are the ones a vMX on 23.2R2-S7.5 showed
for the same statements (`tests/data/captures/keyed-entries-*`).

Every helper reaches junoscfg through a public door -- `convert_config`, the
structure tree an XSD produces, the artefacts `ArtifactBuilder` writes -- so
the tests prove behaviour and not the shape of the code that delivers it.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from junoscfg import Format, convert_config
from junoscfg.display import read_artifact_text
from junoscfg.validate import ArtifactBuilder, parse_xsd, write_structure_tree
from tests.support.paths import TEST_DATA as DATA

if TYPE_CHECKING:
    from pathlib import Path

KEYED_XSD = (DATA / "keyed-entries.xsd").read_text(encoding="utf-8")

#: A schema with `name`-keyed lists only, for the byte-identity pins.
NAME_KEYED_XSD = """\
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:junos="http://xml.juniper.net/junos/25.2R0/junos"
            elementFormDefault="qualified">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice minOccurs="0" maxOccurs="unbounded">
          <xsd:element name="policy-options" minOccurs="0">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:choice minOccurs="0" maxOccurs="unbounded">
                  <xsd:element name="policy-statement" minOccurs="0" maxOccurs="unbounded">
                    <xsd:complexType>
                      <xsd:sequence>
                        <xsd:element name="name" type="xsd:string">
                          <xsd:annotation><xsd:appinfo>
                            <flag>identifier</flag><identifier/>
                          </xsd:appinfo></xsd:annotation>
                        </xsd:element>
                        <xsd:choice minOccurs="0" maxOccurs="unbounded">
                          <xsd:element ref="undocumented" minOccurs="0"/>
                          <xsd:element name="description" minOccurs="0" type="xsd:string"/>
                          <xsd:element name="term" minOccurs="0" maxOccurs="unbounded">
                            <xsd:complexType>
                              <xsd:sequence>
                                <xsd:element name="name" type="xsd:string">
                                  <xsd:annotation><xsd:appinfo>
                                    <flag>identifier</flag><identifier/>
                                  </xsd:appinfo></xsd:annotation>
                                </xsd:element>
                                <xsd:choice minOccurs="0" maxOccurs="unbounded">
                                  <xsd:element name="accept" minOccurs="0">
                                    <xsd:complexType/>
                                  </xsd:element>
                                  <xsd:element name="metric" minOccurs="0" type="xsd:string"/>
                                </xsd:choice>
                              </xsd:sequence>
                            </xsd:complexType>
                          </xsd:element>
                        </xsd:choice>
                      </xsd:sequence>
                    </xsd:complexType>
                  </xsd:element>
                  <xsd:element name="community" minOccurs="0" maxOccurs="unbounded">
                    <xsd:annotation><xsd:appinfo><flag>oneliner</flag></xsd:appinfo></xsd:annotation>
                    <xsd:complexType>
                      <xsd:sequence>
                        <xsd:element name="name" type="xsd:string">
                          <xsd:annotation><xsd:appinfo>
                            <flag>identifier</flag><identifier/>
                          </xsd:appinfo></xsd:annotation>
                        </xsd:element>
                        <xsd:choice minOccurs="0" maxOccurs="unbounded">
                          <xsd:element name="members" minOccurs="0" maxOccurs="unbounded"
                                       type="xsd:string"/>
                          <xsd:element name="invert-match" minOccurs="0">
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
</xsd:schema>
"""

POLICY = "set policy-options policy-statement SAMPLE-POLICY"
TERM = f"{POLICY} term T1"


def structure_tree(xsd: str, tmp: Path) -> dict[str, Any]:
    """The structure tree *xsd* produces, read back as the JSON it ships as."""
    path = tmp / "junos-structure-tree.json"
    write_structure_tree(parse_xsd(xsd), str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def build_artifacts(xsd: str, tmp: Path) -> Path:
    """Every artefact `schema generate` writes for *xsd*, in *tmp*."""
    ArtifactBuilder().build_from_xsd(xsd, tmp)
    return tmp


def artifact_json(directory: Path, name: str) -> dict[str, Any]:
    """A generated JSON artefact, compressed or not."""
    gz = directory / f"{name}.gz"
    return json.loads(read_artifact_text(gz if gz.is_file() else directory / name))


def node(tree: dict[str, Any], *path: str) -> dict[str, Any]:
    """The structure-tree node at *path* below the root."""
    current = tree
    for name in path:
        current = current["c"][name]
    return current


def ir(source: str, fmt: Format) -> dict[str, Any]:
    """The IR a reader gives, as `convert_config` renders it to JSON."""
    rendered = convert_config(source, from_format=fmt, to_format=Format.JSON, validate=False)
    return json.loads(rendered)["configuration"]


def set_ir(*lines: str) -> dict[str, Any]:
    """The IR of display-set lines."""
    return ir("\n".join(lines) + "\n", Format.SET)


def term_from(config: dict[str, Any]) -> dict[str, Any]:
    """`from` of term T1 of SAMPLE-POLICY."""
    policy = config["policy-options"]["policy-statement"][0]
    return policy["term"][0]["from"]


def term_then(config: dict[str, Any]) -> dict[str, Any]:
    """`then` of term T1 of SAMPLE-POLICY."""
    policy = config["policy-options"]["policy-statement"][0]
    return policy["term"][0]["then"]


def to_set(source: str, fmt: Format) -> list[str]:
    """Display-set lines, without the trailing blank."""
    rendered = convert_config(source, from_format=fmt, to_format=Format.SET, validate=False)
    return [line for line in rendered.splitlines() if line.strip()]


def as_json(config: dict[str, Any]) -> str:
    """A configuration wrapped as a device's `| display json`."""
    return json.dumps({"configuration": config})
