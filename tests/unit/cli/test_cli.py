"""`junoscfg` and `junoscfg convert`: options, input, output and exit codes.

The plumbing only. Each option is run once, and what the command prints is what
the library gives for the same arguments, and differs from what it gives
without the option, so the option is seen to reach the library. What a
conversion, a path or an anonymize rule does is tested where it is done:

- conversions, every reader to every writer: `tests/contract/test_format_matrix.py`
  over `tests/support/shapes.py`;
- `--path` and `--relative`: `tests/unit/convert/test_convert_api.py`
  (`TestPathFiltering`);
- the rule flags (`--anonymize-passwords`, `-ssh-keys`, `-ips`, `-communities`,
  `-identities`, `-groups`, `-descriptions`, `-as-numbers`, `-sensitive-words`,
  `-sensitive-patterns`) with `--anonymize-salt`, `--anonymize-dump-map`,
  `--anonymize-revert-map` and `--no-field-validate`:
  `tests/contract/test_every_rule.py::TestEveryRule::test_the_cli_flags_keep_the_same_law`;
- the other anonymize options: `tests/unit/anonymize/`;
- `-v` against the minimal artifacts: `test_cli_validate.py`;
- `schema generate` and `schema info`: `test_schema_command.py`.
"""

from __future__ import annotations

import importlib.metadata
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pytest
from click.testing import CliRunner, Result

import junoscfg
from junoscfg import Format, convert_config, convert_config_result, validate_config
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.display import artifacts_dir as artifacts_in
from tests.support.aliases import (
    CYCLE,
    SHARED_BLOCK,
    SHARED_BLOCK_WRITTEN_OUT,
    alias_chain_yaml,
    nested_ir,
    nested_yaml,
)
from tests.support.paths import PROJECT_ROOT
from tests.support.shapes import SHAPES, WRITERS

if TYPE_CHECKING:
    from pathlib import Path

#: `system host-name r1` in every format, from the shape catalogue.
A_LEAF = next(shape for shape in SHAPES if shape.name == "a-leaf").sources
READERS = tuple(A_LEAF)


def run(args: list[str], stdin: str | None = None) -> Result:
    return CliRunner().invoke(main, args, input=stdin)


def library(source: str, reader: Format, writer: Format, **options: Any) -> str:
    return convert_config(source, from_format=reader, to_format=writer, **options)


class TestVersion:
    """One version, three places that must agree; no test names its value."""

    def test_the_cli_prints_the_package_version(self) -> None:
        result = run(["--version"])
        assert result.exit_code == 0
        assert result.stdout == f"junoscfg, version {junoscfg.__version__}\n"

    def test_the_package_version_is_the_installed_distributions(self) -> None:
        assert junoscfg.__version__ == importlib.metadata.version("junoscfg")

    def test_the_package_version_is_the_project_version(self) -> None:
        # Read by pattern, not tomllib: the package supports 3.10, which has none.
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        found = re.search(r'^\[project\]$.*?^version = "([^"]+)"$', pyproject, re.M | re.S)
        assert found, "pyproject.toml declares no [project] version"
        assert junoscfg.__version__ == found.group(1)


def _commands(group: Any, prefix: str = "junoscfg") -> list[str]:
    """Every command's full name under *group*, the `fullhelp` command aside."""
    names = []
    for name, command in group.commands.items():
        if name == "fullhelp":
            continue
        names.append(f"{prefix} {name}")
        if hasattr(command, "commands"):
            names.extend(_commands(command, f"{prefix} {name}"))
    return names


_CONVERT_OPTIONS = [
    max(param.opts, key=len) for param in main.commands["convert"].params if param.opts[0][0] == "-"
]


