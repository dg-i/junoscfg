"""Shared fixtures for Junoser tests."""

from __future__ import annotations

import json
import os
import subprocess
import warnings
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
ARTIFACT_DIR = PROJECT_ROOT / "src" / "junoscfg" / "validate" / "data"

# Where --regen-schema looks for the device XSD. It cannot be committed: it is
# a NETCONF dump from a real device at a specific Junos release, which is both
# large and operator data. private_test_data/ is the documented, gitignored
# home for exactly that.
XSD_SOURCE_ENV = "JUNOSCFG_XSD_SOURCE"
XSD_SOURCE_DIR = PROJECT_ROOT / "private_test_data"


def find_xsd_source() -> Path | None:
    """The device XSD to regenerate from, or None when there is none.

    Checked in order: the ``JUNOSCFG_XSD_SOURCE`` environment variable, then
    the newest ``*.xsd`` in ``private_test_data/``. This used to be a hardcoded
    ``../xsd/config-24.4.xsd`` beside the repository, which existed on one
    machine and nowhere else, so ``--regen-schema`` skipped silently in any
    clean clone and the message named a path nobody could act on.
    """
    override = os.environ.get(XSD_SOURCE_ENV)
    if override:
        return Path(override).expanduser()
    candidates = sorted(XSD_SOURCE_DIR.glob("*.xsd"))
    return candidates[-1] if candidates else None


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

    xsd_source = find_xsd_source()
    if xsd_source is None or not xsd_source.exists():
        # Warn and carry on. This used to call pytest.skip() from a
        # session-scoped autouse fixture, which skipped all 1414 tests and
        # exited 0 -- so `pytest --regen-schema`, the command AGENTS.md tells
        # you to run before committing, reported success having tested nothing
        # in any clone without the XSD.
        warnings.warn(
            "--regen-schema: no device XSD found, so the bundled artifacts "
            "were not regenerated. The suite ran against the committed ones. "
            f"Put a NETCONF XSD dump in {XSD_SOURCE_DIR.relative_to(PROJECT_ROOT)}/ "
            f"(gitignored) or set {XSD_SOURCE_ENV} to its path; "
            "docs/guide/validation.md says how to capture one.",
            stacklevel=2,
        )
        return

    subprocess.run(
        [
            "uv",
            "run",
            "junoscfg",
            "schema",
            "generate",
            str(xsd_source),
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
    """Expected 'display set' output from the synthetic example config."""
    return (examples_dir / "router1.set").read_text()


@pytest.fixture
def json_config(examples_dir: Path) -> str:
    """Synthetic example config in JSON format."""
    return (examples_dir / "router1.json").read_text()


@pytest.fixture
def xml_config(examples_dir: Path) -> str:
    """Synthetic example config in XML format."""
    return (examples_dir / "router1.xml").read_text()


@pytest.fixture
def structured_config(examples_dir: Path) -> str:
    """Synthetic example config in structured (curly-brace) format."""
    return (examples_dir / "router1.conf").read_text()


@pytest.fixture
def yaml_config(json_config: str) -> str:
    """Synthetic example config in hyphenated YAML format (generated from JSON)."""
    from junoscfg import Format, convert_config

    return convert_config(json_config, from_format=Format.JSON, to_format=Format.YAML)
