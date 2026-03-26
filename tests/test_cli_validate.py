"""Tests for CLI validation and schema commands."""

from __future__ import annotations

from click.testing import CliRunner

from junoscfg.cli import main


class TestCliConvertBasic:
    def test_json_to_set(self):
        runner = CliRunner()
        json_in = '{"configuration":{"system":{"host-name":"r1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "set"], input=json_in)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output

    def test_json_to_structured(self):
        runner = CliRunner()
        json_in = '{"configuration":{"system":{"host-name":"r1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "structured"], input=json_in)
        assert result.exit_code == 0
        assert "host-name r1" in result.output

    def test_no_export_error(self):
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "-i", "json"], input="{}")
        assert result.exit_code == 2


class TestCliValidation:
    def test_validate_json_ok(self, artifacts_dir):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-v", "-i", "json", "--artifacts", artifacts_dir],
            input='{"configuration":{"system":{"host-name":"r1"}}}',
        )
        assert "OK" in result.output or result.exit_code == 0

    def test_validate_only_mode(self, artifacts_dir):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-v", "-i", "json", "--artifacts", artifacts_dir],
            input='{"configuration":{"system":{"host-name":"r1"}}}',
        )
        # -v without -e = validate only
        assert result.exit_code == 0


class TestCliSchemaInfo:
    def test_schema_info(self, artifacts_dir):
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "info", "--artifacts", artifacts_dir])
        assert result.exit_code == 0
        assert "21.4R0" in result.output