class TestHelp:
    def test_no_arguments_print_the_help(self) -> None:
        result = run([])
        assert result.exit_code == 0
        assert "Junoscfg" in result.stdout

    @pytest.mark.parametrize("option", ["--help", "-h", "-?"], ids=["long", "h", "question-mark"])
    @pytest.mark.parametrize(
        ("command", "title"), [([], "Junoscfg"), (["convert"], "Convert")], ids=["main", "convert"]
    )
    def test_every_help_option_prints_the_help(
        self, command: list[str], title: str, option: str
    ) -> None:
        result = run([*command, option])
        assert result.exit_code == 0
        assert title in result.stdout

    @pytest.mark.parametrize("option", _CONVERT_OPTIONS)
    def test_convert_help_lists_every_option(self, option: str) -> None:
        result = run(["convert", "--help"])
        assert result.exit_code == 0
        assert option in result.stdout

    @pytest.mark.parametrize("fmt", [f.value for f in Format])
    def test_convert_help_describes_every_format(self, fmt: str) -> None:
        """The Formats list names each one, yaml-new and the planned rename included."""
        result = run(["convert", "--help"])
        line = re.search(rf"^ +{re.escape(fmt)} +(\S.*)$", result.stdout, re.MULTILINE)
        assert line, fmt
        planned = {"yaml": "to be renamed yaml-old", "yaml-new": "to become yaml"}
        assert planned.get(fmt, "") in line.group(1)

    @pytest.mark.parametrize("command", ["junoscfg", *_commands(main)])
    def test_fullhelp_has_a_section_per_command(self, command: str) -> None:
        result = run(["fullhelp"])
        assert result.exit_code == 0
        assert f"  {command}\n" in result.stdout, f"no section for {command}"


class TestConvertIsTheDefaultCommand:
    """Without a subcommand, options and a file go to `convert`."""

    def test_options_without_a_subcommand_run_convert(self) -> None:
        source = A_LEAF[Format.JSON]
        implicit = run(["-i", "json", "-e", "set"], source)
        assert implicit.exit_code == 0
        assert implicit.stdout == run(["convert", "-i", "json", "-e", "set"], source).stdout

    def test_a_file_without_a_subcommand_is_converted(self, tmp_path: Path) -> None:
        source = tmp_path / "config.json"
        source.write_text(A_LEAF[Format.JSON])
        result = run([str(source), "-e", "set"])
        assert result.exit_code == 0
        assert result.stdout == library(A_LEAF[Format.JSON], Format.JSON, Format.SET)


