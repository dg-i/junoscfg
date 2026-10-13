"""Options, markers and the session fixtures every layer shares.

Helpers and data live in ``tests/support/``; see ``tests/CONTRACT.md``.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from junoscfg.display import find_artifact
from tests.support import schema_data
from tests.support.artifacts import make_artifacts_dir
from tests.support.paths import ARTIFACT_DIR, EXAMPLES
from tests.support.regen import (
    REGEN_SOURCE_EXIT,
    XSD_SOURCE_ENV,
    XsdSourceError,
    find_xsd_source,
    regenerate_from,
)

if TYPE_CHECKING:
    from pathlib import Path


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
        "--device-grammar",
        action="store_true",
        default=False,
        help=(
            "run the shipped grammar over every set line a device printed (minutes); "
            "the default run takes the covering subset in tests/data/device/grammar-corpus.json"
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
    from junoscfg.validate import SetValidator

    return SetValidator(find_artifact(ARTIFACT_DIR, "junos-set.lark"))


@pytest.fixture(scope="session")
def bundled_tree() -> dict:
    """The shipped structure tree (13 MB of JSON), read once.

    Through `load_schema_tree`, the door conversion uses, so a test reads the
    tree conversion reads. Treat it as read-only: it is shared by the session
    and by conversion's own cache.
    """
    from junoscfg.display import load_schema_tree

    tree = load_schema_tree()
    assert tree is not None, "the package ships no structure tree"
    return tree


@pytest.fixture(scope="session")
def bundled_validator() -> object:
    """The shipped JSON and YAML schemas, loaded once.

    `tests/contract/test_round_trip_validates.py` needs the same artifacts the CLI uses,
    so it must resolve them the way everything else does rather than naming a
    path -- the one place that named its own went red the day they shipped
    gzipped.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=str(ARTIFACT_DIR))


@pytest.fixture
def json_config() -> str:
    """The example configuration as the vMX printed it with `| display json`.

    `examples/junoscfg-oracle.json`: a device capture, so it carries lines
    junoscfg gets wrong today, each recorded in `known-differences.json`.
    """
    return (EXAMPLES / "junoscfg-oracle.json").read_text(encoding="utf-8")


@pytest.fixture
def xml_config() -> str:
    """The example configuration as the vMX printed it with `| display xml`.

    `examples/junoscfg-oracle.xml`; its recorded differences are in
    `known-differences.json`.
    """
    return (EXAMPLES / "junoscfg-oracle.xml").read_text(encoding="utf-8")


@pytest.fixture
def structured_config() -> str:
    """The example configuration as the vMX printed it with `show` (curly).

    `examples/junoscfg-oracle.conf`; its recorded differences are in
    `known-differences.json`.
    """
    return (EXAMPLES / "junoscfg-oracle.conf").read_text(encoding="utf-8")


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
    if not config.getoption("--device-grammar"):
        skip = pytest.mark.skip(reason="needs --device-grammar; minutes through the grammar")
        for item in items:
            if "device_grammar" in item.keywords:
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
    from junoscfg.validate import apply_all_fixes, extract_xsd, get_fix_count, parse_xsd

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


@pytest.fixture
def schema_content_check(request: pytest.FixtureRequest):
    """Run the existing checks, or verify template-owned proof during qualification."""
    from tools.schema_verification import check_content

    def check(path: Path, operation: str) -> None:
        check_content(request.config, path, operation)

    return check
