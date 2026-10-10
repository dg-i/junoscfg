"""The CLI's validation mode and `schema` commands, on the minimal artifacts.

What the shipped artifacts accept through `-v -i <format>`, beside every other
validation door, is `tests/contract/test_every_door.py`.
"""

from __future__ import annotations

from click.testing import CliRunner

from junoscfg.cli import main


class TestTheCliConvertsWithAnExportFormat:
    """Conversion plumbing: `-i` reads, `-e` writes, and `convert` needs `-e`.

    The conversions themselves are the library's, tested in `tests/unit/convert/`
    and `tests/contract/`.
    """

    def test_json_to_set(self) -> None:
        runner = CliRunner()
        json_in = '{"configuration":{"system":{"host-name":"r1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "set"], input=json_in)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output

    def test_json_to_structured(self) -> None:
        runner = CliRunner()
        json_in = '{"configuration":{"system":{"host-name":"r1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "structured"], input=json_in)
        assert result.exit_code == 0
        assert "host-name r1" in result.output

    def test_no_export_error(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "-i", "json"], input="{}")
        assert result.exit_code == 2


class TestCliValidation:
    def test_validate_only_mode(self, artifacts_dir: str) -> None:
        """`-v` without `-e` validates and converts nothing, against `--artifacts`."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-v", "-i", "json", "--artifacts", artifacts_dir],
            input='{"configuration":{"system":{"host-name":"r1"}}}',
        )
        assert result.exit_code == 0, result.output
        assert "Validation: OK" in result.output
        assert "host-name" not in result.output

    def test_an_invalid_document_exits_one_with_its_errors(self, artifacts_dir: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-v", "-i", "json", "--artifacts", artifacts_dir],
            input='{"configuration":{"bogus":{"x":"y"}}}',
        )
        assert result.exit_code == 1, result.output
        assert "Validation: FAILED (1 error(s))" in result.output
        assert "bogus" in result.output


class TestCliSchemaInfo:
    def test_schema_info(self, artifacts_dir: str) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "info", "--artifacts", artifacts_dir])
        assert result.exit_code == 0
        assert "21.4R0" in result.output
