"""Acceptance tests for caller-owned conversion diagnostics."""

from __future__ import annotations

import json

from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.cli import main
from junoscfg.convert import pipeline, pipeline_result


class TestStructuredConversionResult:
    def test_opt_in_result_preserves_legacy_return_contracts(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'

        top_result = convert_config_result(
            source,
            from_format=Format.JSON,
            to_format=Format.SET,
            validate=False,
        )
        pipeline_result_value = pipeline_result(
            source,
            from_format="json",
            to_format="set",
            validate=False,
        )

        assert top_result.output == "set system host-name r1\n"
        assert top_result.diagnostics == ()
        assert pipeline_result_value == top_result
        assert isinstance(
            convert_config(
                source,
                from_format=Format.JSON,
                to_format=Format.SET,
                validate=False,
            ),
            str,
        )
        assert isinstance(
            pipeline(source, from_format="json", to_format="set", validate=False),
            str,
        )


class TestDiagnosticRouting:
    def test_cli_is_only_stderr_renderer(self, capsys) -> None:
        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "host-name": "router1",
                        "@host-name": {"operation": "delete"},
                    }
                }
            }
        )

        result = convert_config_result(
            source,
            from_format=Format.JSON,
            to_format=Format.STRUCTURED,
            validate=False,
        )
        assert capsys.readouterr().err == ""
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].source == "structured-output"
        assert "delete annotation(s) dropped" in result.diagnostics[0].render()

        assert isinstance(
            convert_config(
                source,
                from_format=Format.JSON,
                to_format=Format.STRUCTURED,
                validate=False,
            ),
            str,
        )
        assert capsys.readouterr().err == ""

        cli = CliRunner().invoke(main, ["-i", "json", "-e", "structured"], input=source)
        assert cli.exit_code == 0
        assert "delete annotation(s) dropped" in cli.stderr
