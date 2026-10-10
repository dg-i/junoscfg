"""`junoscfg schema generate` and `schema info`: arguments, output and exit codes.

The plumbing only. What `ArtifactBuilder` writes for an XSD is tested in
`tests/unit/validate/test_artifact_builder.py`, and what the validator reads
from the artifacts in `tests/unit/validate/test_validator.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner, Result

from junoscfg.cli import main
from junoscfg.display import read_artifact_text
from tests.support.artifacts import MINIMAL_XSD

if TYPE_CHECKING:
    from pathlib import Path

#: What `schema generate` writes, compressed, and nothing else: no XSD among them.
ARTIFACTS = {
    "junos-structure-tree.json.gz",
    "junos-json-schema.json.gz",
    "junos-yaml-schema.json.gz",
    "junos-set.lark.gz",
    "junos-schema-meta.json.gz",
}


def run(args: list[str]) -> Result:
    return CliRunner().invoke(main, args)


def write_xsd(tmp_path: Path, text: str = MINIMAL_XSD) -> Path:
    xsd = tmp_path / "mini.xsd"
    xsd.write_text(text, encoding="utf-8")
    return xsd


class TestTheSchemaGroup:
    """``schema`` offers `generate` and `info`; ``makedoc`` is gone.

    ``cli.py`` imported ``junoscfg.validate.schema_doc``, a module that never
    existed in the tree or in git history, so every `makedoc` raised
    ModuleNotFoundError while ``docs/guide/cli.md`` documented it with worked
    examples. Removed by openspec/changes/remove-dead-makedoc as a declared
    ``cli`` surface break; these replace the test that pinned the crash.
    """

    def test_makedoc_is_not_a_command(self) -> None:
        result = run(["schema", "makedoc", "--help"])
        assert result.exit_code != 0
        assert "No such command" in result.output

    def test_the_help_offers_generate_and_info_and_not_makedoc(self) -> None:
        result = run(["schema", "--help"])
        assert result.exit_code == 0
        assert "makedoc" not in result.output
        assert "generate" in result.output
        assert "info" in result.output


class TestSchemaGenerate:
    """``schema generate XSD -o DIR`` creates *DIR* and overwrites in it.

    The reachable file-writing surface, and intended: the caller names the
    directory. Pinned so that a change to what gets written, or to the silent
    overwrite, is visible.
    """

    def test_the_directory_is_created_and_holds_the_artifacts(self, tmp_path: Path) -> None:
        """Five artifacts and no XSD: `validate_xml` needs a cleaned one, which
        nothing produces (`TestValidateXmlNeedsACleanedXsd`)."""
        out = tmp_path / "does-not-exist-yet"
        result = run(["schema", "generate", str(write_xsd(tmp_path)), "-o", str(out)])
        assert result.exit_code == 0, result.output
        assert result.stdout.endswith("Artifacts generated successfully.\n")
        assert {p.name for p in out.iterdir()} == ARTIFACTS

    def test_existing_artifacts_are_overwritten_without_prompt(self, tmp_path: Path) -> None:
        out = tmp_path / "artifacts"
        out.mkdir()
        stale = out / "junos-schema-meta.json.gz"
        stale.write_text("STALE")  # deliberately not valid gzip
        result = run(["schema", "generate", str(write_xsd(tmp_path)), "-o", str(out)])
        assert result.exit_code == 0, result.output
        # Artifacts ship compressed, so a readable one proves it was rewritten:
        # the stale bytes are not valid gzip and would raise.
        assert "junos_version" in read_artifact_text(stale)

    def test_a_file_without_an_xsd_exits_three(self, tmp_path: Path) -> None:
        out = tmp_path / "artifacts"
        result = run(["schema", "generate", str(write_xsd(tmp_path, "no schema")), "-o", str(out)])
        assert result.exit_code == 3
        assert result.stdout == ""
        assert result.stderr.startswith("Error: No <xsd:schema> found in ")

    def test_the_output_directory_is_required(self, tmp_path: Path) -> None:
        result = run(["schema", "generate", str(write_xsd(tmp_path))])
        assert result.exit_code == 2
        assert "Missing option '-o' / '--output-dir'" in result.stderr

    def test_a_source_that_does_not_exist_exits_two(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.xsd"
        result = run(["schema", "generate", str(missing), "-o", str(tmp_path / "out")])
        assert result.exit_code == 2
        assert "does not exist" in result.stderr


class TestSchemaInfo:
    """``schema info`` prints the version and date the artifacts were built from."""

    def test_the_version_and_date_are_printed(self, artifacts_dir: str) -> None:
        result = run(["schema", "info", "--artifacts", artifacts_dir])
        assert result.exit_code == 0
        assert result.stdout == ("Schema version: 21.4R0\nGenerated at:   2026-01-01T00:00:00Z\n")

    def test_artifacts_without_metadata_are_unknown(self, tmp_path: Path) -> None:
        result = run(["schema", "info", "--artifacts", str(tmp_path)])
        assert result.exit_code == 0
        assert result.stdout == "Schema version: unknown\nGenerated at:   unknown\n"

    def test_metadata_that_cannot_be_read_exits_three(self, tmp_path: Path) -> None:
        (tmp_path / "junos-schema-meta.json").write_text("not json", encoding="utf-8")
        result = run(["schema", "info", "--artifacts", str(tmp_path)])
        assert result.exit_code == 3
        assert result.stdout == ""
        assert result.stderr.startswith("Error: ")
