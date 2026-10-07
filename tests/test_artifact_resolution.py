"""One rule for where the artifacts live.

Conversion and validation used to answer this separately. `JunosValidator`
took an argument, then `JUNOSCFG_ARTIFACTS`, then the bundle, and documented
it; `display.constants` hardcoded the bundled path and cached it in a
process-wide singleton. So the environment variable switched validation and
was silently ignored by conversion — the larger feature, and the one the
downstream Ansible collection renders through.

A documented option that works for half a tool is worse than one that does not
exist, because the documentation is true and nobody checks the other half.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from junoscfg.display import (
    artifacts_dir,
    constants,
    load_schema_tree,
    resolve_artifacts_dir,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _clean_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test may leak an override or a cache entry into the next."""
    monkeypatch.delenv("JUNOSCFG_ARTIFACTS", raising=False)
    before = dict(constants._schema_trees)
    yield
    constants._schema_trees.clear()
    constants._schema_trees.update(before)


def _tree_at(directory: Path, marker: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / constants.STRUCTURE_TREE_NAME).write_text(json.dumps({"c": {marker: {"l": True}}}))
    return directory


class TestResolutionOrder:
    def test_the_bundle_is_the_default(self) -> None:
        assert resolve_artifacts_dir() == constants._BUNDLED_DIR

    def test_the_environment_beats_the_bundle(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(tmp_path))
        assert resolve_artifacts_dir() == tmp_path

    def test_an_invocation_override_beats_the_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(tmp_path / "env"))
        with artifacts_dir(tmp_path / "flag"):
            assert resolve_artifacts_dir() == tmp_path / "flag"

    def test_an_explicit_argument_beats_everything(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(tmp_path / "env"))
        with artifacts_dir(tmp_path / "flag"):
            assert resolve_artifacts_dir(tmp_path / "arg") == tmp_path / "arg"


class TestConversionHonoursIt:
    """The half that used to ignore every knob."""

    def test_the_environment_switches_the_schema_tree(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _tree_at(tmp_path, "from-the-environment")
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(tmp_path))
        tree = load_schema_tree()
        assert tree is not None
        assert "from-the-environment" in tree["c"]

    def test_a_missing_directory_is_none_not_a_crash(self, tmp_path: Path) -> None:
        assert load_schema_tree(tmp_path / "nothing-here") is None


class TestTwoSchemasCoexist:
    """The old singleton could not hold two.

    An Ansible play touching two device roles would have got whichever tree
    was loaded first, silently, for the rest of the process.
    """

    def test_each_directory_keeps_its_own_tree(self, tmp_path: Path) -> None:
        a = _tree_at(tmp_path / "a", "schema-a")
        b = _tree_at(tmp_path / "b", "schema-b")
        assert "schema-a" in load_schema_tree(a)["c"]
        assert "schema-b" in load_schema_tree(b)["c"]
        # and again, from the cache, in the other order
        assert "schema-b" in load_schema_tree(b)["c"]
        assert "schema-a" in load_schema_tree(a)["c"]


class TestTheOverrideIsScoped:
    """A setter with no reset leaked one invocation's schema into the next.

    That is not hypothetical: the first version of this change used one, and
    109 conversion tests failed because `CliRunner` runs the CLI in the test
    process. The Ansible collection has the same shape — the library is
    imported into a long-lived `ansible-playbook`.
    """

    def test_the_override_is_restored_on_exit(self, tmp_path: Path) -> None:
        before = resolve_artifacts_dir()
        with artifacts_dir(tmp_path):
            assert resolve_artifacts_dir() == tmp_path
        assert resolve_artifacts_dir() == before

    def test_it_is_restored_even_when_the_block_raises(self, tmp_path: Path) -> None:
        before = resolve_artifacts_dir()
        with pytest.raises(RuntimeError), artifacts_dir(tmp_path):
            raise RuntimeError("as a command exiting non-zero would")
        assert resolve_artifacts_dir() == before


class TestValidationSharesTheResolver:
    def test_the_validator_resolves_the_same_way(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from junoscfg.validate.validator import JunosValidator

        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(tmp_path))
        assert JunosValidator()._artifacts_dir == resolve_artifacts_dir()
