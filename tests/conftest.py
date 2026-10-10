"""Shared fixtures for Junoser tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from junoscfg.display import find_artifact, read_artifact_text

from . import jvd_data, schema_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
ARTIFACT_DIR = PROJECT_ROOT / "src" / "junoscfg" / "validate" / "data"

# Where --regen-schema looks for the device XSD. It cannot be committed: it is
# a NETCONF dump from a real device at a specific Junos release, which is both
# large and operator data. private_test_data/ is the documented, gitignored
# home for exactly that.
XSD_SOURCE_ENV = "JUNOSCFG_XSD_SOURCE"
XSD_SOURCE_DIR = PROJECT_ROOT / "private_test_data"
#: pytest keeps 0 to 5 for itself; this one means "no dump to regenerate from".
REGEN_SOURCE_EXIT = 7
_TRAIN_RE = re.compile(r"^(\d+\.\d+)")


class XsdSourceError(Exception):
    """No single dump answers ``--regen-schema``; the message says what would."""


def shipped_release_train(artifact_dir: Path = ARTIFACT_DIR) -> str:
    """The release train of the bundled artifacts: ``25.2`` for ``25.2R0``.

    The metadata records the namespace release the dump declared, which is
    the train's base; a dump's own header names the full release, such as
    ``25.2R2-S1.5``. The train is what the two share.
    """
    meta = find_artifact(artifact_dir, "junos-schema-meta.json")
    if meta is None:
        raise XsdSourceError(f"no junos-schema-meta.json under {artifact_dir}")
    version = str(json.loads(read_artifact_text(meta)).get("junos_version", ""))
    match = _TRAIN_RE.match(version)
    if match is None:
        raise XsdSourceError(
            f"the bundled metadata names no release train ({version!r}), so no dump can "
            f"be matched to it; name the dump to rebuild from with {XSD_SOURCE_ENV}"
        )
    return match.group(1)


def _dumps(directory: Path) -> list[Path]:
    """Every ``.xsd`` file in *directory*, left as they are: a lookup renames nothing."""
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.xsd") if p.is_file())


def find_xsd_source(
    *,
    train: str | None = None,
    schemas_dir: Path | None = None,
    legacy_dir: Path | None = None,
    override: str | None = None,
) -> Path:
    """The dump to regenerate from: *override*, or the one dump of the shipped train.

    This used to be whichever dump sorted newest under
    ``private_test_data/schemas/``, so the documented pre-commit step would
    have replaced the shipped artifacts with whatever a developer had synced
    last, as a side effect of a file name. The release is an explicit choice:
    the dump whose release matches the bundled metadata's train, read from the
    dump's own header, or the one ``JUNOSCFG_XSD_SOURCE`` names, which is how
    the release moves on purpose. Anything else raises, with the reason,
    rather than picking. ``None`` for *override* means the variable is unset;
    set and empty is an error, not a fallback.
    """
    if override is not None:
        path = Path(override).expanduser()
        if not override.strip() or not path.is_file():
            raise XsdSourceError(f"{XSD_SOURCE_ENV}={override!r} is not a file")
        if schema_data.read_version(path) == "unknown":
            raise XsdSourceError(
                f"{XSD_SOURCE_ENV}={override} declares no Junos release in its header; "
                "artifacts built from it could not be matched to a dump again"
            )
        return path
    train = train or shipped_release_train()
    schemas_dir = schemas_dir or schema_data.SCHEMA_DIR
    legacy_dir = XSD_SOURCE_DIR if legacy_dir is None else legacy_dir
    candidates = _dumps(schemas_dir) + _dumps(legacy_dir)
    releases = {p: schema_data.read_version(p) for p in candidates}
    # The train followed by anything but another digit: 25.2R2-S1.5, 25.2X75-D10,
    # 25.2R2-S1.5-EVO, and not 25.20R1.
    wanted = re.compile(rf"{re.escape(train)}(?![0-9])")
    matching = [p for p in candidates if wanted.match(releases[p])]
    if len(matching) == 1:
        return matching[0]

    def _show(p: Path) -> str:
        where = p.relative_to(PROJECT_ROOT) if p.is_relative_to(PROJECT_ROOT) else p
        return f"{where} ({releases[p]})"

    if not matching:
        found = ", ".join(_show(p) for p in candidates) or "none"
        raise XsdSourceError(
            f"--regen-schema: no dump of the shipped release {train} under {schemas_dir} "
            f"or beside it; found: {found}. Sync the shipped release's dump, or name "
            f"another with {XSD_SOURCE_ENV} to move the release on purpose."
        )
    raise XsdSourceError(
        f"--regen-schema: {len(matching)} dumps of release {train}: "
        + ", ".join(_show(p) for p in matching)
        + f". Name one with {XSD_SOURCE_ENV}."
    )


def regenerate_from(xsd_source: Path) -> None:
    """Rebuild the bundled artifacts from *xsd_source* and drop the cached tree."""
    subprocess.run(
        ["uv", "run", "junoscfg", "schema", "generate", str(xsd_source), "-o", str(ARTIFACT_DIR)],
        check=True,
        capture_output=True,
    )
    from junoscfg.display import forget_loaded_artifacts

    forget_loaded_artifacts()


def pytest_sessionstart(session: pytest.Session) -> None:
    """Regenerate before collection when ``--regen-schema`` is passed.

    Before collection, so a run that selects no test, or only collects, still
    regenerates or stops; as a fixture this ran at the first test's setup and
    a ``-k`` that matched nothing reported success having done nothing. On an
    error the run stops with the reason and ``REGEN_SOURCE_EXIT``. It used to
    warn and run the suite against the committed artifacts, and before that
    skip every test and exit 0, each a way of reporting success for a rebuild
    that never happened.
    """
    if not session.config.getoption("--regen-schema"):
        return
    try:
        xsd_source = find_xsd_source(override=os.environ.get(XSD_SOURCE_ENV))
    except XsdSourceError as err:
        pytest.exit(str(err), returncode=REGEN_SOURCE_EXIT)
    regenerate_from(xsd_source)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--schema",
        action="store_true",
        default=False,
        help="run tests that need a device XSD dump in private_test_data/schemas/",
    )
    parser.addoption(
        "--jvd",
        action="store_true",
        default=False,
        help=(
            "run tests against Juniper's published jvd corpus; clones it under "
            "private_test_data/ unless JUNOSCFG_JVD_PATH names a clone"
        ),
    )
    parser.addoption(
        "--regen-schema",
        action="store_true",
        default=False,
        help=(
            "regenerate the bundled artifacts before collection, from the one dump of "
            "the shipped release under private_test_data/schemas/ or the dump "
            "JUNOSCFG_XSD_SOURCE names; with none, two, or an unusable override the "
            "run stops with the reason and exit code 7"
        ),
    )


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


@pytest.fixture(scope="session")
def bundled_set_validator() -> object:
    """The shipped grammar, compiled once for the whole session.

    Compiling it costs about four seconds, and more than one module needs it:
    the corpus tier and the negative tests that pin what the grammar must keep
    rejecting. A module-scoped fixture paid for it twice.
    """
    from junoscfg.validate.set_validator import SetValidator

    return SetValidator(find_artifact(ARTIFACT_DIR, "junos-set.lark"))


@pytest.fixture(scope="session")
def bundled_validator() -> object:
    """The shipped JSON and YAML schemas, loaded once.

    `tests/test_round_trip_validates.py` needs the same artifacts the CLI uses,
    so it must resolve them the way everything else does rather than naming a
    path -- the one place that named its own went red the day they shipped
    gzipped.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=str(ARTIFACT_DIR))