class TestConvertReadsAndWrites:
    """`-i` and `-e` reach the library; input comes from a file or stdin."""

    @pytest.mark.parametrize("writer", WRITERS, ids=[w.value for w in WRITERS])
    @pytest.mark.parametrize("reader", READERS, ids=[r.value for r in READERS])
    def test_every_import_and_export_format_reaches_the_library(
        self, reader: Format, writer: Format
    ) -> None:
        source = A_LEAF[reader]
        result = run(["convert", "-i", reader.value, "-e", writer.value], source)
        assert result.exit_code == 0, result.output
        assert result.stdout == library(source, reader, writer)
        assert result.stderr == ""

    @pytest.mark.parametrize("reader", READERS, ids=[r.value for r in READERS])
    def test_without_an_import_format_the_format_is_detected(self, reader: Format) -> None:
        source = A_LEAF[reader]
        result = run(["convert", "-e", "set"], source)
        assert result.exit_code == 0, result.output
        assert result.stdout == library(source, reader, Format.SET)

    @pytest.mark.parametrize(
        ("import_format", "export_format"),
        [("conf", "set"), ("set", "conf"), ("conf", "conf")],
        ids=["import", "export", "both"],
    )
    def test_conf_is_an_alias_for_structured(self, import_format: str, export_format: str) -> None:
        reader = Format.STRUCTURED if import_format == "conf" else Format.SET
        writer = Format.STRUCTURED if export_format == "conf" else Format.SET
        result = run(["convert", "-i", import_format, "-e", export_format], A_LEAF[reader])
        assert result.exit_code == 0
        assert result.stdout == library(A_LEAF[reader], reader, writer)

    def test_an_ir_yaml_file_migrates_to_junos_yaml(self, tmp_path: Path) -> None:
        """The documented migration: `-i yaml -e yaml-new` drops the yaml reader's
        meta keys and writes the Junos JSON object (docs/guide/conversion.md)."""
        legacy = tmp_path / "old.yaml"
        legacy.write_text(
            "configuration:\n  system:\n    host-name: r1\n    _ansible_host: x\n"
            "  routing-options:\n    static:\n      route:\n      - name: 0.0.0.0/0\n"
            "        next-hop: 10.0.0.1\n"
        )
        result = run(["convert", "-i", "yaml", "-e", "yaml-new", str(legacy)])
        assert result.exit_code == 0, result.output
        assert result.stdout == library(legacy.read_text(), Format.YAML, Format.YAML_NEW)
        assert "_ansible_host" not in result.stdout
        as_json = library(legacy.read_text(), Format.YAML, Format.JSON)
        assert library(result.stdout, Format.YAML_NEW, Format.JSON) == as_json

    @pytest.mark.parametrize("reader", ["yaml-new", "yaml"])
    @pytest.mark.parametrize(
        ("source", "said"),
        [
            (CYCLE, "a YAML cycle at configuration.system.x has no JSON spelling"),
            (
                nested_yaml(62),
                "a YAML value at configuration.system.x"
                + ".0" * 62
                + " is nested deeper than 64 levels",
            ),
            (
                alias_chain_yaml(),
                "a YAML value at s3" + ".0" * 64 + " is nested deeper than 64 levels",
            ),
        ],
        ids=["a-cycle", "sixty-five-deep", "an-alias-chain"],
    )
    def test_a_cycle_or_a_value_past_64_levels_exits_two(
        self, source: str, said: str, reader: str
    ) -> None:
        """A cycle or a value past 64 levels is refused with its path, exit 2,
        never a traceback, by both YAML readers (owner rulings on SC-A and C5)."""
        result = run(["convert", "-i", reader, "-e", "json"], source)
        assert result.exit_code == 2, result.output
        assert said in result.stderr
        assert result.stdout == ""

    @pytest.mark.parametrize("reader", ["yaml", None], ids=["yaml", "detected"])
    def test_a_yaml_key_that_is_not_a_string_exits_two(self, reader: str | None) -> None:
        """The owner's example (2026-10-16, change own-crash-fixes): a number as
        a key, which crashed the meta-key cleanup with a traceback, is refused
        with its path, as yaml-new refuses it."""
        source = "configuration:\n  system:\n    host-name: r1\n  64496: x\n"
        flags = ["-i", reader] if reader else []
        result = run(["convert", *flags, "-e", "set"], source)
        assert result.exit_code == 2, result.output
        assert "a YAML int key at configuration has no JSON spelling" in result.stderr
        assert "Traceback" not in result.output and "64496" not in result.output
        assert result.stdout == ""

    @pytest.mark.parametrize("reader", ["json", None], ids=["json", "detected"])
    def test_json_past_64_levels_exits_two(self, reader: str | None) -> None:
        """JSON nested 1,600 levels deep crashed with RecursionError (owner
        request 2026-10-16, change own-crash-fixes); it is refused with its path,
        named or detected (Test/Challenge TC8)."""
        source = json.dumps({"configuration": nested_ir(1600)})
        flags = ["-i", reader] if reader else []
        result = run(["convert", *flags, "-e", "set"], source)
        assert result.exit_code == 2, result.output
        assert (
            "a JSON value at configuration" + ".a" * 64 + " is nested deeper than 64 levels"
            in result.stderr
        )
        assert result.stdout == ""

    def test_detected_yaml_refuses_a_cycle(self) -> None:
        """YAML the CLI detects reads as `yaml`, which refuses a cycle with its
        path, exit 2 (owner ruling on C5)."""
        result = run(["convert", "-e", "json"], CYCLE)
        assert result.exit_code == 2, result.output
        assert "a YAML cycle at configuration.system.x has no JSON spelling" in result.stderr

    def test_a_yaml_new_shared_block_converts_as_written_out(self) -> None:
        shared = run(["convert", "-i", "yaml-new", "-e", "set"], SHARED_BLOCK)
        assert shared.exit_code == 0, shared.output
        assert shared.stdout == library(SHARED_BLOCK_WRITTEN_OUT, Format.YAML_NEW, Format.SET)

    def test_a_value_json_cannot_hold_stops_the_migration(self, tmp_path: Path) -> None:
        """A date the yaml file holds unquoted has no JSON spelling: the
        migration exits 2 naming its path, rather than write a file yaml-new
        refuses (Reviewer finding 1)."""
        legacy = tmp_path / "old.yaml"
        legacy.write_text("configuration:\n  system:\n    host-name: 2026-10-15\n")
        result = run(["convert", "-i", "yaml", "-e", "yaml-new", str(legacy)])
        assert result.exit_code == 2, result.output
        assert "date at configuration.system.host-name has no JSON spelling" in result.stderr
        assert result.stdout == ""
        quoted = legacy.read_text().replace("2026-10-15", "'2026-10-15'")
        assert library(quoted, Format.YAML, Format.YAML_NEW).endswith("host-name: '2026-10-15'\n")

    def test_a_file_argument_is_read(self, tmp_path: Path) -> None:
        source = tmp_path / "config.json"
        source.write_text(A_LEAF[Format.JSON])
        result = run(["convert", "-i", "json", "-e", "set", str(source)])
        assert result.exit_code == 0
        assert result.stdout == library(A_LEAF[Format.JSON], Format.JSON, Format.SET)

    def test_empty_input_prints_nothing(self) -> None:
        result = run(["convert", "-i", "json", "-e", "set"], "")
        assert result.exit_code == 0
        assert result.output == ""


