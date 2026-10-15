"""The CLI's validation mode, `-v`, on the minimal artifacts.

What the shipped artifacts accept through `-v -i <format>`, beside every other
validation door, is `tests/contract/test_every_door.py`; the `schema` commands
are `test_schema_command.py`, and conversion through `-i` and `-e` is
`test_cli.py`.
"""

from __future__ import annotations

from click.testing import CliRunner

from junoscfg.cli import main


class TestCliValidation:
    """`-v` validates against `--artifacts` and exits by the verdict."""

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

    def test_a_yaml_new_value_json_cannot_hold_exits_one(self, artifacts_dir: str) -> None:
        """`-v -i yaml-new` judges what JSON can hold: a key PyYAML reads as a
        boolean is an error with its path, not a traceback (Test/Challenge B2)."""
        result = CliRunner().invoke(
            main,
            ["-v", "-i", "yaml-new", "--artifacts", artifacts_dir],
            input="configuration:\n  system:\n    on: x\n",
        )
        assert result.exit_code == 1, result.output
        assert "Validation: FAILED (1 error(s))" in result.output
        assert "bool key has no JSON spelling" in result.output

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
