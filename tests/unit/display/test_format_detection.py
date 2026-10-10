"""Characterization tests for shared configuration format detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

import junoscfg
from junoscfg.cli import main
from junoscfg.display import (
    AUDIT_FORMATS,
    CONVERSION_FORMATS,
    VALIDATION_FORMATS,
    detect_format,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestFormatDetection:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ('{"configuration": {"system": {}}}', "json"),
            ("{}", "json"),
            ("<configuration><system/></configuration>", "xml"),
            ("configuration:\n  system:\n    host-name: r1\n", "yaml"),
            ("{configuration: {system: {host-name: r1}}}", "yaml"),
            ("set system host-name r1\n", "set"),
            ("protect system\n", "set"),
            ("activate system\n", "set"),
            ("system {\n    host-name r1;\n}\n", "structured"),
        ],
    )
    def test_characterization_matrix(self, source: str, expected: str) -> None:
        assert detect_format(source, accepted_formats=CONVERSION_FORMATS) == expected

        if expected in AUDIT_FORMATS:
            assert detect_format(source, accepted_formats=AUDIT_FORMATS) == expected

    def test_characterization_matrix_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            detect_format(" \n\t", accepted_formats=CONVERSION_FORMATS)


class TestDetectionPolicies:
    def test_each_caller_policy(self, monkeypatch: MonkeyPatch) -> None:
        flow_yaml = "{configuration: {system: {host-name: r1}}}"
        runner = CliRunner()

        conversion = runner.invoke(main, ["-e", "json"], input=flow_yaml)
        assert conversion.exit_code == 0
        assert '"host-name": "r1"' in conversion.output

        audit = runner.invoke(main, ["audit", "unused"], input=flow_yaml)
        assert audit.exit_code == 0

        marker = object()
        monkeypatch.setattr(junoscfg, "validate_structured", lambda *_args, **_kwargs: marker)
        monkeypatch.setattr(
            junoscfg,
            "validate_json",
            lambda *_args, **_kwargs: pytest.fail("validation auto-detection widened to JSON"),
        )

        assert (
            junoscfg.validate_config(
                '{"configuration": {"system": {}}}',
                format=None,
            )
            is marker
        )
        assert (
            detect_format(
                '{"configuration": {"system": {}}}',
                accepted_formats=VALIDATION_FORMATS,
            )
            == "structured"
        )
        assert junoscfg.validate_config("", format=None) is marker
