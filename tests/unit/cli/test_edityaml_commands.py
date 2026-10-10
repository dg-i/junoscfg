"""`junoscfg edityaml addvars`, `ansibilize` and `rename-root`: input, options, exit codes.

The plumbing of addvars and ansibilize: what they read, which options reach
the library call, and how they exit. An ansibilize run prints exactly what the
library gives for the options' values; their behaviour is tested in
``tests/unit/edityaml/``. `rename-root` has no library function, its logic
lives in ``cli.py``, so its behaviour is tested here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import yaml
from click.testing import CliRunner

from junoscfg.cli import main
from junoscfg.edityaml import (
    ansibilize_multi,
    ansibilize_with_offset,
    format_output,
    format_output_with_offset,
)

if TYPE_CHECKING:
    from pathlib import Path


def run_cli(args: list[str], stdin: str | None = None) -> tuple[int, str]:
    result = CliRunner().invoke(main, args, input=stdin)
    return result.exit_code, result.output


def as_yaml(data: dict[str, Any]) -> str:
    """*data* as YAML in its own key order, so the CLI reads the same dict."""
    return yaml.dump(data, sort_keys=False)


SYSTEM = {"configuration": {"system": {"host-name": "r1"}}}


class TestHelp:
    @pytest.mark.parametrize("subcommand", ["addvars", "ansibilize", "rename-root"])
    def test_edityaml_help_lists_its_subcommands(self, subcommand: str) -> None:
        exit_code, output = run_cli(["edityaml", "--help"])
        assert exit_code == 0
        assert subcommand in output

    def test_addvars_help(self) -> None:
        exit_code, output = run_cli(["edityaml", "addvars", "--help"])
        assert exit_code == 0
        assert "--rules" in output or "-r" in output
        assert "--set" in output
        assert "--path" in output

    @pytest.mark.parametrize("option", ["-p", "--root", "-P", "--offset-var"])
    def test_ansibilize_help_lists_its_options(self, option: str) -> None:
        exit_code, output = run_cli(["edityaml", "ansibilize", "--help"])
        assert exit_code == 0
        assert option in output


class TestAddvars:
    def test_static_transform_from_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(as_yaml(SYSTEM))
        rules = {
            "rules": [
                {
                    "path": "configuration.system",
                    "transforms": [
                        {"type": "static", "target": "_ansible_managed", "value": True},
                    ],
                }
            ]
        }
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(as_yaml(rules))

        exit_code, output = run_cli(
            ["edityaml", "addvars", "-r", str(rules_file), str(config_file)]
        )
        assert exit_code == 0
        assert yaml.safe_load(output)["configuration"]["system"]["_ansible_managed"] is True

    def test_inline_static(self) -> None:
        """``--path`` with ``--set``, the configuration read from stdin."""
        exit_code, output = run_cli(
            [
                "edityaml",
                "addvars",
                "--path",
                "configuration.system",
                "--set",
                "_managed=static(true)",
            ],
            as_yaml(SYSTEM),
        )
        assert exit_code == 0
        assert yaml.safe_load(output)["configuration"]["system"]["_managed"] is True

    def test_multiple_set_exprs(self) -> None:
        exit_code, output = run_cli(
            [
                "edityaml",
                "addvars",
                "--path",
                "configuration.system",
                "--set",
                "_a=static(1)",
                "--set",
                "_b=static(2)",
            ],
            as_yaml(SYSTEM),
        )
        assert exit_code == 0
        system = yaml.safe_load(output)["configuration"]["system"]
        assert system["_a"] == 1
        assert system["_b"] == 2

    def test_file_rules_then_inline(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(as_yaml(SYSTEM))
        rules = {
            "rules": [
                {
                    "path": "configuration.system",
                    "transforms": [
                        {"type": "static", "target": "_from_file", "value": "yes"},
                    ],
                }
            ]
        }
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(as_yaml(rules))

        exit_code, output = run_cli(
            [
                "edityaml",
                "addvars",
                "-r",
                str(rules_file),
                "--path",
                "configuration.system",
                "--set",
                "_from_inline=also",
                str(config_file),
            ]
        )
        assert exit_code == 0
        system = yaml.safe_load(output)["configuration"]["system"]
        assert system["_from_file"] == "yes"
        assert system["_from_inline"] == "also"

    def test_no_rules_or_set_shows_error(self) -> None:
        exit_code, _ = run_cli(["edityaml", "addvars"], as_yaml(SYSTEM))
        assert exit_code == 2

    def test_set_without_path_shows_error(self) -> None:
        exit_code, _ = run_cli(["edityaml", "addvars", "--set", "_foo=bar"], as_yaml(SYSTEM))
        assert exit_code == 2

    def test_empty_input_prints_nothing(self) -> None:
        exit_code, output = run_cli(
            ["edityaml", "addvars", "--path", "configuration.system", "--set", "_a=static(1)"], ""
        )
        assert exit_code == 0
        assert output == ""


ITEMS = {"items": [{"name": "10.0.0.1", "desc": "a"}]}
INTERFACES_CFG = {
    "interfaces_cfg": {"interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]}}
}
TWO_CONFIGS = {
    "config_a": {"system": {"host-name": "r1"}},
    "config_b": {"system": {"host-name": "r2"}},
}
ROUTER = {
    "system": {"host-name": "router04"},
    "interfaces": {
        "interface": [
            {
                "name": "ge-0/0/0",
                "unit": [
                    {"name": "0", "family": {"inet": {"address": [{"name": "10.0.2.64/31"}]}}}
                ],
            }
        ]
    },
}
ADDRESSES = "interfaces.interface[*].unit[*].family.*.address[*].name"


class TestAnsibilize:
    def test_basic_ansibilize_from_stdin(self) -> None:
        exit_code, output = run_cli(
            ["edityaml", "ansibilize", "-p", "addr:items[*].name"], as_yaml(ITEMS)
        )
        assert exit_code == 0
        assert output == format_output(*ansibilize_multi(ITEMS, [("addr", "items[*].name")]))

    def test_ansibilize_from_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(as_yaml(ITEMS))
        exit_code, output = run_cli(
            ["edityaml", "ansibilize", "-p", "addr:items[*].name", str(config_file)]
        )
        assert exit_code == 0
        assert output == format_output(*ansibilize_multi(ITEMS, [("addr", "items[*].name")]))

    def test_empty_input_prints_nothing(self) -> None:
        exit_code, output = run_cli(["edityaml", "ansibilize", "-p", "addr:items[*].name"], "")
        assert exit_code == 0
        assert output == ""

    def test_ansibilize_multi_pair(self) -> None:
        data = {
            "configuration": {
                "system": {"host-name": "router1"},
                "interfaces": {"interface": [{"name": "xe-0/0/0", "description": "uplink"}]},
            }
        }
        pairs = [
            ("junos_hostname", "configuration.system.host-name"),
            ("intf_desc", "configuration.interfaces.interface[*].description"),
        ]
        args = ["edityaml", "ansibilize"]
        for prefix, path in pairs:
            args += ["-p", f"{prefix}:{path}"]
        exit_code, output = run_cli(args, as_yaml(data))
        assert exit_code == 0
        assert output == format_output(*ansibilize_multi(data, pairs))

    @pytest.mark.parametrize(
        ("data", "roots", "pair"),
        [
            (INTERFACES_CFG, ["interfaces_*"], ("desc", "interfaces.interface[*].description")),
            (TWO_CONFIGS, ["config_a", "config_b"], ("host", "system.host-name")),
        ],
        ids=["descends-into-matching-key", "multiple-roots"],
    )
    def test_root_option(
        self, data: dict[str, Any], roots: list[str], pair: tuple[str, str]
    ) -> None:
        """Each ``--root`` is one root-key glob."""
        args = ["edityaml", "ansibilize", "-p", ":".join(pair)]
        for root in roots:
            args += ["--root", root]
        exit_code, output = run_cli(args, as_yaml(data))
        assert exit_code == 0
        assert output == format_output(*ansibilize_multi(data, [pair], root_keys=roots))

    def test_ansibilize_bad_prefix_path_format(self) -> None:
        exit_code, _ = run_cli(
            ["edityaml", "ansibilize", "-p", "no_colon_here"], "items:\n- name: a\n"
        )
        assert exit_code == 2

    def test_neither_literal_nor_offset_shows_error(self) -> None:
        exit_code, _ = run_cli(["edityaml", "ansibilize"], "items:\n- name: a\n")
        assert exit_code == 2


class TestAnsibilizeOffset:
    def test_offset_basic_ipv4(self) -> None:
        """``-P`` alone: three documents, host_vars, offset vars and the template."""
        data = {"items": [{"name": "10.0.2.64/31", "desc": "a"}]}
        exit_code, output = run_cli(
            ["edityaml", "ansibilize", "-P", "addr:items[*].name"], as_yaml(data)
        )
        assert exit_code == 0
        assert output == format_output_with_offset(
            *ansibilize_with_offset(data, [], [("addr", "items[*].name")])
        )

    def test_mixed_literal_and_offset(self) -> None:
        exit_code, output = run_cli(
            ["edityaml", "ansibilize", "-p", "host:system.host-name", "-P", f"addr:{ADDRESSES}"],
            as_yaml(ROUTER),
        )
        assert exit_code == 0
        assert output == format_output_with_offset(
            *ansibilize_with_offset(ROUTER, [("host", "system.host-name")], [("addr", ADDRESSES)])
        )

    def test_offset_var_custom_name(self) -> None:
        data = {"items": [{"name": "10.0.0.1/30"}]}
        exit_code, output = run_cli(
            ["edityaml", "ansibilize", "--offset-var", "my_offset", "-P", "addr:items[*].name"],
            as_yaml(data),
        )
        assert exit_code == 0
        assert output == format_output_with_offset(
            *ansibilize_with_offset(data, [], [("addr", "items[*].name")], offset_var="my_offset")
        )

    def test_a_value_of_no_known_type_exits_1(self) -> None:
        """The library's ValueError is reported as a usage-free error, exit 1."""
        exit_code, output = run_cli(
            ["edityaml", "ansibilize", "-P", "addr:items[*].name"], "items:\n- name: hello\n"
        )
        assert exit_code == 1
        assert "hello" in output


