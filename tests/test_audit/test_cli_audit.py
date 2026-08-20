"""Integration tests for the `junoscfg audit unused` CLI command."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config
from junoscfg.cli import main


def to_format(fmt: str) -> str:
    """Convert the shared set-text fixture into another input format."""
    return convert_config(
        SET_CONFIG, from_format=Format("set"), to_format=Format(fmt), validate=False
    )


if TYPE_CHECKING:
    from pathlib import Path

SET_CONFIG = """\
set policy-options policy-statement dead-pol term 1 then reject
set policy-options policy-statement live-pol term 1 then accept
set protocols bgp group ebgp import live-pol
set interfaces ge-0/0/0 description half-pol
set policy-options policy-statement half-pol term 1 then accept
"""

INPUT_FORMATS = ["set", "structured", "json", "yaml"]

OUTPUT_STYLES = [
    ("pathname", "policy-options policy-statement dead-pol"),
    ("delete-script", "delete policy-options policy-statement dead-pol"),
    ("show-script", "show policy-options policy-statement dead-pol"),
    (
        "show-configuration-script",
        "show configuration policy-options policy-statement dead-pol",
    ),
    ("deactivate-script", "deactivate policy-options policy-statement dead-pol"),
]


def run_cli(args: list[str], stdin: str) -> tuple[int, str, str]:
    runner = CliRunner()
    result = runner.invoke(main, args, input=stdin)
    return result.exit_code, result.output, result.stderr


class TestInputFormats:
    @pytest.mark.parametrize("fmt", INPUT_FORMATS)
    def test_each_input_format(self, fmt: str) -> None:
        source = SET_CONFIG if fmt == "set" else to_format(fmt)
        exit_code, output, _ = run_cli(["audit", "unused", "-i", fmt], source)
        assert exit_code == 0
        assert "policy-options policy-statement dead-pol" in output
        assert "live-pol" not in output

    def test_autodetect_set(self) -> None:
        exit_code, output, _ = run_cli(["audit", "unused"], SET_CONFIG)
        assert exit_code == 0
        assert "dead-pol" in output

    def test_conf_alias(self) -> None:
        structured = to_format("structured")
        exit_code, output, _ = run_cli(["audit", "unused", "-i", "conf"], structured)
        assert exit_code == 0
        assert "dead-pol" in output

    def test_file_input(self, tmp_path: Path) -> None:
        config = tmp_path / "config.set"
        config.write_text(SET_CONFIG)
        exit_code, output, _ = run_cli(["audit", "unused", str(config)], "")
        assert exit_code == 0
        assert "dead-pol" in output

    def test_empty_input(self) -> None:
        exit_code, output, _ = run_cli(["audit", "unused"], "")
        assert exit_code == 0
        assert output == ""


class TestOutputStyles:
    @pytest.mark.parametrize(("style", "expected"), OUTPUT_STYLES)
    def test_style(self, style: str, expected: str) -> None:
        exit_code, output, _ = run_cli(["audit", "unused", "-o", style], SET_CONFIG)
        assert exit_code == 0
        assert expected in output

    @pytest.mark.parametrize(("style", "expected"), OUTPUT_STYLES)
    def test_verbose_style(self, style: str, expected: str) -> None:
        exit_code, output, _ = run_cli(["audit", "unused", "-o", f"{style}-verbose"], SET_CONFIG)
        assert exit_code == 0
        assert expected in output
        assert "# summary:" in output

    def test_non_verbose_is_pipe_clean(self) -> None:
        exit_code, output, _ = run_cli(["audit", "unused", "-o", "delete-script"], SET_CONFIG)
        assert exit_code == 0
        lines = output.splitlines()
        assert lines
        assert all(line and not line.startswith("#") for line in lines)

    def test_delete_script_excludes_probably_unused(self) -> None:
        exit_code, output, _ = run_cli(["audit", "unused", "-o", "delete-script"], SET_CONFIG)
        assert exit_code == 0
        assert "half-pol" not in output

    def test_include_probably_unused_flag(self) -> None:
        exit_code, output, _ = run_cli(
            ["audit", "unused", "-o", "delete-script", "--include-probably-unused"], SET_CONFIG
        )
        assert exit_code == 0
        assert "delete policy-options policy-statement half-pol" in output


class TestFilters:
    def test_types_filter(self) -> None:
        source = SET_CONFIG + "set groups g-dead system host-name router1\n"
        exit_code, output, _ = run_cli(["audit", "unused", "--types", "policy-statement"], source)
        assert exit_code == 0
        assert "dead-pol" in output
        assert "g-dead" not in output

    def test_unknown_type_exits_2(self) -> None:
        exit_code, _, stderr = run_cli(["audit", "unused", "--types", "nonsense"], SET_CONFIG)
        assert exit_code == 2
        assert "unknown audit type" in stderr

    def test_match_filter(self) -> None:
        exit_code, output, _ = run_cli(["audit", "unused", "--match", "^dead-"], SET_CONFIG)
        assert exit_code == 0
        assert "dead-pol" in output
        assert "half-pol" not in output

    def test_invalid_match_regex_exits_2(self) -> None:
        exit_code, _, stderr = run_cli(["audit", "unused", "--match", "["], SET_CONFIG)
        assert exit_code == 2
        assert "invalid match regex" in stderr


class TestFailOn:
    def test_default_never(self) -> None:
        exit_code, _, _ = run_cli(["audit", "unused"], SET_CONFIG)
        assert exit_code == 0

    def test_fail_on_unused_with_findings(self) -> None:
        exit_code, _, _ = run_cli(["audit", "unused", "--fail-on", "unused"], SET_CONFIG)
        assert exit_code == 1

    def test_fail_on_unused_without_strict_findings(self) -> None:
        source = (
            "set policy-options policy-statement half-pol term 1 then accept\n"
            "set interfaces ge-0/0/0 description half-pol\n"
        )
        exit_code, _, _ = run_cli(["audit", "unused", "--fail-on", "unused"], source)
        assert exit_code == 0

    def test_fail_on_probably_unused_with_any_finding(self) -> None:
        source = (
            "set policy-options policy-statement half-pol term 1 then accept\n"
            "set interfaces ge-0/0/0 description half-pol\n"
        )
        exit_code, _, _ = run_cli(["audit", "unused", "--fail-on", "probably-unused"], source)
        assert exit_code == 1

    def test_fail_on_probably_unused_clean_config(self) -> None:
        source = (
            "set policy-options policy-statement live-pol term 1 then accept\n"
            "set protocols bgp group ebgp import live-pol\n"
        )
        exit_code, _, _ = run_cli(["audit", "unused", "--fail-on", "probably-unused"], source)
        assert exit_code == 0


class TestRegistryOption:
    def test_broken_registry_exits_3(self, tmp_path: Path) -> None:
        broken = tmp_path / "broken.yaml"
        broken.write_text("version: 1\ntypes: {}\n")
        exit_code, _, stderr = run_cli(["audit", "unused", "--registry", str(broken)], SET_CONFIG)
        assert exit_code == 3
        assert "must be a non-empty mapping" in stderr

    def test_custom_registry(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom.yaml"
        custom.write_text(
            """
version: 1
types:
  policy-statement:
    source: curated
    definition: [policy-options policy-statement]
    references:
      schema-types: [policy-algebra]
"""
        )
        source = SET_CONFIG + "set groups g-dead system host-name router1\n"
        exit_code, output, _ = run_cli(["audit", "unused", "--registry", str(custom)], source)
        assert exit_code == 0
        assert "dead-pol" in output
        assert "g-dead" not in output  # custom registry has no config-group type