class TestUsageErrorsExitTwo:
    """A usage or input error exits 2, says why on stderr, and writes nothing."""

    def _refused(self, result: Result, message: str) -> None:
        assert result.exit_code == 2
        assert result.stdout == ""
        assert message in result.stderr

    def test_convert_without_an_export_format(self) -> None:
        self._refused(run(["convert", "-i", "json"], "{}"), "Error: specify -e/--export-format")

    def test_relative_without_path(self) -> None:
        self._refused(
            run(["convert", "-i", "json", "-e", "set", "--relative"], A_LEAF[Format.JSON]),
            "Error: --relative requires --path.",
        )

    def test_a_file_that_does_not_exist(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.json"
        self._refused(run(["convert", "-e", "set", str(missing)]), "does not exist")

    def test_xml_output(self) -> None:
        self._refused(
            run(["convert", "-i", "json", "-e", "xml"], A_LEAF[Format.JSON]),
            "Error: XML output is not yet supported.",
        )

    def test_malformed_json(self) -> None:
        self._refused(run(["convert", "-i", "json", "-e", "set"], "{bad json"), "Error: ")

    def test_malformed_yaml(self) -> None:
        self._refused(
            run(["convert", "-i", "yaml", "-e", "set"], "configuration: [unclosed\n"),
            "Error: Invalid YAML: ",
        )

    def test_set_bracket_syntax_is_refused_with_the_whole_line(self) -> None:
        """The diagnostic names the line in full, however long it is.

        Spec: conversion/raw-set-input; the readers' rejection itself is
        `tests/unit/convert/test_set_input.py::TestSetBracketSyntaxRejection`.
        """
        line = "set system host-name " + "r" * 120 + " [broken]"
        self._refused(
            run(["convert", "-i", "set", "-e", "json"], line),
            f"Unsupported bracket syntax in set input on line 1:\n{line}",
        )


#: A statement the bundled schema cannot place: a field-validation finding.
UNPLACED = "set interfaces ge-0/0/0 nonsense alpha"


class TestFieldValidationOptions:
    """Field validation reports on stderr; `--strict` fails; `--no-field-validate` skips it."""

    def test_a_finding_goes_to_stderr_beside_the_output(self) -> None:
        result = run(["convert", "-i", "set", "-e", "set"], UNPLACED)
        expected = convert_config_result(UNPLACED, from_format=Format.SET, to_format=Format.SET)
        assert result.exit_code == 0
        assert result.stdout == expected.output
        assert expected.diagnostics
        assert result.stderr == "".join(d.render() + "\n" for d in expected.diagnostics)

    def test_no_field_validate_reports_nothing(self) -> None:
        result = run(["convert", "-i", "set", "-e", "set", "--no-field-validate"], UNPLACED)
        assert result.exit_code == 0
        assert result.stdout == library(UNPLACED, Format.SET, Format.SET, validate=False)
        assert result.stderr == ""

    def test_strict_exits_one_with_the_error(self) -> None:
        result = run(["convert", "-i", "set", "-e", "set", "--strict"], UNPLACED)
        assert result.exit_code == 1
        assert result.stdout == ""
        lines = result.stderr.splitlines()
        assert lines[0] == "Field validation: FAILED (1 error(s))"
        assert len(lines) == 2
        assert "'nonsense alpha' under interfaces ge-0/0/0 could not be placed" in lines[1]

    def test_strict_exits_one_with_the_first_ten_errors(self) -> None:
        source = "\n".join(f"set interfaces ge-0/0/{n} nonsense alpha" for n in range(11))
        result = run(["convert", "-i", "set", "-e", "set", "--strict"], source)
        assert result.exit_code == 1
        assert result.stdout == ""
        lines = result.stderr.splitlines()
        assert lines[0] == "Field validation: FAILED (11 error(s))"
        assert [line.split(" under interfaces ", 1)[1].split()[0] for line in lines[1:11]] == [
            f"ge-0/0/{n}" for n in range(10)
        ]
        assert lines[11:] == ["  ... and 1 more errors"]


class TestAKeptStatementOnTheCommandLine:
    """`junoscfg convert` writes a bare statement beside the node it names,
    reports it, fails under `--strict`, and anonymizes it without printing it.
    Change kept-whole-statements (OPEN-2, NEW-C1)."""

    _SOURCE = "set system host-name router1\nset system host-name\n"

    def test_json_output_holds_the_record_and_stderr_the_report(self) -> None:
        result = run(["convert", "-i", "set", "-e", "json"], self._SOURCE)
        assert result.exit_code == 0
        assert json.loads(result.stdout)["configuration"]["system"] == {
            "host-name": "router1",
            "junoscfg:unplaced": {"host-name": [None]},
        }
        assert "'host-name' could not be placed in the schema" in result.stderr

    def test_strict_fails(self) -> None:
        result = run(["convert", "-i", "set", "-e", "set", "--strict"], self._SOURCE)
        assert result.exit_code == 1
        assert result.stdout == ""

    def test_anonymizing_warns_without_the_statement(self) -> None:
        """Owner answer 5 (change anonymize-every-placed-value): the statement's
        address is replaced and its schema path named on stderr, where the run
        exited 1; no line of stderr carries the statement."""
        source = "set system nonsense 203.0.114.9 SAMPLE-WORD\n"
        result = run(
            ["convert", "-i", "set", "-e", "set", "--anonymize-ips", "--anonymize-salt", "s"],
            source,
        )
        assert result.exit_code == 0
        assert result.stdout.startswith("set system nonsense ")
        assert "SAMPLE-WORD" in result.stdout
        assert "203.0.114.9" not in result.output
        assert "anonymize: system: " in result.stderr
        assert "nonsense" not in result.stderr
        assert "SAMPLE-WORD" not in result.stderr


class TestValidateOption:
    """`-v` beside `-e` validates, then converts; the artifacts it reads can fail."""

    def test_validate_with_an_export_format_validates_and_converts(self) -> None:
        source = A_LEAF[Format.JSON]
        result = run(["convert", "-v", "-i", "json", "-e", "set"], source)
        assert result.exit_code == 0
        assert result.stderr == "Validation: OK\n"
        assert result.stdout == library(source, Format.JSON, Format.SET)

    def test_more_than_ten_errors_are_counted_not_listed(self, artifacts_dir: str) -> None:
        source = "\n".join(f"set bogus{n} x" for n in range(11))
        result = run(["convert", "-v", "-i", "set", "--artifacts", artifacts_dir], source)
        errors = validate_config(source, format="set", artifacts_dir=artifacts_dir).errors
        assert result.exit_code == 1
        lines = result.stderr.splitlines()
        assert lines[0] == "Validation: FAILED (11 error(s))"
        assert lines[1:11] == [f"  - {e.message} (line {e.line})" for e in errors[:10]]
        assert lines[11:] == ["  ... and 1 more errors"]

    def test_artifacts_that_cannot_load_exit_three(self, tmp_path: Path) -> None:
        result = run(["convert", "-v", "-i", "json", "--artifacts", str(tmp_path)], "{}")
        assert result.exit_code == 3
        assert result.stderr.startswith("Error loading validation artifacts: ")


class TestArtifactsOption:
    """`--artifacts` holds for the conversion too, and only for that command."""

    def _expected_error(self, directory: str) -> str:
        with artifacts_in(directory), pytest.raises(ValueError) as refused:
            library(A_LEAF[Format.SET], Format.SET, Format.JSON)
        return f"Error: {refused.value}\n"

    def test_the_conversion_reads_the_named_artifacts(self, artifacts_dir: str) -> None:
        """The minimal artifacts carry no structure tree, so the conversion is refused."""
        result = run(
            ["convert", "-i", "set", "-e", "json", "--artifacts", artifacts_dir],
            A_LEAF[Format.SET],
        )
        assert result.exit_code == 2
        assert result.stderr == self._expected_error(artifacts_dir)
        after = library(A_LEAF[Format.SET], Format.SET, Format.JSON)
        assert json.loads(after)["configuration"] == {"system": {"host-name": "r1"}}, (
            "the override outlived the command"
        )

    def test_the_environment_variable_is_the_option(self, artifacts_dir: str) -> None:
        result = CliRunner(env={"JUNOSCFG_ARTIFACTS": artifacts_dir}).invoke(
            main, ["convert", "-i", "set", "-e", "json"], input=A_LEAF[Format.SET]
        )
        assert result.exit_code == 2
        assert result.stderr == self._expected_error(artifacts_dir)


class TestPathOptions:
    """`--path` and `--relative` reach `convert_config(path=, relative=)`."""

    SOURCE = (
        '{"configuration": {"system": {"host-name": "r1",'
        ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
    )

    @pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
    @pytest.mark.parametrize(
        ("writer", "path"),
        [
            (Format.SET, "system.syslog"),
            (Format.STRUCTURED, "system"),
            (Format.YAML, "system"),
            (Format.YAML_NEW, "system"),
            (Format.JSON, "system"),
            (Format.SET, "nonexistent"),
        ],
        ids=["set", "structured", "yaml", "yaml-new", "json", "set-not-found"],
    )
    def test_the_path_reaches_the_library(self, writer: Format, path: str, relative: bool) -> None:
        flags = ["--path", path] + (["--relative"] if relative else [])
        result = run(["convert", "-i", "json", "-e", writer.value, *flags], self.SOURCE)
        expected = library(self.SOURCE, Format.JSON, writer, path=path, relative=relative)
        assert result.exit_code == 0
        assert result.stdout == expected
        if path != "nonexistent":
            assert expected != library(self.SOURCE, Format.JSON, writer)

    def test_path_keeps_a_selected_leafs_tags(self) -> None:
        """The owner's example (2026-10-16, change own-crash-fixes): a selected
        leaf keeps its `deactivate`, as `--path system` writes it, where it was
        written active."""
        source = (
            "set system host-name r1\ndeactivate system host-name\n"
            "set system domain-name example.net\n"
        )
        result = run(["convert", "-i", "set", "-e", "set", "--path", "system.host-name"], source)
        assert result.exit_code == 0, result.output
        assert result.stdout == "set system host-name r1\ndeactivate system host-name\n"

    def test_path_keeps_an_ancestors_tag(self) -> None:
        """A leaf under `deactivate system` is written inside the deactivated
        statement, as the QFX5120 25.2R2-S1.5 prints a leaf under a deactivated
        route (probe C3), where it was written active (change device-probe-fixes)."""
        source = "set system host-name r1\nset system domain-name example.net\ndeactivate system\n"
        result = run(["convert", "-i", "set", "-e", "set", "--path", "system.host-name"], source)
        assert result.exit_code == 0, result.output
        assert result.stdout == "set system host-name r1\ndeactivate system\n"

    def test_a_relative_path_notes_a_dropped_tag(self) -> None:
        """Relative output of a deactivated container writes what lies below it
        and notes the tag on stderr; the bare `deactivate` it wrote is a line the
        device refuses (probe SC1; owner ruling 2026-10-17, change
        device-probe-fixes)."""
        source = "set system syslog file f any any\ndeactivate system syslog\n"
        result = run(
            ["convert", "-i", "set", "-e", "set", "--path", "system.syslog", "--relative"], source
        )
        assert result.exit_code == 0, result.output
        assert result.stdout == "set file f any any\n"
        assert "1 tag(s) at or above the selected path dropped" in result.stderr


#: An IP-typed leaf, a name server.
NAME_SERVER = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
#: An address in the system tree and one in the interfaces tree.
TWO_TREES = json.dumps(
    {
        "configuration": {
            "system": {"name-server": [{"name": "8.8.8.8"}]},
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {"inet": {"address": [{"name": "10.1.2.3/24"}]}},
                            }
                        ],
                    }
                ]
            },
        }
    }
)


