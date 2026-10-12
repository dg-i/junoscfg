"""Conversion diagnostics are returned to the caller, never printed by the library.

Spec: conversion/diagnostics. `convert_config_result` and `pipeline_result`
carry the findings; the string doors return only the output, and the CLI is
the one place that renders them, on stderr.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.convert import pipeline, pipeline_result

if TYPE_CHECKING:
    from junoscfg.convert import Diagnostic


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


#: A radius server without its `secret`, which the schema marks mandatory: the
#: vMX (23.2R2-S7.5) loaded it so, the device's own line
#: (`tests/data/device/synthetic/vmx-23.2R2-S7.5/synthetic-probes.set.gz`), and
#: Junos may check it at commit.
RADIUS_WITHOUT_SECRET = {
    Format.SET: "set access radius-server 192.168.50.10\n",
    Format.STRUCTURED: "access {\n    radius-server {\n        192.168.50.10;\n    }\n}\n",
    Format.JSON: json.dumps(
        {"configuration": {"access": {"radius-server": [{"name": "192.168.50.10"}]}}}
    ),
    Format.YAML: "configuration:\n  access:\n    radius-server:\n    - name: 192.168.50.10\n",
    Format.XML: (
        "<configuration><access><radius-server><name>192.168.50.10</name>"
        "</radius-server></access></configuration>"
    ),
}
SECRET_WARNING = (
    "field-validate",
    "access.radius-server.secret",
    "Missing mandatory field 'secret': may be required at commit; "
    "the configuration loads without it",
)


def _field_findings(diagnostics: tuple[Diagnostic, ...]) -> list[tuple[str, str | None, str]]:
    return [(d.source, d.path, d.message) for d in diagnostics if d.source == "field-validate"]


class TestAFieldWarningNeedsNoError:
    """A field-validation warning is carried whether or not an error was found
    (NEW-B7 = NEW-C2; spec conversion/diagnostics).

    It was carried only beside an error: the radius server without `secret`
    converted silently alone and was reported once an unrelated statement
    failed. `strict` raises on errors only; a warning never stops a conversion.
    """

    @pytest.mark.parametrize("strict", [False, True], ids=["lenient", "strict"])
    @pytest.mark.parametrize("from_format", list(RADIUS_WITHOUT_SECRET), ids=lambda f: f.value)
    def test_every_door_reports_it(self, from_format: Format, strict: bool) -> None:
        source = RADIUS_WITHOUT_SECRET[from_format]
        result = convert_config_result(
            source, from_format=from_format, to_format=Format.SET, strict=strict
        )
        assert result.output == "set access radius-server 192.168.50.10\n"
        assert _field_findings(result.diagnostics) == [SECRET_WARNING]
        assert result == pipeline_result(
            source, from_format=from_format.value, to_format="set", strict=strict
        )

    def test_an_error_beside_it_changes_nothing(self) -> None:
        """An unplaced statement adds its error; the warning is the one reported alone."""
        source = RADIUS_WITHOUT_SECRET[Format.SET] + "set chassis dump-on-panic\n"
        result = convert_config_result(source, from_format=Format.SET, to_format=Format.SET)
        findings = _field_findings(result.diagnostics)
        assert SECRET_WARNING in findings
        assert [f for f in findings if f != SECRET_WARNING] == [
            (
                "field-validate",
                "chassis",
                "'dump-on-panic' could not be placed in the schema: kept as written, not validated",
            )
        ]

    @pytest.mark.parametrize("options", [[], ["--strict"]], ids=["lenient", "strict"])
    def test_the_cli_prints_it(self, options: list[str]) -> None:
        cli = CliRunner().invoke(
            main, ["-i", "set", "-e", "set", *options], input=RADIUS_WITHOUT_SECRET[Format.SET]
        )
        assert cli.exit_code == 0
        assert cli.stdout == "set access radius-server 192.168.50.10\n"
        assert cli.stderr.splitlines() == [": ".join(SECRET_WARNING)]
