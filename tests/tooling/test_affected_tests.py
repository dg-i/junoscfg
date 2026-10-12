"""The pre-commit hook runs the tests a change can break, chosen by one rule.

`tools/affected_tests.py` reads who imports whom from the source rather than
from a hand-kept map, so a package that starts importing another is covered
the day it does.
"""

from __future__ import annotations

import importlib.util
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
        answers = {("diff", "--cached", "--name-only"): ["src/junoscfg/audit/engine.py"]}
        monkeypatch.setattr(affected, "_git", lambda *args: answers.get(args, []))
        assert affected.changed_files() == ["src/junoscfg/audit/engine.py"]

    def test_with_nothing_staged_the_branch_and_the_working_tree_count(self, monkeypatch) -> None:
        def git(*args: str) -> list[str]:
            if args[0] == "merge-base":
                return ["abc123"]
            if args[:2] == ("diff", "--name-only"):
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
                    "docs/guide/cli-reference.md",
                    "README.md",
                    "tools/schema_verification.CONTRACT.md",
                ]
            )
            == []
        )


class TestSharedInputsReceiveCoverage:
    @pytest.mark.parametrize(
        "name",
        [
            "tools/affected_tests.py",
            "tools/schema_verification.py",
            "tools/schema-verification/policy.json",
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
                ["tools/affected_tests.py", "tests/tooling/test_affected_tests.py"],
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
        assert affected.select([name]) == ["tests/unit/audit/"]


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
