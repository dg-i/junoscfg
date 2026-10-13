"""Execution relevance, including the checks-v0.17.1 updater-only release."""

import pytest

from tests.tooling.test_schema_dependency_trigger_challenge import (
    isolated_git_environment as isolated_git_environment,
)
from tests.tooling.test_schema_selection import (
    NEW,
    OLD,
    native_generation_context,
    producer_patterns,
)
from tools import schema_dependencies, schema_selection

qualified_context = native_generation_context


@pytest.mark.parametrize(
    "path,relevant",
    [
        (".agents/skills/agent-ready-change/SKILL.md", False),
        ("CLAUDE.md", False),
        ("src/junoscfg/validate/CONTRACT.md", False),
        ("tools/render_cli_reference.py", False),
        ("tools/affected_tests.py", False),
        (".pre-commit-config.yaml", False),
        ("mkdocs.yml", False),
        (".agent-ready/template.toml", False),
        (".agent-ready/update-receipt.json", False),
        ("docs/architecture/diagram.svg", False),
        ("openspec/schemas/agent-ready/schema.yaml", False),
        ("tools/schema_verification.py", True),
        ("src/junoscfg/validate/json_yaml_validator.py", True),
        ("src/junoscfg/validate/set_validator.py", True),
        ("src/junoscfg/input.py", True),
        ("src/junoscfg/convert/json.py", True),
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


@pytest.mark.parametrize(
    "fragment,relevant",
    [
        ("[tool.ruff]\nline-length = 100\n", False),
        ("[tool.template.assurance]\ndefault = 'economy'\n", False),
        ("[tool.pytest.ini_options]\naddopts = '-p schema_plugin'\n", True),
        ("[tool.unknown_schema_options]\nstrict = false\n", True),
    ],
)
def test_configuration_readers(fragment, relevant):
    before = '[project]\nname="junoscfg"\nversion="1"\n'
    assert schema_selection.classify("pyproject.toml", [], before, before + fragment) is relevant


@pytest.mark.parametrize(
    "name",
    ["tools/unrelated.py", ".agents/skills/example/SKILL.md", "tools/schema_selection.CONTRACT.md"],
)
def test_native_evidence_survives_unrelated_commits(qualified_context, name):
    from tests.tooling.test_schema_verification import commit_fixture, git

    root, base, patterns, metadata, engine, receipt = qualified_context
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# unrelated first edit\n")
    commit_fixture(root)
    assert schema_selection.established_context(root, base, patterns)
    base = git(root, "rev-parse", "HEAD").strip()
    path.write_text("# unrelated second edit\n")
    commit_fixture(root)
    assert schema_selection.established_context(root, base, patterns)


def test_transitive_tool_is_bound(qualified_context):
    from tests.tooling.test_schema_selection import write_source_boundary
    from tests.tooling.test_schema_verification import commit_fixture

    root, base, patterns, metadata, engine, receipt = qualified_context
    producer = root / "tools/schema_verification.py"
    producer.write_text("from tools.helper import build\n")
    helper = root / "tools/helper.py"
    helper.write_text("def build():\n    return 1\n")
    commit_fixture(root)
    write_source_boundary(root)
    assert schema_selection.verified_source_boundary(root)
    helper.write_text("def build():\n    return 2\n")
    assert not schema_selection.verified_source_boundary(root)


def test_missing_evidence_explains_reason(qualified_context, capsys):
    root, base, patterns, metadata, engine, receipt = qualified_context
    receipt.unlink()
    assert not schema_selection.established_context(root, base, patterns)
    assert "no successful native generation receipt" in capsys.readouterr().err


def test_real_source_closure_excludes_binary_artifacts():
    from agent_ready_checks import verification

    from tests.support.paths import PROJECT_ROOT

    sources = schema_selection.execution_sources(PROJECT_ROOT, verification.tracked(PROJECT_ROOT))
    assert "tools/schema_verification.py" in sources
    assert "tests/support/paths.py" in sources
    assert all(name.endswith(".py") for name in sources)
    assert "tools/affected_tests.py" not in sources


def test_explicit_input_overrides_documentation_category():
    assert schema_selection.classify("docs/schema-input.json", ["docs/schema-input.json"])


def test_transitive_tool_selects_qualification(qualified_context, capsys):
    from tests.tooling.test_schema_selection import write_source_boundary
    from tests.tooling.test_schema_verification import commit_fixture, git

    root, base, patterns, metadata, engine, receipt = qualified_context
    (root / "tools/schema_verification.py").write_text("from tools.helper import build\n")
    helper = root / "tools/helper.py"
    helper.write_text("def build():\n    return 1\n")
    commit_fixture(root)
    write_source_boundary(root)
    commit_fixture(root)
    base = git(root, "rev-parse", "HEAD").strip()
    helper.write_text("def build():\n    return 2\n")
    commit_fixture(root)
    schema_dependencies.write_dependencies(root)
    assert schema_selection.select(root, base)
    assert "tools/helper.py" in capsys.readouterr().err
