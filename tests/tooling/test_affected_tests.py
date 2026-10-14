"""The pre-commit hook runs the tests a change can break, chosen by one rule.

`tools/affected_tests.py` reads who imports whom from the source rather than
from a hand-kept map, so a package that starts importing another is covered
the day it does.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

import pytest
import yaml

from tests.support.paths import PROJECT_ROOT

# The tools read tach.toml with 3.11's tomllib, as the dev tooling they serve does.
pytest.importorskip("tomllib")


def _tool(name: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


affected = _tool("affected_tests")


@pytest.fixture(autouse=True, scope="module")
def _one_real_graph():
    """Build this repository's graph once; a test that moves ROOT builds its own."""
    build, real = affected.tooling_importers, {}

    def cached():
        if affected.ROOT != PROJECT_ROOT:
            return build()
        if not real:
            real.update(build())
        return real

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(affected, "tooling_importers", cached)
        yield


class TestASourceChangeSelectsItsPackageAndItsImporters:
    def test_a_feature_package_selects_itself_the_cli_and_the_contracts(self) -> None:
        assert affected.select(["src/junoscfg/audit/engine.py"]) == [
            "tests/contract/",
            "tests/unit/audit/",
            "tests/unit/cli/",
        ]

    def test_the_kernel_selects_every_package_that_imports_it(self) -> None:
        selection = affected.select(["src/junoscfg/display/constants.py"])
        for package in ("anonymize", "audit", "cli", "convert", "display", "validate"):
            assert f"tests/unit/{package}/" in selection

    def test_an_importer_is_found_through_another(self) -> None:
        # convert imports anonymize; audit imports convert, not anonymize.
        assert "tests/unit/audit/" in affected.select(["src/junoscfg/anonymize/rules/ip.py"])

    def test_a_package_nothing_else_imports_selects_only_itself(self) -> None:
        assert "tests/unit/convert/" not in affected.select(["src/junoscfg/edityaml/rules.py"])

    def test_every_selected_directory_exists(self) -> None:
        for path in affected.select(["src/junoscfg/input.py"]):
            assert (PROJECT_ROOT / path).is_dir(), path


class TestWithNoFilesTheChangeComesFromGit:
    def test_a_commit_selects_by_its_staged_files(self, monkeypatch) -> None:
        answers = {
            ("diff", "--cached", "--name-only", "--no-renames"): ["src/junoscfg/audit/engine.py"]
        }
        monkeypatch.setattr(affected, "_git", lambda *args: answers.get(args, []))
        assert affected.changed_files() == ["src/junoscfg/audit/engine.py"]

    def test_a_rename_lists_the_old_path_too(self, tmp_path, monkeypatch) -> None:
        # A commit hook exports GIT_DIR and GIT_INDEX_FILE for the real repository;
        # neither this scratch repository nor the selector may inherit them.
        for name in [name for name in os.environ if name.startswith("GIT_")]:
            monkeypatch.delenv(name)

        def git(*args: str) -> None:
            identity = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
            subprocess.run(["git", "-C", str(tmp_path), *identity, *args], check=True)

        git("init", "-q", "-b", "master")
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
        (tmp_path / "ci.yml").write_text("on: push\n")
        git("add", ".")
        git("commit", "-qm", "base")
        git("checkout", "-qb", "work")
        git("mv", "ci.yml", "main.yml")
        monkeypatch.setattr(affected, "ROOT", tmp_path)
        assert affected.changed_files() == ["ci.yml", "main.yml"]  # staged
        git("commit", "-qm", "rename")
        assert affected.changed_files() == ["ci.yml", "main.yml"]  # branch diff

    def test_with_nothing_staged_the_branch_and_the_working_tree_count(self, monkeypatch) -> None:
        def git(*args: str) -> list[str]:
            if args[0] == "merge-base":
                return ["abc123"]
            if args[:3] == ("diff", "--name-only", "--no-renames"):
                return ["src/junoscfg/edityaml/rules.py"]
            if args[0] == "status":
                return [" M tests/unit/audit/test_engine.py"]
            return []

        monkeypatch.setattr(affected, "_git", git)
        assert affected.changed_files() == [
            "src/junoscfg/edityaml/rules.py",
            "tests/unit/audit/test_engine.py",
        ]


