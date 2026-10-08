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

import gzip
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

    def test_a_directory_the_caller_chose_reports_an_error(self, tmp_path: Path) -> None:
        """A typo in `--artifacts` is a usage error, not a traceback.

        This asserted `None`, and `None` is what conversion then dereferenced:
        `set_input._merge_tokens` called `.get` on it and the user saw an
        `AttributeError` traceback. The knob that made a wrong directory
        reachable arrived in the same change, so the pin recorded the defect.
        """
        with pytest.raises(ValueError, match="junos-structure-tree.json"):
            load_schema_tree(tmp_path / "nothing-here")

    def test_only_the_bundled_directory_answers_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A package missing its own artifacts is not a path the user can fix."""
        import junoscfg.display.constants as c

        monkeypatch.setattr(c, "_BUNDLED_DIR", c._BUNDLED_DIR / "not-here")
        monkeypatch.setattr(c, "_schema_trees", {})
        assert c.load_schema_tree() is None


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


class TestCompressedAndPlainBothWork:
    """Artifacts ship gzipped; a directory generated before that still works.

    The set is 34.5 MB raw and 2.1 MB compressed — the two JSON schemas alone
    give back 20 MB at a 5% ratio, and the package goes 38 MB to 5.2 MB. But a
    developer who ran `schema generate` last week has the plain files, so every
    reader takes either, compressed first.
    """

    def test_the_compressed_form_is_preferred(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("plain")
        with gzip.open(tmp_path / "a.json.gz", "wt", encoding="utf-8") as h:
            h.write("compressed")
        found = constants.find_artifact(tmp_path, "a.json")
        assert found is not None
        assert constants.read_artifact_text(found) == "compressed"

    def test_a_plain_artifact_is_still_found(self, tmp_path: Path) -> None:
        (tmp_path / "a.json").write_text("plain")
        found = constants.find_artifact(tmp_path, "a.json")
        assert found is not None
        assert constants.read_artifact_text(found) == "plain"

    def test_a_missing_artifact_is_none(self, tmp_path: Path) -> None:
        assert constants.find_artifact(tmp_path, "nothing.json") is None

    def test_the_writer_compresses_when_the_name_says_to(self, tmp_path: Path) -> None:
        target = tmp_path / "out.json.gz"
        with constants.open_artifact_write(target) as handle:
            handle.write("payload")
        assert target.read_bytes()[:2] == b"\x1f\x8b", "not gzip"
        assert constants.read_artifact_text(target) == "payload"

    def test_the_writer_leaves_a_plain_name_plain(self, tmp_path: Path) -> None:
        target = tmp_path / "out.json"
        with constants.open_artifact_write(target) as handle:
            handle.write("payload")
        assert target.read_text() == "payload"

    def test_a_schema_tree_loads_from_either_form(self, tmp_path: Path) -> None:
        plain = tmp_path / "plain"
        plain.mkdir()
        (plain / constants.STRUCTURE_TREE_NAME).write_text(json.dumps({"c": {"p": {}}}))
        packed = tmp_path / "packed"
        packed.mkdir()
        with gzip.open(packed / f"{constants.STRUCTURE_TREE_NAME}.gz", "wt") as h:
            h.write(json.dumps({"c": {"z": {}}}))
        assert "p" in load_schema_tree(plain)["c"]
        assert "z" in load_schema_tree(packed)["c"]


class TestTheShippedArtifactsAreCompressed:
    def test_every_bundled_artifact_is_gzipped(self) -> None:
        shipped = sorted(p.name for p in constants._BUNDLED_DIR.iterdir() if p.is_file())
        assert shipped, "no bundled artifacts"
        assert all(n.endswith(".gz") for n in shipped), shipped

    def test_the_bundled_set_stays_small(self) -> None:
        """34.5 MB raw. A plain file slipping back in would be visible here."""
        total = sum(p.stat().st_size for p in constants._BUNDLED_DIR.iterdir() if p.is_file())
        assert total < 6 * 1024 * 1024, f"{total / 1048576:.1f} MB"