def _name_servers(*addresses: str) -> str:
    servers = [{"name": address} for address in addresses]
    return json.dumps({"configuration": {"system": {"name-server": servers}}})


@dataclass(frozen=True)
class AnonymizeOption:
    """One `--anonymize-*` option and the `AnonymizeConfig` fields it sets.

    *base* is what the option needs beside it (an IP option needs the IP rule
    on); the expected output is the library's with ``base_config`` and
    ``config``, and the option must change it from ``base_config`` alone.
    """

    id: str
    flags: tuple[str, ...]
    config: dict[str, Any]
    source: str = NAME_SERVER
    writer: Format = Format.JSON
    base: tuple[str, ...] = ("--anonymize-ips",)
    base_config: dict[str, Any] = field(default_factory=lambda: {"ips": True})


_EVERY_BOOLEAN_RULE = {
    "ips": True,
    "passwords": True,
    "communities": True,
    "ssh_keys": True,
    "identities": True,
    "groups": True,
    "descriptions": True,
    "ips_in_strings": True,
    "as_numbers_in_strings": True,
}

ANONYMIZE_OPTIONS = (
    AnonymizeOption("ips", ("--anonymize-ips",), {"ips": True}, base=(), base_config={}),
    AnonymizeOption(
        "ips-set-output",
        ("--anonymize-ips",),
        {"ips": True},
        writer=Format.SET,
        base=(),
        base_config={},
    ),
    AnonymizeOption(
        "all",
        ("--anonymize-all",),
        _EVERY_BOOLEAN_RULE,
        source=json.dumps(
            {
                "configuration": {
                    "system": {
                        "name-server": [{"name": "8.8.8.8"}],
                        "login": {
                            "user": [
                                {
                                    "name": "admin",
                                    "authentication": {"encrypted-password": "$6$abc123$xyz"},
                                }
                            ]
                        },
                    }
                }
            }
        ),
        base=(),
        base_config={},
    ),
    AnonymizeOption(
        "include", ("--anonymize-include", "interfaces"), {"include": ["interfaces"]}, TWO_TREES
    ),
    AnonymizeOption(
        "exclude", ("--anonymize-exclude", "system"), {"exclude": ["system"]}, TWO_TREES
    ),
    AnonymizeOption(
        "preserve-prefixes",
        ("--anonymize-preserve-prefixes", "10.1.0.0/16"),
        {"preserve_prefixes": ["10.1.0.0/16"]},
        TWO_TREES,
    ),
    AnonymizeOption(
        "networks",
        ("--anonymize-networks", "203.0.114.0/24"),
        {"networks": ["203.0.114.0/24"]},
        _name_servers("203.0.114.1", "203.0.114.254"),
    ),
    AnonymizeOption(
        "ignore-subnets",
        ("--anonymize-ignore-subnets",),
        {"ignore_subnets": True},
        _name_servers("192.168.1.1"),
    ),
    AnonymizeOption(
        "ignore-reserved",
        ("--anonymize-ignore-reserved",),
        {"ignore_reserved": True},
        _name_servers("127.0.0.1"),
    ),
    AnonymizeOption(
        "ips-in-strings",
        ("--anonymize-ips-in-strings",),
        {"ips_in_strings": True},
        # An address beside text is replaced without the option (change
        # anonymize-embedded-values); what it adds is an address that is a
        # whole value of a leaf whose type holds none, an `areaid` reference.
        json.dumps(
            {
                "configuration": {
                    "policy-options": {
                        "policy-statement": [
                            {"name": "P", "term": [{"name": "T", "from": {"area": "198.0.2.1"}}]}
                        ]
                    }
                }
            }
        ),
    ),
    AnonymizeOption(
        "as-numbers-in-strings",
        ("--anonymize-as-numbers-in-strings",),
        {"as_numbers_in_strings": True},
        json.dumps(
            {
                "configuration": {
                    "protocols": {
                        "bgp": {"group": [{"name": "inet-Upstream-AS64497", "peer-as": "64497"}]}
                    }
                }
            }
        ),
        base=("--anonymize-as-numbers", "64497"),
        base_config={"as_numbers": [64497]},
    ),
)

