"""Conversion diagnostics are returned to the caller, never printed by the library.

Spec: conversion/diagnostics. `convert_config_result` and `pipeline_result`
carry the findings; the string doors return only the output, and the CLI is
the one place that renders them, on stderr.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.convert import pipeline, pipeline_result

if TYPE_CHECKING:
    import pytest


class TestStructuredConversionResult:
    def test_the_result_doors_agree_and_the_string_doors_return_text(self) -> None:
        """The two result doors give the same `ConversionResult`; `convert_config`
        and `pipeline` still return a string."""
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
    def test_cli_is_only_stderr_renderer(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A writer's note and the anonymizer's debug lines reach the result;
        the library writes nothing to stderr, the CLI writes the note there."""
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
        assert result.diagnostics[0].severity == "note"
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

        anonymize_result = convert_config_result(
            '{"configuration":{"system":{"name-server":[{"name":"8.8.8.8"}]}}}',
            from_format=Format.JSON,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(ips=True, salt="diagnostic-test", log_level="debug"),
        )
        assert capsys.readouterr().err == ""
        assert any(item.source == "anonymize" for item in anonymize_result.diagnostics)
