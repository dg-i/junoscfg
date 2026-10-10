"""The one minimal set of validation artifacts, and the way to the shipped ones.

The minimal set is enough for a validator to load and to tell a known element
from an unknown one, and nothing else: a JSON and a YAML schema that know
`system host-name`, a grammar that knows `system host-name`, `system services
ssh` and `interfaces description`, and an XSD that knows `system host-name`. A
test that needs the shipped artifacts uses the session fixtures in
``tests/conftest.py``, or `shipped` and `shipped_text` here for the files
themselves.

Every validator wraps a document without a `configuration` key in one before
validating, so the schemas name `system` under `configuration` only: a
top-level `system` would let a bare document pass without the wrapping.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from junoscfg.display import find_artifact, read_artifact_text
from tests.support.paths import ARTIFACT_DIR

if TYPE_CHECKING:
    from pathlib import Path

_SYSTEM = {
    "type": "object",
    "properties": {"host-name": {}},
    "additionalProperties": False,
}
#: Keys a YAML document may carry anywhere: Ansible variables and metadata.
_YAML_KEYS = {"patternProperties": {"^_ansible_": {}, "^_meta_": {}}}

MINIMAL_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "configuration": {
            "type": "object",
            "properties": {"system": _SYSTEM},
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}

MINIMAL_YAML_SCHEMA = {
    **MINIMAL_JSON_SCHEMA,
    "properties": {
        "configuration": {
            "type": "object",
            "properties": {"system": {**_SYSTEM, **_YAML_KEYS}},
            "additionalProperties": False,
            **_YAML_KEYS,
        },
    },
}

MINIMAL_GRAMMAR = """\
start: SET configuration
configuration: "system" system | "interfaces" interfaces
system: "host-name" VALUE | "services" services
services: "ssh"
interfaces: "description" QUOTED_OR_VALUE

SET: "set"
VALUE: /\\S+/
QUOTED: /"[^"]*"/
QUOTED_OR_VALUE: QUOTED | VALUE

%import common.WS
%ignore WS
"""

#: Not written by `make_artifacts_dir`: no artifact set ships an XSD, and
#: `validate_xml` reports that absence (`TestValidateXmlNeedsACleanedXsd`).
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
</xsd:schema>
"""

MINIMAL_META = {
    "junos_version": "21.4R0",
    "generated_at": "2026-01-01T00:00:00Z",
    "generator_version": "0.1.0",
}


@dataclass(frozen=True)
class MinimalArtifacts:
    """Where `make_artifacts_dir` wrote each file."""

    directory: Path
    json_schema: Path
    yaml_schema: Path
    grammar: Path
    meta: Path


def make_artifacts_dir(path: Path) -> MinimalArtifacts:
    """Write the minimal validation artifacts into *path*."""
    written = MinimalArtifacts(
        directory=path,
        json_schema=path / "junos-json-schema.json",
        yaml_schema=path / "junos-yaml-schema.json",
        grammar=path / "junos-set.lark",
        meta=path / "junos-schema-meta.json",
    )
    written.json_schema.write_text(json.dumps(MINIMAL_JSON_SCHEMA), encoding="utf-8")
    written.yaml_schema.write_text(json.dumps(MINIMAL_YAML_SCHEMA), encoding="utf-8")
    written.grammar.write_text(MINIMAL_GRAMMAR, encoding="utf-8")
    written.meta.write_text(json.dumps(MINIMAL_META), encoding="utf-8")
    return written


def shipped(name: str) -> Path:
    """The shipped artifact *name*, compressed or not, as the package resolves it."""
    path = find_artifact(ARTIFACT_DIR, name)
    assert path is not None, f"the package ships no {name}"
    return path


def shipped_text(name: str) -> str:
    """The text of the shipped artifact *name*."""
    return read_artifact_text(shipped(name))