SALT = "cli-option"


def _anonymized(source: str, writer: Format, salt: str = SALT, **config: Any) -> str:
    anon = AnonymizeConfig(salt=salt, **config) if config else None
    return library(source, Format.JSON, writer, anon_config=anon)


class TestAnonymizeOptions:
    """Each `--anonymize-*` option sets its `AnonymizeConfig` field."""

    @pytest.mark.parametrize("option", ANONYMIZE_OPTIONS, ids=[o.id for o in ANONYMIZE_OPTIONS])
    def test_the_option_reaches_the_library(self, option: AnonymizeOption) -> None:
        args = ["convert", "-i", "json", "-e", option.writer.value, *option.base, *option.flags]
        result = run([*args, "--anonymize-salt", SALT], option.source)
        expected = _anonymized(option.source, option.writer, **option.base_config, **option.config)
        assert result.exit_code == 0, result.output
        assert result.stdout == expected
        assert expected != _anonymized(option.source, option.writer, **option.base_config)

    def test_a_network_file_reaches_the_library(self, tmp_path: Path) -> None:
        networks = tmp_path / "networks.txt"
        networks.write_text("203.0.114.0/24\n")
        source = _name_servers("203.0.114.1", "203.0.114.254")
        result = run(
            ["convert", "-i", "json", "-e", "json", "--anonymize-ips"]
            + ["--anonymize-network-file", str(networks), "--anonymize-salt", SALT],
            source,
        )
        expected = _anonymized(source, Format.JSON, ips=True, network_file=str(networks))
        assert result.exit_code == 0, result.output
        assert result.stdout == expected
        assert expected != _anonymized(source, Format.JSON, ips=True)

    def test_networks_auto_scans_the_input_for_subnets(self, tmp_path: Path) -> None:
        """`--anonymize-networks auto` keeps two hosts of one subnet in one subnet.

        `cli.py` is the one caller that hands the input text to the IP rule
        (`AnonymizeConfig.source_text`); without it the subnets go undetected.
        """
        source = tmp_path / "in.set"
        source.write_text(
            "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.1/24\n"
            "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.254/24\n"
        )
        result = run(
            ["convert", "-i", "set", "-e", "set", "--anonymize-ips"]
            + ["--anonymize-networks", "auto", "--anonymize-salt", "fixed", str(source)]
        )
        assert result.exit_code == 0
        addrs = [line.rsplit(" ", 1)[-1] for line in result.stdout.strip().splitlines()]
        assert addrs[0] != "203.0.114.1/24"
        assert addrs[0].endswith(".1/24")
        assert addrs[1].endswith(".254/24")
        assert addrs[0].rsplit(".", 1)[0] == addrs[1].rsplit(".", 1)[0]

    def test_a_config_file_reaches_the_library(self, tmp_path: Path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  salt: cfg-test\n")
        result = run(
            ["convert", "-i", "json", "-e", "json", "--anonymize-config", str(config_file)],
            NAME_SERVER,
        )
        assert result.exit_code == 0
        assert result.stdout == _anonymized(NAME_SERVER, Format.JSON, "cfg-test", ips=True)
        assert result.stdout != _anonymized(NAME_SERVER, Format.JSON)

    def test_a_salt_option_overrides_the_config_file(self, tmp_path: Path) -> None:
        """The precedence itself is `build_config_from_cli`'s, tested in
        `tests/unit/anonymize/test_config.py`."""
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  salt: file-salt\n")
        args = ["convert", "-i", "json", "-e", "json", "--anonymize-config", str(config_file)]
        from_file = run(args, NAME_SERVER)
        overridden = run([*args, "--anonymize-salt", "cli-salt"], NAME_SERVER)
        assert from_file.exit_code == overridden.exit_code == 0
        assert overridden.stdout == _anonymized(NAME_SERVER, Format.JSON, "cli-salt", ips=True)
        assert overridden.stdout != from_file.stdout

    @pytest.mark.parametrize("level", ["quiet", "normal", "debug"])
    def test_the_log_level_reaches_the_library(self, level: str) -> None:
        """Only `debug` adds the anonymizer's lines; the CLI prints them on stderr."""
        result = run(
            ["convert", "-i", "json", "-e", "json", "--anonymize-ips"]
            + ["--anonymize-salt", SALT, "--anonymize-log-level", level],
            NAME_SERVER,
        )
        expected = convert_config_result(
            NAME_SERVER,
            from_format=Format.JSON,
            to_format=Format.JSON,
            anon_config=AnonymizeConfig(ips=True, salt=SALT, log_level=level),
        )
        assert result.exit_code == 0
        assert result.stdout == expected.output
        assert result.stderr == "".join(d.render() + "\n" for d in expected.diagnostics)
        assert bool(result.stderr) == (level == "debug")
