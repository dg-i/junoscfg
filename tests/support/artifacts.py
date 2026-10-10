"""The one minimal set of validation artifacts: a two-element schema and grammar.

Enough for a validator to load and to tell a known element from an unknown
one, and nothing else; a test that needs the shipped artifacts uses the
session fixtures in ``tests/conftest.py`` instead.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

MINIMAL_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "configuration": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "object",
                    "properties": {"host-name": {}},
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
        "system": {
            "type": "object",
            "properties": {"host-name": {}},
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
            "properties": {
                "system": {
                    "type": "object",
                    "properties": {"host-name": {}},
                    "additionalProperties": False,
                    "patternProperties": {"^_ansible_": {}, "^_meta_": {}},
                },
            },
            "additionalProperties": False,
            "patternProperties": {"^_ansible_": {}, "^_meta_": {}},
        },
        "system": {
            "type": "object",
            "properties": {"host-name": {}},
            "additionalProperties": False,
            "patternProperties": {"^_ansible_": {}, "^_meta_": {}},
        },
    },
}

MINIMAL_GRAMMAR = """\
start: SET configuration
configuration: "system" system
system: "host-name" VALUE

SET: "set"
VALUE: /\\S+/
QUOTED: /"[^"]*"/
QUOTED_OR_VALUE: QUOTED | VALUE

%import common.WS
%ignore WS
"""

MINIMAL_META = {
    "junos_version": "21.4R0",
    "generated_at": "2026-01-01T00:00:00Z",
    "generator_version": "0.1.0",
}


def make_artifacts_dir(path: Path) -> None:
    """Write minimal validation artifacts into *path*."""
    with open(path / "junos-json-schema.json", "w") as f:
        json.dump(MINIMAL_JSON_SCHEMA, f)
    with open(path / "junos-yaml-schema.json", "w") as f:
        json.dump(MINIMAL_YAML_SCHEMA, f)
    with open(path / "junos-set.lark", "w") as f:
        f.write(MINIMAL_GRAMMAR)
    with open(path / "junos-schema-meta.json", "w") as f:
        json.dump(MINIMAL_META, f)