GROUPED = {
    "configuration": {
        "@": {"junos:commit-user": "admin"},
        "groups": [
            {"name": "ansible-managed", "interfaces": {"ge-0/0/0": {"unit": 0}}},
        ],
    }
}


class TestRenameRoot:
    """`rename-root` renames the top-level key, or makes a subtree the document.

    Its logic is in ``cli.py`` only, so these are its behaviour tests too.
    """

    def test_the_default_from_key_is_configuration(self) -> None:
        exit_code, output = run_cli(
            ["edityaml", "rename-root", "--to", "junos_config"], as_yaml(SYSTEM)
        )
        assert exit_code == 0
        assert yaml.safe_load(output) == {"junos_config": SYSTEM["configuration"]}

    def test_an_explicit_from_key(self) -> None:
        data = {"my_root": {"interfaces": {"ge-0/0/0": "up"}}}
        exit_code, output = run_cli(
            ["edityaml", "rename-root", "--from", "my_root", "--to", "device_config"],
            as_yaml(data),
        )
        assert exit_code == 0
        assert yaml.safe_load(output) == {"device_config": data["my_root"]}

    def test_a_missing_from_key_exits_two(self) -> None:
        result = CliRunner().invoke(
            main, ["edityaml", "rename-root", "--to", "new_name"], input="other_key:\n  value: 1\n"
        )
        assert result.exit_code == 2
        assert result.stdout == ""
        assert result.stderr == "Error: key 'configuration' not found in input.\n"

    def test_a_file_argument_is_read(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(as_yaml(SYSTEM))
        exit_code, output = run_cli(
            ["edityaml", "rename-root", "--to", "junos_config", str(config_file)]
        )
        assert exit_code == 0
        assert yaml.safe_load(output) == {"junos_config": SYSTEM["configuration"]}

    def test_empty_input_prints_nothing(self) -> None:
        exit_code, output = run_cli(["edityaml", "rename-root", "--to", "junos_config"], "")
        assert exit_code == 0
        assert output == ""

    def test_the_other_top_level_keys_stay_in_their_place(self) -> None:
        data = {**SYSTEM, "metadata": {"version": 1}}
        exit_code, output = run_cli(
            ["edityaml", "rename-root", "--to", "junos_config"], as_yaml(data)
        )
        assert exit_code == 0
        renamed = yaml.safe_load(output)
        assert list(renamed) == ["junos_config", "metadata"]
        assert renamed == {"junos_config": SYSTEM["configuration"], "metadata": {"version": 1}}

    def test_a_path_from_makes_the_subtree_the_document(self) -> None:
        """A `--from` with dots or brackets is a path expression, as in ansibilize."""
        exit_code, output = run_cli(
            [
                "edityaml",
                "rename-root",
                "--from",
                "configuration.groups[ansible-managed].interfaces",
                "--to",
                "junos_interfaces",
            ],
            as_yaml(GROUPED),
        )
        assert exit_code == 0
        assert yaml.safe_load(output) == {"junos_interfaces": {"ge-0/0/0": {"unit": 0}}}

    def test_a_path_from_that_matches_nothing_exits_two(self) -> None:
        path = "configuration.groups[other-group].interfaces"
        result = CliRunner().invoke(
            main,
            ["edityaml", "rename-root", "--from", path, "--to", "junos_interfaces"],
            input=as_yaml(GROUPED),
        )
        assert result.exit_code == 2
        assert result.stdout == ""
        assert result.stderr == f"Error: path '{path}' not found in input.\n"
