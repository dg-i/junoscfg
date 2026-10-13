"""Execution relevance, including the checks-v0.17.1 updater-only release."""

import pytest

from tests.tooling.test_schema_selection import NEW, OLD, producer_patterns
from tools import schema_dependencies, schema_selection


@pytest.mark.parametrize(
    "path,relevant",
    [
        (".agents/skills/agent-ready-change/SKILL.md", False),
        ("CLAUDE.md", False),
        ("tools/render_cli_reference.py", False),
        ("tools/affected_tests.py", False),
        (".pre-commit-config.yaml", False),
        ("mkdocs.yml", False),
        ("tools/schema_verification.py", True),
        ("src/junoscfg/validate/json_yaml_validator.py", True),
        ("src/junoscfg/validate/set_validator.py", True),
        ("src/junoscfg/input.py", True),
        ("src/junoscfg/display/constants.py", True),
        ("tests/support/paths.py", True),
    ],
)
def test_execution_path_selection(path, relevant):
    assert schema_selection.classify(path, producer_patterns(), OLD, NEW) is relevant


def lock():
    return """version = 1
requires-python = ">=3.10"
[[package]]
name = "junoscfg"
version = "1"
source = {editable = "."}
[[package]]
name = "lxml"
version = "1"
source = {registry = "https://example.invalid"}
dependencies = [{name = "transitive"}]
[[package]]
name = "transitive"
version = "1"
source = {registry = "https://example.invalid"}
[[package]]
name = "ruff"
version = "1"
source = {registry = "https://example.invalid"}
[[package]]
name = "agent-ready-checks"
version = "0.17.0"
source = {git = "https://example.invalid/checks?tag=checks-v0.17.0"}
"""


@pytest.mark.parametrize(
    "package,relevant", [("lxml", True), ("transitive", True), ("ruff", False)]
)
def test_dependency_projection(package, relevant):
    before = lock()
    after = before.replace(
        f'name = "{package}"\nversion = "1"', f'name = "{package}"\nversion = "2"'
    )
    assert (
        schema_dependencies.fingerprint_text(before) != schema_dependencies.fingerprint_text(after)
    ) is relevant


def test_updater_release_projection():
    before = lock()
    # checks-v0.17.0..0.17.1: update.py is the only changed runtime module.
    after = before.replace("0.17.0", "0.17.1")
    assert schema_dependencies.fingerprint_text(before) == schema_dependencies.fingerprint_text(
        after
    )
