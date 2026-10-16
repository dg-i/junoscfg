"""The CLI's validation mode, `-v`, on the minimal artifacts.

What the shipped artifacts accept through `-v -i <format>`, beside every other
validation door, is `tests/contract/test_every_door.py`; the `schema` commands
are `test_schema_command.py`, and conversion through `-i` and `-e` is
`test_cli.py`.
"""

from __future__ import annotations

import json

from click.testing import CliRunner

from junoscfg.cli import main
from tests.support.aliases import alias_chain_yaml, nested_ir, nested_yaml


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

    def test_a_yaml_new_cycle_exits_one(self, artifacts_dir: str) -> None:
        """A self-referencing alias is a cycle JSON cannot hold: an error, not a
        RecursionError traceback (Reviewer finding 2; owner ruling on PO-2)."""
        result = CliRunner().invoke(
            main,
            ["-v", "-i", "yaml-new", "--artifacts", artifacts_dir],
            input="configuration: &a\n  system:\n    x: *a\n",
        )
        assert result.exit_code == 1, result.output
        assert "cycle has no JSON spelling" in result.output

    def test_a_yaml_new_value_past_64_levels_exits_one(self, artifacts_dir: str) -> None:
        """A value past 64 levels, written in the text or reached through an
        alias chain, is an invalid result naming its path, not a RecursionError
        traceback (owner ruling on SC-A)."""
        for source, path in (
            (nested_yaml(62), "configuration.system.x" + ".0" * 62),
            (alias_chain_yaml(), "s3" + ".0" * 64),
        ):
            result = CliRunner().invoke(
                main, ["-v", "-i", "yaml-new", "--artifacts", artifacts_dir], input=source
            )
            assert result.exit_code == 1, result.output
            assert "value is nested deeper than 64 levels" in result.output
            assert path in result.output

    def test_a_yaml_key_that_is_not_a_string_exits_one(self, artifacts_dir: str) -> None:
        """`-v -i yaml` reports a key that is not a string with its path, as
        yaml-new validation does, where jsonschema raised TypeError (owner
        request 2026-10-16, change own-crash-fixes)."""
        result = CliRunner().invoke(
            main,
            ["-v", "-i", "yaml", "--artifacts", artifacts_dir],
            input="configuration:\n  system:\n    host-name: r1\n  64496: x\n",
        )
        assert result.exit_code == 1, result.output
        assert "Validation: FAILED (1 error(s))" in result.output
        assert "int key has no JSON spelling" in result.output
        assert "Traceback" not in result.output and "64496" not in result.output

    def test_json_past_64_levels_exits_one(self, artifacts_dir: str) -> None:
        """`-v -i json` reports a value past 64 levels with its path, where it
        printed "Validation: OK" and the conversion crashed (Test/Challenge SC3,
        change own-crash-fixes)."""
        result = CliRunner().invoke(
            main,
            ["-v", "-i", "json", "--artifacts", artifacts_dir],
            input=json.dumps({"configuration": {"system": {"host-name": nested_ir(1600)}}}),
        )
        assert result.exit_code == 1, result.output
        assert "JSON value is nested deeper than 64 levels" in result.output
        assert "Validation: OK" not in result.output and "Traceback" not in result.output

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
