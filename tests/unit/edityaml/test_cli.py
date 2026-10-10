"""Tests for edityaml CLI commands."""

from __future__ import annotations

import yaml
from click.testing import CliRunner

from junoscfg.cli import main


def _make_config_yaml() -> str:
    return yaml.dump(
        {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "overlay",
                                "neighbor": [
                                    {
                                        "name": "10.0.0.1",
                                        "description": "overlay: spine1",
                                    },
                                    {
                                        "name": "10.0.0.2",
                                        "description": "overlay: spine2",
                                    },
                                ],
                            }
                        ]
                    }
                },
                "system": {"host-name": "router1"},
            }
        }
    )


class TestEdityamlAddvarsHelp:
    def test_edityaml_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "--help"])
        assert result.exit_code == 0
        assert "addvars" in result.output

    def test_addvars_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "addvars", "--help"])
        assert result.exit_code == 0
        assert "--rules" in result.output or "-r" in result.output
        assert "--set" in result.output
        assert "--path" in result.output


class TestAddvarsWithRuleFile:
    def test_static_transform_from_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        runner = CliRunner()
        config_yaml = _make_config_yaml()
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

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
        rules_file.write_text(yaml.dump(rules))

        result = runner.invoke(
            main, ["edityaml", "addvars", "-r", str(rules_file), str(config_file)]
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        assert output["configuration"]["system"]["_ansible_managed"] is True

    def test_regex_extract_bgp_peername(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        runner = CliRunner()
        config_yaml = _make_config_yaml()
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        rules = {
            "rules": [
                {
                    "path": "configuration.protocols.bgp.group[*].neighbor[*]",
                    "transforms": [
                        {
                            "type": "regex_extract",
                            "source": "description",
                            "pattern": r"overlay: (\w+)",
                            "target": "_ansible_bgp_peername",
                        },
                    ],
                }
            ]
        }
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text(yaml.dump(rules))

        result = runner.invoke(
            main, ["edityaml", "addvars", "-r", str(rules_file), str(config_file)]
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        neighbors = output["configuration"]["protocols"]["bgp"]["group"][0]["neighbor"]
        assert neighbors[0]["_ansible_bgp_peername"] == "spine1"
        assert neighbors[1]["_ansible_bgp_peername"] == "spine2"


class TestAddvarsInline:
    def test_inline_static(self) -> None:
        runner = CliRunner()
        config_yaml = _make_config_yaml()
        result = runner.invoke(
            main,
            [
                "edityaml",
                "addvars",
                "--path",
                "configuration.system",
                "--set",
                "_managed=static(true)",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        assert output["configuration"]["system"]["_managed"] is True

    def test_inline_copy(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump(
            {
                "configuration": {
                    "interfaces": {
                        "interface": [
                            {"name": "ge-0/0/0", "unit": "0"},
                            {"name": "ge-0/0/1", "unit": "1"},
                        ]
                    }
                }
            }
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "addvars",
                "--path",
                "configuration.interfaces.interface[*]",
                "--set",
                "_intf=copy(name)",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        intfs = output["configuration"]["interfaces"]["interface"]
        assert intfs[0]["_intf"] == "ge-0/0/0"
        assert intfs[1]["_intf"] == "ge-0/0/1"

    def test_inline_bare_value(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"configuration": {"system": {"host-name": "r1"}}})
        result = runner.invoke(
            main,
            [
                "edityaml",
                "addvars",
                "--path",
                "configuration.system",
                "--set",
                "_env=production",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        assert output["configuration"]["system"]["_env"] == "production"

    def test_multiple_set_exprs(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"configuration": {"system": {"host-name": "r1"}}})
        result = runner.invoke(
            main,
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
            input=config_yaml,
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        assert output["configuration"]["system"]["_a"] == 1
        assert output["configuration"]["system"]["_b"] == 2


class TestAddvarsCombined:
    def test_file_rules_then_inline(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        runner = CliRunner()
        config_yaml = yaml.dump({"configuration": {"system": {"host-name": "r1"}}})
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

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
        rules_file.write_text(yaml.dump(rules))

        result = runner.invoke(
            main,
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
            ],
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        system = output["configuration"]["system"]
        assert system["_from_file"] == "yes"
        assert system["_from_inline"] == "also"


class TestAddvarsStdin:
    def test_reads_from_stdin(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"configuration": {"system": {"host-name": "r1"}}})
        result = runner.invoke(
            main,
            [
                "edityaml",
                "addvars",
                "--path",
                "configuration.system",
                "--set",
                "_flag=static(true)",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        output = yaml.safe_load(result.output)
        assert output["configuration"]["system"]["_flag"] is True


class TestAddvarsErrors:
    def test_no_rules_or_set_shows_error(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["edityaml", "addvars"],
            input="configuration:\n  system:\n    host-name: r1\n",
        )
        assert result.exit_code == 2

    def test_set_without_path_shows_error(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["edityaml", "addvars", "--set", "_foo=bar"],
            input="configuration:\n  system:\n    host-name: r1\n",
        )
        assert result.exit_code == 2


class TestAnsibilizeHelp:
    def test_ansibilize_listed_in_edityaml_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "--help"])
        assert result.exit_code == 0
        assert "ansibilize" in result.output

    def test_ansibilize_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "ansibilize", "--help"])
        assert result.exit_code == 0
        assert "-p" in result.output


class TestAnsibilizeCli:
    def test_basic_ansibilize_from_stdin(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"items": [{"name": "10.0.0.1", "desc": "a"}]})
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "-p",
                "addr:items[*].name",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        assert "---" in result.output
        parts = result.output.split("---\n")
        assert len(parts) == 2
        host = yaml.safe_load(parts[0])
        group = yaml.safe_load(parts[1])
        assert host["addr_0"] == "10.0.0.1"
        assert group["items"][0]["name"] == "{{ addr_0 }}"

    def test_ansibilize_from_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        config_yaml = yaml.dump({"items": [{"name": "10.0.0.1"}]})
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml)

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "-p",
                "addr:items[*].name",
                str(config_file),
            ],
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        host = yaml.safe_load(parts[0])
        assert host["addr_0"] == "10.0.0.1"

    def test_ansibilize_missing_required_options(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["edityaml", "ansibilize"],
            input="items:\n- name: a\n",
        )
        # Missing -p → error
        assert result.exit_code != 0

    def test_ansibilize_multi_pair(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump(
            {
                "configuration": {
                    "system": {"host-name": "router1"},
                    "interfaces": {
                        "interface": [
                            {"name": "xe-0/0/0", "description": "uplink"},
                        ]
                    },
                }
            }
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "-p",
                "junos_hostname:configuration.system.host-name",
                "-p",
                "intf_desc:configuration.interfaces.interface[*].description",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        assert len(parts) == 2
        host = yaml.safe_load(parts[0])
        group = yaml.safe_load(parts[1])
        assert host["junos_hostname"] == "router1"
        assert host["intf_desc_xe_0_0_0"] == "uplink"
        assert group["configuration"]["system"]["host-name"] == "{{ junos_hostname }}"
        intf = group["configuration"]["interfaces"]["interface"][0]
        assert intf["description"] == "{{ intf_desc_xe_0_0_0 }}"

    def test_ansibilize_bad_prefix_path_format(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["edityaml", "ansibilize", "-p", "no_colon_here"],
            input="items:\n- name: a\n",
        )
        assert result.exit_code == 2


class TestAnsibilizeRootOption:
    def test_root_option_descends_into_matching_key(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump(
            {
                "interfaces_cfg": {
                    "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]}
                }
            }
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "--root",
                "interfaces_*",
                "-p",
                "desc:interfaces.interface[*].description",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        host = yaml.safe_load(parts[0])
        group = yaml.safe_load(parts[1])
        assert host["desc_ge_0_0_0"] == "uplink"
        intf = group["interfaces_cfg"]["interfaces"]["interface"][0]
        assert intf["description"] == "{{ desc_ge_0_0_0 }}"

    def test_root_option_multiple_roots(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump(
            {
                "config_a": {"system": {"host-name": "r1"}},
                "config_b": {"system": {"host-name": "r2"}},
            }
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "--root",
                "config_a",
                "--root",
                "config_b",
                "-p",
                "host:system.host-name",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        group = yaml.safe_load(parts[1])
        assert group["config_a"]["system"]["host-name"] == "{{ host }}"
        assert group["config_b"]["system"]["host-name"] == "{{ host }}"

    def test_ansibilize_help_shows_root_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "ansibilize", "--help"])
        assert result.exit_code == 0
        assert "--root" in result.output


class TestAnsibilizeOffsetCli:
    def test_offset_basic_ipv4(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"items": [{"name": "10.0.2.64/31", "desc": "a"}]})
        result = runner.invoke(
            main,
            ["edityaml", "ansibilize", "-P", "addr:items[*].name"],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        assert len(parts) == 3
        host = yaml.safe_load(parts[0])
        offset = yaml.safe_load(parts[1])
        template = yaml.safe_load(parts[2])
        assert host["base_address_offset"] == 0
        assert "ipmath" in offset["addr_0"]
        assert template["items"][0]["name"] == "{{ addr_0 }}"

    def test_offset_ipv6(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"items": [{"name": "2001:db8::1:2e/112"}]})
        result = runner.invoke(
            main,
            ["edityaml", "ansibilize", "-P", "addr:items[*].name"],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        offset = yaml.safe_load(parts[1])
        assert "ipmath" in offset["addr_0"]
        assert "2001:db8::1:2e" in offset["addr_0"]

    def test_mixed_literal_and_offset(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump(
            {
                "system": {"host-name": "router04"},
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "10.0.2.64/31"}]}},
                                }
                            ],
                        }
                    ]
                },
            }
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "-p",
                "host:system.host-name",
                "-P",
                "addr:interfaces.interface[*].unit[*].family.*.address[*].name",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        assert len(parts) == 3
        host = yaml.safe_load(parts[0])
        offset = yaml.safe_load(parts[1])
        template = yaml.safe_load(parts[2])
        assert host["host"] == "router04"
        assert host["base_address_offset"] == 0
        assert "addr_ge_0_0_0_0_inet_0" in offset
        assert template["system"]["host-name"] == "{{ host }}"

    def test_offset_var_custom_name(self) -> None:
        runner = CliRunner()
        config_yaml = yaml.dump({"items": [{"name": "10.0.0.1/30"}]})
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "--offset-var",
                "my_offset",
                "-P",
                "addr:items[*].name",
            ],
            input=config_yaml,
        )
        assert result.exit_code == 0
        parts = result.output.split("---\n")
        host = yaml.safe_load(parts[0])
        offset = yaml.safe_load(parts[1])
        assert host["my_offset"] == 0
        assert "my_offset" in offset["addr_0"]

    def test_neither_literal_nor_offset_shows_error(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["edityaml", "ansibilize"],
            input="items:\n- name: a\n",
        )
        assert result.exit_code == 2

    def test_help_shows_offset_options(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "ansibilize", "--help"])
        assert result.exit_code == 0
        assert "-P" in result.output
        assert "--offset-var" in result.output