@pytest.fixture
def project_root() -> Path:
    """The repository root, for tests that read a committed example."""
    return PROJECT_ROOT


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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not config.getoption("--schema"):
        skip = pytest.mark.skip(reason="needs --schema and a dump in private_test_data/schemas/")
        for item in items:
            if "schema" in item.keywords:
                item.add_marker(skip)
    if not config.getoption("--jvd"):
        skip = pytest.mark.skip(reason="needs --jvd; clones Juniper's jvd corpus")
        for item in items:
            if "jvd" in item.keywords:
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


# ----------------------------------------------------------------------
# Juniper's published jvd corpus. Cloned at test time rather than vendored:
# it is someone else's repository, it is large, and a stale copy would be
# worse than none. Converting all of it costs about three minutes, so it is
# opt-in like the schema tier.
# ----------------------------------------------------------------------


@pytest.fixture(scope="session")
def jvd_corpus() -> Path:
    """The jvd checkout, cloned on first use. Skips if it cannot be had."""
    root = jvd_data.ensure_corpus()
    if root is None:
        pytest.skip(
            f"could not obtain the jvd corpus; clone {jvd_data.CLONE_URL} and set "
            f"{jvd_data.PATH_ENV}, or check network access"
        )
    if not jvd_data.configs(root):
        pytest.skip(f"no .conf files under {root}")
    return root
