"""Shared fixtures for Junoser tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
XSD_SOURCE = PROJECT_ROOT / "data" / "xml-schema-from-device.xml"
ARTIFACT_DIR = PROJECT_ROOT / "src" / "junoscfg" / "validate" / "data"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--regen-schema",
        action="store_true",
        default=False,
        help="Regenerate bundled schema artifacts from the device XSD before tests.",
    )


@pytest.fixture(scope="session", autouse=True)
def _regenerate_schema_artifacts(request: pytest.FixtureRequest) -> None:
    """Regenerate bundled schema artifacts from the device XSD before any tests.

    Only runs when ``--regen-schema`` is passed.  This ensures XSD fixes
    in xsd_fixes.py are reflected in the bundled junos-structure-tree.json
    and other artifacts.
    """
    if not request.config.getoption("--regen-schema"):
        return

    if not XSD_SOURCE.exists():
        pytest.skip(f"XSD source not found: {XSD_SOURCE}")
        return

    subprocess.run(
        [
            "uv",
            "run",
            "junoscfg",
            "schema",
            "generate",
            str(XSD_SOURCE),
            "-o",
            str(ARTIFACT_DIR),
        ],
        check=True,
        capture_output=True,
    )

    # Invalidate the cached schema tree so tests pick up the fresh one
    import junoscfg.display.constants as constants

    constants._schema_tree = None


# Minimal validation artifacts shared across test modules.
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


@pytest.fixture
def artifacts_dir(tmp_path: Path) -> str:
    """Temporary directory populated with minimal validation artifacts."""
    make_artifacts_dir(tmp_path)
    return str(tmp_path)


@pytest.fixture
def examples_dir() -> Path:
    """Path to the examples directory with test data."""
    return EXAMPLES_DIR


@pytest.fixture
def set_lines(examples_dir: Path) -> str:
    """Expected 'display set' output from the example router config."""
    return (examples_dir / "load_ox_conf.set").read_text()


@pytest.fixture
def json_config(examples_dir: Path) -> str:
    """Example router config in JSON format."""
    return (examples_dir / "load_ox_conf.json").read_text()


@pytest.fixture
def xml_config(examples_dir: Path) -> str:
    """Example router config in XML format."""
    return (examples_dir / "load_ox_conf.xml").read_text()


@pytest.fixture
def structured_config(examples_dir: Path) -> str:
    """Example router config in structured (curly-brace) format."""
    return (examples_dir / "load_ox_conf.conf").read_text()


@pytest.fixture
def yaml_config(json_config: str) -> str:
    """Example router config in hyphenated YAML format (generated from JSON)."""
    from junoscfg import Format, convert_config

    return convert_config(json_config, from_format=Format.JSON, to_format=Format.YAML)