class TestATestChangeSelectsItself:
    def test_a_test_file_selects_that_file(self) -> None:
        name = "tests/tooling/test_affected_tests.py"
        assert affected.select([name]) == [name]

    def test_a_conftest_selects_its_directory(self) -> None:
        assert affected.select(["tests/unit/audit/conftest.py"]) == ["tests/unit/audit/"]

    @pytest.mark.parametrize(
        "name",
        [
            "tests/conftest.py",
            "tests/support/paths.py",
            "src/junoscfg/__init__.py",
            "src/junoscfg/validate/data/junos-set.lark.gz",
            "uv.lock",
        ],
    )
    def test_shared_ground_selects_everything(self, name: str) -> None:
        assert affected.select([name]) == ["tests/"]

    def test_a_document_selects_nothing(self) -> None:
        assert (
            affected.select(
                [
                    "docs/guide/usage.md",
                    "README.md",
                    "tools/schema_verification.CONTRACT.md",
                ]
            )
            == []
        )


class TestRepositoryFilesATestReadsReceiveCoverage:
    """A test that reads a repository file names it from the project root; that
    file then selects the test, wherever it lives and whatever its suffix."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            (".github/workflows/ci.yml", ["tests/tooling/test_type_policy.py"]),
            ("docs/guide/cli-reference.md", ["tests/tooling/test_cli_reference.py"]),
            (".agent-ready/activation.json", ["tests/tooling/test_schema_verification.py"]),
            ("mkdocs.yml", ["tests/tooling/test_schema_verification.py"]),
        ],
    )
    def test_a_file_a_test_reads_selects_that_test(self, name, expected) -> None:
        assert affected.select([name]) == expected

    @pytest.mark.parametrize("name", ["examples/junoscfg-oracle.json", "examples/added.set"])
    def test_a_directory_shared_support_reads_selects_everything(self, name) -> None:
        assert affected.select([name]) == ["tests/"]

    @pytest.mark.parametrize(
        "name", ["src/junoscfg/audit/data/unused-types.yaml", "src/junoscfg/audit/data/words.txt"]
    )
    def test_package_data_selects_its_package(self, name) -> None:
        assert affected.select([name]) == affected.select(["src/junoscfg/audit/registry.py"])

    def test_a_marker_outside_every_package_selects_everything(self) -> None:
        assert affected.select(["src/junoscfg/py.typed"]) == ["tests/"]

    @pytest.mark.parametrize("name", [".gitignore", ".ignore", "data/request-xml-schema.xml"])
    def test_unclassified_configuration_keeps_tooling_coverage(self, name) -> None:
        assert affected.select([name]) == ["tests/tooling/"]

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("tests/integration_test.sh", ["tests/"]),
            ("tests/unit/cli/expected.txt", ["tests/unit/cli/"]),
            ("tests/unit/cli/expected.json", ["tests/unit/cli/"]),
        ],
    )
    def test_a_non_python_test_input_selects_its_directory(self, name, expected) -> None:
        assert affected.select([name]) == expected

    def test_documents_and_change_records_nobody_reads_select_nothing(self) -> None:
        assert (
            affected.select(
                [
                    "openspec/changes/example/metrics.json",
                    "openspec/changes/example/.openspec.yaml",
                    "openspec/specs/schema-pipeline/test-selection/spec.md",
                    "changelog.d/+example.misc.md",
                    ".agent-ready/update-receipt.json",
                    ".agents/skills/agent-ready-change/SKILL.md",
                    ".claude/skills/agent-ready-change/SKILL.md",
                    ".github/workflows/publish.yml",
                    ".copier-answers.yml",
                    "LICENSE",
                    "private_test_data/README.md",
                    "docs/reviews/example.md",
                    "src/junoscfg/validate/CONTRACT.md",
                    "tests/CONTRACT.md",
                ]
            )
            == []
        )


class TestSharedInputsReceiveCoverage:
    @pytest.mark.parametrize(
        "name",
        [
            "tools/schema-verification/policy.json",
            "tools/verification-costs.json",
            "tach.toml",
            ".pre-commit-config.yaml",
        ],
    )
    def test_tooling_inputs_select_tooling(self, name: str) -> None:
        assert affected.select([name]) == ["tests/tooling/"]

    @pytest.mark.parametrize(
        "name",
        ["tests/data/device/grammar-corpus.json", "tests/data/keyed-entries.xsd"],
    )
    def test_shared_data_selects_everything(self, name: str) -> None:
        assert affected.select([name]) == ["tests/"]

    def test_hook_runs_for_deletion_only_commits(self) -> None:
        config = yaml.safe_load((PROJECT_ROOT / ".pre-commit-config.yaml").read_text())
        hooks = [hook for repo in config["repos"] for hook in repo["hooks"]]
        hook = next(hook for hook in hooks if hook["id"] == "affected-tests")
        # pre-commit removes deleted paths before applying files/types filters.
        assert hook.get("always_run") is True
        assert hook["pass_filenames"] is False

    @pytest.mark.parametrize(
        "files, expected",
        [
            (
                ["tach.toml", "tests/tooling/test_affected_tests.py"],
                ["tests/tooling/"],
            ),
            (
                ["src/junoscfg/audit/engine.py", "tests/unit/audit/test_engine.py"],
                ["tests/contract/", "tests/unit/audit/", "tests/unit/cli/"],
            ),
        ],
    )
    def test_ancestor_selection_subsumes_descendants(self, files, expected) -> None:
        assert affected.select(files) == expected


class TestDeletedTestsRetainCoverage:
    @pytest.mark.parametrize(
        "name",
        ["tests/unit/audit/test_removed.py", "tests/unit/audit/gone/conftest.py"],
    )
    def test_deleted_test_selects_existing_ancestor(self, name: str) -> None:
        assert not (PROJECT_ROOT / name).exists()
        # A deleted module may have been a repository reader, so the reader
        # assertions run too.
        assert affected.select([name]) == [affected.READER_TESTS, "tests/unit/audit/"]


class TestTheDoorCheck:
    """`tools/check_test_doors.py` reads the doors from `tach.toml` and refuses
    every reach past one; checked here on a file of its own."""

    doors = _tool("check_test_doors")

    def _found(self, tmp_path, monkeypatch, source: str, layer: str = "unit/x") -> list[str]:
        tests = tmp_path / "tests"
        target = tests / layer / "test_probe.py"
        target.parent.mkdir(parents=True)
        target.write_text(source)
        monkeypatch.setattr(self.doors, "TESTS", tests)
        return self.doors.violations([target])

    def test_the_doors_are_the_tach_modules(self) -> None:
        assert {"junoscfg", "junoscfg.cli", "junoscfg.display", "junoscfg.validate"} <= (
            self.doors.doors()
        )

    def test_a_package_door_passes(self, tmp_path, monkeypatch) -> None:
        assert (
            self._found(tmp_path, monkeypatch, "from junoscfg.display import find_artifact\n") == []
        )

    @pytest.mark.parametrize(
        "source",
        [
            "from junoscfg.display.constants import KEY_ALIASES\n",
            "import junoscfg.validate.set_validator\n",
            "from junoscfg.display import _BUNDLED_DIR\n",
            "from junoscfg.display import constants\n",
            "x = validator._parser\n",
            'monkeypatch.setattr("junoscfg.convert.input.normalization.load_schema_tree", f)\n',
        ],
    )
    def test_a_reach_past_a_door_is_refused(self, tmp_path, monkeypatch, source: str) -> None:
        assert len(self._found(tmp_path, monkeypatch, source)) == 1

    def test_self_may_reach_its_own_helpers(self, tmp_path, monkeypatch) -> None:
        assert self._found(tmp_path, monkeypatch, "y = self._helper()\n") == []

    def test_contract_tests_are_held_to_the_named_surfaces(self, tmp_path, monkeypatch) -> None:
        found = self._found(
            tmp_path, monkeypatch, "from junoscfg.display import find_artifact\n", "contract"
        )
        assert len(found) == 1

    def test_a_surface_parameter_type_is_admitted(self, tmp_path, monkeypatch) -> None:
        source = "from junoscfg.anonymize import AnonymizeConfig\n"
        assert self._found(tmp_path, monkeypatch, source, "contract") == []


class TestToolConsumersDetermineSelection:
    @pytest.mark.parametrize(
        "tool, expected",
        [
            (
                "generate_cli_reference",
                [affected.READER_TESTS, "tests/tooling/test_cli_reference.py"],
            ),
            ("check_test_doors", ["tests/tooling/test_affected_tests.py"]),
            (
                "affected_tests",
                [
                    "tests/tooling/test_affected_execution.py",
                    "tests/tooling/test_affected_tests.py",
                ],
            ),
            ("compare_device_outputs", ["tests/tooling/test_compare_device_outputs.py"]),
            ("schema_content_worker", ["tests/"]),
            ("schema_verification", ["tests/"]),
            ("schema_dependencies", ["tests/"]),
        ],
    )
    def test_real_execution_consumers_are_selected(self, tool, expected):
        assert affected.select([f"tools/{tool}.py"]) == expected

    def test_bookkeeping_does_not_expand_a_tool_change(self):
        tool = "tools/generate_cli_reference.py"
        assert affected.select(
            [
                tool,
                "openspec/changes/example/metrics.md",
                "openspec/changes/example/workflow-events.jsonl",
            ]
        ) == affected.select([tool])

    @pytest.fixture
    def tree(self, tmp_path, monkeypatch):
        monkeypatch.setattr(affected, "ROOT", tmp_path)
        monkeypatch.setattr(affected, "TESTS", tmp_path / "tests")

        def write(path, source=""):
            target = tmp_path / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)

        write("tests/support/paths.py", "PROJECT_ROOT = Path(__file__).resolve().parents[2]")
        write("tools/leaf.py")
        write("tests/tooling/test_direct.py", "from tools.leaf import value")
        return write

    def test_transitive_imports_reach_tests_outside_tooling_and_terminate_cycles(self, tree):
        tree("tools/leaf.py", "from tools import middle")
        tree("tools/middle.py", "import tools.leaf")
        tree("tests/tooling/test_direct.py", "from tools.middle import value")
        tree("tests/unit/test_indirect.py", "from tests.tooling.test_direct import helper")
        tree("tests/unit/test_unrelated.py")
        assert affected.select(["tools/leaf.py"]) == [
            "tests/tooling/test_direct.py",
            "tests/unit/test_indirect.py",
        ]

    def test_relative_and_literal_dynamic_imports_are_dependencies(self, tree):
        tree("tools/middle.py", "from . import leaf")
        tree(
            "tests/unit/test_dynamic.py",
            'from importlib import import_module as load\nload("tools.middle")',
        )
        assert affected.select(["tools/leaf.py"]) == [
            "tests/tooling/test_direct.py",
            "tests/unit/test_dynamic.py",
        ]

    @pytest.mark.parametrize("shared", ["tests/conftest.py", "tests/support/helper.py"])
    def test_shared_consumers_select_the_full_suite(self, tree, shared):
        tree(shared, "import tools.leaf")
        assert affected.select(["tools/leaf.py"]) == ["tests/"]

    def test_nested_conftest_selects_its_directory(self, tree):
        tree("tests/unit/conftest.py", "import tools.leaf")
        assert affected.select(["tools/leaf.py"]) == [
            "tests/tooling/test_direct.py",
            "tests/unit/",
        ]

    @pytest.mark.parametrize(
        "source",
        [
            "def broken(",
            "import importlib\nimportlib.import_module(chosen_at_runtime)",
            "from importlib import import_module as load\nload(chosen_at_runtime)",
            "import importlib.util\nimportlib.util.spec_from_file_location(name, path)",
            "__import__(chosen_at_runtime)",
            "import runpy\nrunpy.run_path(chosen_at_runtime)",
        ],
    )
    def test_uncertain_discovery_never_silently_narrows(self, tree, source):
        tree("tests/unit/test_unknown.py", source)
        assert affected.select(["tools/leaf.py"]) == ["tests/"]

    @pytest.mark.parametrize(
        "reader",
        [
            'from tests.support.paths import PROJECT_ROOT\nPROJECT_ROOT / "docs" / "page.md"',
            "from tests.support.paths import PROJECT_ROOT as top\n"
            'ROOT = top\nROOT / "docs/page.md"',
            "from tools.pages import page",
        ],
    )
    def test_a_named_root_path_is_a_dependency(self, tree, reader):
        tree(
            "tools/pages.py",
            "from pathlib import Path\nHOME = Path(__file__).resolve().parents[1]\n"
            'page = HOME / "docs" / "page.md"\ndef text():\n    return page.read_text()',
        )
        tree("tests/tooling/test_pages.py", "import tools.pages")
        tree("tests/unit/test_reader.py", reader)
        tree("tests/unit/test_unrelated.py", 'Path("docs") / "page.md"')
        assert affected.select(["docs/page.md"]) == [
            "tests/tooling/test_pages.py",
            "tests/unit/test_reader.py",
        ]

    @pytest.mark.parametrize(
        "body, expected",
        [
            (
                "def test_reads():\n    PROJECT_ROOT / 'docs/page.md'",
                ["tests/tooling/test_owner.py"],
            ),
            (
                "class TestPage:\n"
                "    async def test_reads(self):\n        PROJECT_ROOT / 'docs/page.md'",
                ["tests/tooling/test_owner.py"],
            ),
            (
                "def helper():\n    return PROJECT_ROOT / 'docs/page.md'",
                ["tests/tooling/test_owner.py", "tests/unit/test_importer.py"],
            ),
        ],
    )
    def test_a_path_read_inside_a_test_reaches_no_importer(self, tree, body, expected):
        tree("tests/tooling/test_owner.py", f"from tests.support.paths import PROJECT_ROOT\n{body}")
        tree("tests/unit/test_importer.py", "from tests.tooling.test_owner import helper")
        assert affected.select(["docs/page.md"]) == expected

    def test_a_named_directory_covers_deleted_files_below_it(self, tree):
        tree(
            "tests/support/paths.py",
            "PROJECT_ROOT = Path(__file__).resolve().parents[2]\n"
            'EXAMPLES = PROJECT_ROOT / "examples"',
        )
        assert affected.select(["examples/gone.conf"]) == ["tests/"]

    @pytest.mark.parametrize(
        "reader",
        [
            "(PROJECT_ROOT / name).read_text()",
            "PROJECT_ROOT.joinpath(name)",
            "subprocess.run(['git', 'show'], cwd=PROJECT_ROOT)",
            "ROOT, OTHER = PROJECT_ROOT, 1",
            "def root():\n    return PROJECT_ROOT",
        ],
    )
    def test_a_root_wide_read_outside_tooling_reaches_every_outside_file(self, tree, reader):
        source = f"from tests.support.paths import PROJECT_ROOT\n{reader}"
        tree("tests/unit/test_dynamic.py", source)
        tree("tests/unit/test_importer.py", "from tests.unit.test_dynamic import helper")
        for name in ("docs/page.md", "openspec/changes/x/tasks.md", "settings.cfg"):
            assert "tests/unit/test_dynamic.py" in affected.select([name])
            assert "tests/unit/test_importer.py" in affected.select([name])

    @pytest.mark.parametrize(
        "reader",
        [
            "PROJECT_ROOT.joinpath('docs', 'page.md').read_text()",
            "list(PROJECT_ROOT.glob('docs/*.md'))",
            "PROJECT_ROOT.resolve() / 'docs/page.md'",
            "ROOT: Path = PROJECT_ROOT\nROOT / 'docs/page.md'",
            "Path(__file__).parents[2] / 'docs/page.md'",
            "Path(__file__).resolve().parent.parent.parent / 'docs/page.md'",
            "import tests.support.paths as p\np.PROJECT_ROOT / 'docs/page.md'",
            "from tests.support import paths\npaths.PROJECT_ROOT / 'docs/page.md'",
            "from tools.leaf import HOME\nHOME / 'docs/page.md'",
        ],
    )
    def test_other_spellings_of_a_root_read_are_found(self, tree, reader):
        tree("tools/leaf.py", "HOME = Path(__file__).resolve().parents[1]")
        tree("tests/unit/test_reader.py", f"from tests.support.paths import PROJECT_ROOT\n{reader}")
        assert affected.select(["docs/page.md"]) == ["tests/unit/test_reader.py"]

    def test_a_test_another_module_runs_keeps_its_importers(self, tree):
        tree(
            "tests/corpus/test_a.py",
            "from tests.support.paths import PROJECT_ROOT\n"
            "class TestA:\n    def test_y(self):\n        PROJECT_ROOT / 'docs/page.md'",
        )
        tree("tests/tooling/test_b.py", "from tests.corpus.test_a import TestA")
        assert affected.select(["docs/page.md"]) == [
            "tests/corpus/test_a.py",
            "tests/tooling/test_b.py",
        ]

    def test_an_unparsable_module_reaches_outside_files_without_escalating(self, tree):
        tree("tests/unit/test_broken.py", "def broken(")
        assert affected.select(["changelog.d/+x.misc.md"]) == ["tests/unit/test_broken.py"]
        assert affected.select(["tools/leaf.py"]) == ["tests/"]

    def test_a_dynamic_root_path_in_tooling_reaches_unclassified_inputs(self, tree):
        tree(
            "tests/tooling/test_dynamic.py",
            "from tests.support.paths import PROJECT_ROOT\n(PROJECT_ROOT / name).read_text()",
        )
        assert affected.select(["docs/page.md"]) == []
        assert affected.select(["settings.cfg"]) == ["tests/tooling/"]

    @pytest.mark.parametrize("path", ["tools/unmapped.py", "tools/deleted.py"])
    def test_missing_or_unmapped_tools_keep_broad_tooling_coverage(self, tree, path):
        if "unmapped" in path:
            tree(path)
        assert affected.select([path]) == ["tests/tooling/"]

    def test_discovery_is_fresh_after_an_import_changes(self, tree):
        assert affected.select(["tools/leaf.py"]) == ["tests/tooling/test_direct.py"]
        tree("tests/unit/test_added.py", "import tools.leaf")
        assert affected.select(["tools/leaf.py"]) == [
            "tests/tooling/test_direct.py",
            "tests/unit/test_added.py",
        ]

    @pytest.mark.parametrize(
        "path, old, new",
        [
            ("tests/tooling/test_affected_tests.py", 'f"{name}.py"', 'f"other_{name}.py"'),
            (
                "tests/tooling/test_compare_device_outputs.py",
                '"compare_device_outputs.py"',
                '"other.py"',
            ),
            ("tests/conftest.py", '"tools/schema_content_worker.py"', '"tools/other.py"'),
            (
                "tools/schema_verification.py",
                '"tools/schema_content_worker.py"',
                '"tools/other.py"',
            ),
        ],
    )
    def test_changed_audited_loaders_require_broad_coverage(self, tree, path, old, new):
        source = (PROJECT_ROOT / path).read_text()
        assert old in source
        tree(path, source.replace(old, new))
        assert affected.select(["tools/leaf.py"]) == ["tests/"]
