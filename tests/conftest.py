"""Shared fixtures for Junoser tests."""

from __future__ import annotations

import json
import os
import subprocess
import warnings
from pathlib import Path
from types import SimpleNamespace

import pytest

from . import schema_data

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

    Checked in order: the ``JUNOSCFG_XSD_SOURCE`` environment variable, the
    newest dump under ``private_test_data/schemas/``, then any ``*.xsd`` left
    directly in ``private_test_data/``. This used to be a hardcoded
    ``../xsd/config-24.4.xsd`` beside the repository, which existed on one
    machine and nowhere else, so ``--regen-schema`` skipped silently in any
    clean clone and the message named a path nobody could act on.
    """
    override = os.environ.get(XSD_SOURCE_ENV)
    if override:
        return Path(override).expanduser()
    synced = schema_data.available()
    if synced:
        return synced[-1]
    candidates = sorted(XSD_SOURCE_DIR.glob("*.xsd"))
    return candidates[-1] if candidates else None


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--schema",
        action="store_true",
        default=False,
        help="run tests that need a device XSD dump in private_test_data/schemas/",
    )
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
            f"Put a NETCONF XSD dump in "
            f"{schema_data.SCHEMA_DIR.relative_to(PROJECT_ROOT)}/ (gitignored, "
            f"as new.xsd to have it named for you) or set {XSD_SOURCE_ENV}; "
            "private_test_data/README.md says how to capture one.",
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


# ----------------------------------------------------------------------
# Schema-backed tests
#
# A user needs no device data. A developer should sync one or more NETCONF
# XSD dumps into private_test_data/schemas/; the tests marked `schema` then
# run against each. Parsing one dump costs about three minutes, so they are
# opt-in rather than part of the inner loop.
# ----------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "schema: needs a device XSD dump in private_test_data/schemas/; run with --schema",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--schema"):
        return
    skip = pytest.mark.skip(reason="needs --schema and a dump in private_test_data/schemas/")
    for item in items:
        if "schema" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session", params=[p.name for p in schema_data.available()])
def schema_dump(request: pytest.FixtureRequest) -> Path:
    """One synced device dump. Parametrised over every dump found."""
    return schema_data.SCHEMA_DIR / str(request.param)


@pytest.fixture(scope="session")
def parsed_schema(schema_dump: Path) -> object:
    """The dump parsed into a SchemaNode tree, with fixes applied.

    Session-scoped and parametrised, so each dump is parsed once however many
    tests use it.
    """
    from junoscfg.validate.xsd_extractor import extract_xsd
    from junoscfg.validate.xsd_fixes import apply_all_fixes, get_fix_count
    from junoscfg.validate.xsd_parser import parse_xsd

    xsd_text = extract_xsd(schema_dump.read_text(encoding="utf-8", errors="replace"))
    tree = parse_xsd(xsd_text)
    applied = apply_all_fixes(tree)
    return SimpleNamespace(
        path=schema_dump,
        version=schema_data.read_version(schema_dump),
        xsd_text=xsd_text,
        tree=tree,
        fixes_applied=applied,
        fixes_registered=get_fix_count(),
    )
