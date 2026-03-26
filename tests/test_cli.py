"""Tests for CLI interface."""

from __future__ import annotations

import json

from click.testing import CliRunner

from junoscfg.cli import main


class TestCli:
    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.5.4" in result.output

    def test_no_mode_shows_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Junoscfg" in result.output

    def test_convert_no_export_shows_error(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "-i", "json"], input="{}")
        assert result.exit_code == 2
        assert "Error" in result.output

    def test_display_set_from_json_stdin(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "router1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "set"], input=json_input)
        assert result.exit_code == 0
        assert "set system host-name router1" in result.output

    def test_display_set_from_xml_stdin(self) -> None:
        runner = CliRunner()
        xml_input = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = runner.invoke(main, ["-i", "xml", "-e", "set"], input=xml_input)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output

    def test_structured_from_set_stdin(self) -> None:
        runner = CliRunner()
        set_input = "set system host-name router1"
        result = runner.invoke(main, ["-i", "set", "-e", "structured"], input=set_input)
        assert result.exit_code == 0
        assert "system host-name" in result.output
        assert "host-name router1;" in result.output

    def test_display_set_from_structured_stdin(self) -> None:
        runner = CliRunner()
        config = "system {\n    host-name foo;\n}"
        result = runner.invoke(main, ["-i", "structured", "-e", "set"], input=config)
        assert result.exit_code == 0
        assert "set system host-name foo" in result.output

    def test_structured_from_json_stdin(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "router1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "structured"], input=json_input)
        assert result.exit_code == 0
        assert "system host-name" in result.output
        assert "host-name router1;" in result.output

    def test_display_set_from_json_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        runner = CliRunner()
        json_file = tmp_path / "config.json"
        json_file.write_text('{"configuration": {"system": {"host-name": "router1"}}}')
        result = runner.invoke(main, ["-i", "json", "-e", "set", str(json_file)])
        assert result.exit_code == 0
        assert "set system host-name router1" in result.output

    def test_empty_input(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["-i", "json", "-e", "set"], input="")
        assert result.exit_code == 0
        assert result.output == ""

    def test_display_set_from_yaml_stdin(self) -> None:
        runner = CliRunner()
        yaml_input = "configuration:\n  system:\n    host-name: router1\n"
        result = runner.invoke(main, ["-i", "yaml", "-e", "set"], input=yaml_input)
        assert result.exit_code == 0
        assert "set system host-name router1" in result.output

    def test_structured_from_yaml_stdin(self) -> None:
        runner = CliRunner()
        yaml_input = "configuration:\n  system:\n    host-name: router1\n"
        result = runner.invoke(main, ["-i", "yaml", "-e", "structured"], input=yaml_input)
        assert result.exit_code == 0
        assert "system host-name" in result.output
        assert "host-name router1;" in result.output

    def test_yaml_from_json_stdin(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "router1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "yaml"], input=json_input)
        assert result.exit_code == 0
        assert "configuration:" in result.output
        assert "host-name: router1" in result.output

    def test_yaml_from_xml_stdin(self) -> None:
        runner = CliRunner()
        xml_input = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = runner.invoke(main, ["-i", "xml", "-e", "yaml"], input=xml_input)
        assert result.exit_code == 0
        assert "configuration:" in result.output
        assert "host-name: r1" in result.output

    def test_auto_detect_set_input(self) -> None:
        runner = CliRunner()
        set_input = "set system host-name router1"
        result = runner.invoke(main, ["-e", "structured"], input=set_input)
        assert result.exit_code == 0
        assert "host-name router1;" in result.output

    def test_auto_detect_structured_input(self) -> None:
        runner = CliRunner()
        config = "system {\n    host-name foo;\n}"
        result = runner.invoke(main, ["-e", "set"], input=config)
        assert result.exit_code == 0
        assert "set system host-name foo" in result.output

    def test_auto_detect_json_input(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = runner.invoke(main, ["-e", "set"], input=json_input)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output

    def test_auto_detect_xml_input(self) -> None:
        runner = CliRunner()
        xml_input = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = runner.invoke(main, ["-e", "set"], input=xml_input)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output


class TestCliPathFilter:
    """Tests for --path and --relative CLI options."""

    def test_set_path_filter(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"host-name": "r1",'
            ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
        )
        result = runner.invoke(
            main, ["-i", "json", "-e", "set", "--path", "system.syslog"], input=json_input
        )
        assert result.exit_code == 0
        assert "syslog" in result.output
        assert "host-name" not in result.output
        assert "interfaces" not in result.output

    def test_set_path_filter_relative(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"host-name": "r1",'
            ' "syslog": {"file": [{"name": "messages"}]}}}}'
        )
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "set", "--path", "system.syslog", "--relative"],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "system" not in result.output
        assert "syslog" not in result.output
        assert "file messages" in result.output

    def test_structured_path_filter(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"host-name": "r1",'
            ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
        )
        result = runner.invoke(
            main, ["-i", "json", "-e", "structured", "--path", "system"], input=json_input
        )
        assert result.exit_code == 0
        assert "system" in result.output
        assert "interfaces" not in result.output

    def test_structured_path_filter_relative(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"host-name": "r1",'
            ' "syslog": {"file": [{"name": "messages"}]}}}}'
        )
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "structured", "--path", "system", "--relative"],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "system" not in result.output
        assert "host-name r1;" in result.output

    def test_yaml_path_filter(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "r1"}, "interfaces": {}}}'
        result = runner.invoke(
            main, ["-i", "json", "-e", "yaml", "--path", "system"], input=json_input
        )
        assert result.exit_code == 0
        assert "host-name" in result.output
        assert "interfaces" not in result.output

    def test_yaml_path_filter_relative(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "r1"}, "interfaces": {}}}'
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "yaml", "--path", "system", "--relative"],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "host-name: r1" in result.output
        assert "system" not in result.output
        assert "configuration" not in result.output

    def test_relative_without_path_shows_error(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "set", "--relative"], input=json_input)
        assert result.exit_code == 2
        assert "--relative requires --path" in result.output

    def test_json_path_filter(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"host-name": "r1",'
            ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
        )
        result = runner.invoke(
            main, ["-i", "json", "-e", "json", "--path", "system"], input=json_input
        )
        assert result.exit_code == 0
        assert '"system"' in result.output
        assert '"interfaces"' not in result.output

    def test_json_path_filter_relative(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"host-name": "r1",'
            ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
        )
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "json", "--path", "system", "--relative"],
            input=json_input,
        )
        assert result.exit_code == 0
        assert '"host-name"' in result.output
        assert '"configuration"' not in result.output
        assert '"system"' not in result.output

    def test_path_not_found_empty_output(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = runner.invoke(
            main, ["-i", "json", "-e", "set", "--path", "nonexistent"], input=json_input
        )
        assert result.exit_code == 0
        assert result.output == ""


class TestCliIdentityConversion:
    """Identity conversions via CLI."""

    def test_json_to_json(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = runner.invoke(main, ["-i", "json", "-e", "json"], input=json_input)
        assert result.exit_code == 0
        assert '"host-name": "r1"' in result.output

    def test_set_to_set(self) -> None:
        runner = CliRunner()
        set_input = "set system host-name r1"
        result = runner.invoke(main, ["-i", "set", "-e", "set"], input=set_input)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output

    def test_yaml_to_yaml(self) -> None:
        runner = CliRunner()
        yaml_input = "configuration:\n  system:\n    host-name: r1\n"
        result = runner.invoke(main, ["-i", "yaml", "-e", "yaml"], input=yaml_input)
        assert result.exit_code == 0
        assert "host-name: r1" in result.output

    def test_structured_to_structured(self) -> None:
        runner = CliRunner()
        struct_input = "system {\n    host-name r1;\n}"
        result = runner.invoke(main, ["-i", "structured", "-e", "structured"], input=struct_input)
        assert result.exit_code == 0
        assert "host-name r1;" in result.output


class TestCliConfAlias:
    """Tests for 'conf' as CLI alias for 'structured'."""

    def test_conf_as_import(self) -> None:
        runner = CliRunner()
        struct_input = "system {\n    host-name r1;\n}"
        result = runner.invoke(main, ["-i", "conf", "-e", "set"], input=struct_input)
        assert result.exit_code == 0
        assert "set system host-name r1" in result.output

    def test_conf_as_export(self) -> None:
        runner = CliRunner()
        set_input = "set system host-name r1"
        result = runner.invoke(main, ["-i", "set", "-e", "conf"], input=set_input)
        assert result.exit_code == 0
        assert "host-name r1;" in result.output

    def test_conf_as_both(self) -> None:
        runner = CliRunner()
        struct_input = "system {\n    host-name r1;\n}"
        result = runner.invoke(main, ["-i", "conf", "-e", "conf"], input=struct_input)
        assert result.exit_code == 0
        assert "host-name r1;" in result.output


class TestCliAnonymize:
    """Tests for --anonymize-* CLI options on the convert command."""

    def test_anonymize_ips_flag(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "json", "--anonymize-ips", "--anonymize-salt", "cli-test"],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "8.8.8.8" not in result.output
        assert "name-server" in result.output

    def test_anonymize_ips_with_set_output(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "set", "--anonymize-ips", "--anonymize-salt", "set-test"],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "set system name-server" in result.output
        assert "8.8.8.8" not in result.output

    def test_anonymize_salt_deterministic(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
        result1 = runner.invoke(
            main,
            ["-i", "json", "-e", "json", "--anonymize-ips", "--anonymize-salt", "fixed"],
            input=json_input,
        )
        result2 = runner.invoke(
            main,
            ["-i", "json", "-e", "json", "--anonymize-ips", "--anonymize-salt", "fixed"],
            input=json_input,
        )
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert result1.output == result2.output

    def test_anonymize_include(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]},'
            '"interfaces": {"interface": [{"name": "ge-0/0/0", "unit": [{"name": "0",'
            '"family": {"inet": {"address": [{"name": "10.1.2.3/24"}]}}}]}]}}}'
        )
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-ips",
                "--anonymize-salt",
                "incl",
                "--anonymize-include",
                "interfaces",
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        # name-server should NOT be anonymized (outside include scope)
        assert "8.8.8.8" in result.output
        # Interface IP SHOULD be anonymized
        assert "10.1.2.3/24" not in result.output

    def test_anonymize_exclude(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]},'
            '"interfaces": {"interface": [{"name": "ge-0/0/0", "unit": [{"name": "0",'
            '"family": {"inet": {"address": [{"name": "10.1.2.3/24"}]}}}]}]}}}'
        )
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-ips",
                "--anonymize-salt",
                "excl",
                "--anonymize-exclude",
                "system",
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        # name-server should NOT be anonymized (excluded)
        assert "8.8.8.8" in result.output
        # Interface IP SHOULD be anonymized
        assert "10.1.2.3/24" not in result.output

    def test_anonymize_preserve_prefixes(self) -> None:
        runner = CliRunner()
        json_input = (
            '{"configuration": {"interfaces": {"interface": [{"name": "ge-0/0/0",'
            '"unit": [{"name": "0", "family": {"inet": '
            '{"address": [{"name": "10.1.2.3/24"}]}}}]}]}}}'
        )
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-ips",
                "--anonymize-salt",
                "pp",
                "--anonymize-preserve-prefixes",
                "10.1.0.0/16",
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        # IP in preserved prefix should be unchanged
        assert "10.1.2.3/24" in result.output

    def test_anonymize_without_any_flag_no_change(self) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
        result = runner.invoke(
            main,
            ["-i", "json", "-e", "json"],
            input=json_input,
        )
        assert result.exit_code == 0
        # No anonymization: IP should be unchanged
        assert "8.8.8.8" in result.output

    def test_anonymize_ips_in_strings(self) -> None:
        runner = CliRunner()
        json_input = json.dumps(
            {
                "configuration": {
                    "security": {
                        "ssh-known-hosts": {
                            "host": [{"name": "server.example.com,10.1.2.3"}],
                        },
                    },
                },
            }
        )
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-ips",
                "--anonymize-ips-in-strings",
                "--anonymize-salt",
                "str-cli",
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "10.1.2.3" not in result.output
        assert "server.example.com," in result.output

    def test_anonymize_as_numbers_in_strings_flag(self) -> None:
        """--anonymize-as-numbers-in-strings replaces AS numbers embedded in strings."""
        runner = CliRunner()
        json_input = json.dumps(
            {
                "configuration": {
                    "protocols": {
                        "bgp": {
                            "group": [
                                {
                                    "name": "inet-Upstream-AS64497",
                                    "peer-as": "64497",
                                },
                            ],
                        },
                    },
                },
            }
        )
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-as-numbers",
                "64497",
                "--anonymize-as-numbers-in-strings",
                "--anonymize-salt",
                "as-str-cli",
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "64497" not in result.output

    def test_anonymize_help_shows_options(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0
        assert "--anonymize-ips" in result.output
        assert "--anonymize-salt" in result.output
        assert "--anonymize-include" in result.output
        assert "--anonymize-exclude" in result.output


class TestCliAnonymizeDumpRevert:
    """Tests for --anonymize-dump-map, --anonymize-revert-map, --anonymize-config."""

    def test_dump_map_writes_file(self, tmp_path) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
        map_file = tmp_path / "map.json"
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-ips",
                "--anonymize-salt",
                "dump-test",
                "--anonymize-dump-map",
                str(map_file),
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "8.8.8.8" not in result.output
        assert map_file.exists()
        import json as json_mod

        mapping = json_mod.loads(map_file.read_text())
        assert "ip" in mapping
        assert len(mapping["ip"]) > 0

    def test_revert_map_restores_originals(self, tmp_path) -> None:
        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'

        # Step 1: anonymize and dump the map
        map_file = tmp_path / "map.json"
        result1 = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-ips",
                "--anonymize-salt",
                "revert-test",
                "--anonymize-dump-map",
                str(map_file),
            ],
            input=json_input,
        )
        assert result1.exit_code == 0
        anon_output = result1.output
        assert "8.8.8.8" not in anon_output

        # Step 2: revert using the map
        result2 = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-revert-map",
                str(map_file),
            ],
            input=anon_output,
        )
        assert result2.exit_code == 0
        assert "8.8.8.8" in result2.output

    def test_config_file(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  salt: cfg-test\n")

        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-config",
                str(config_file),
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "8.8.8.8" not in result.output

    def test_config_file_with_cli_override(self, tmp_path) -> None:
        config_file = tmp_path / "anon.yaml"
        config_file.write_text("anonymize:\n  ips: true\n  salt: file-salt\n")

        runner = CliRunner()
        json_input = '{"configuration": {"system": {"name-server": [{"name": "8.8.8.8"}]}}}'

        # With file salt
        result1 = runner.invoke(
            main,
            ["-i", "json", "-e", "json", "--anonymize-config", str(config_file)],
            input=json_input,
        )
        # With CLI salt override
        result2 = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-config",
                str(config_file),
                "--anonymize-salt",
                "cli-salt",
            ],
            input=json_input,
        )
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        # Different salts should produce different output
        assert result1.output != result2.output

    def test_anonymize_all_flag(self) -> None:
        runner = CliRunner()
        json_input = json.dumps(
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
                    },
                },
            }
        )
        result = runner.invoke(
            main,
            [
                "-i",
                "json",
                "-e",
                "json",
                "--anonymize-all",
                "--anonymize-salt",
                "all-test",
            ],
            input=json_input,
        )
        assert result.exit_code == 0
        assert "8.8.8.8" not in result.output
        assert "$6$abc123$xyz" not in result.output


class TestCliHelp:
    """Tests for -h, -?, and --help options."""

    def test_main_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Junoscfg" in result.output

    def test_main_h(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["-h"])
        assert result.exit_code == 0
        assert "Junoscfg" in result.output

    def test_main_question_mark(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["-?"])
        assert result.exit_code == 0
        assert "Junoscfg" in result.output

    def test_convert_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0
        assert "Convert" in result.output

    def test_convert_h(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "-h"])
        assert result.exit_code == 0
        assert "Convert" in result.output

    def test_convert_question_mark(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["convert", "-?"])
        assert result.exit_code == 0
        assert "Convert" in result.output


class TestFullHelp:
    """Tests for the fullhelp command."""

    def test_fullhelp(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["fullhelp"])
        assert result.exit_code == 0
        for keyword in ("convert", "addvars", "ansibilize", "generate", "makedoc", "info"):
            assert keyword in result.output

    def test_fullhelp_contains_all_sections(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["fullhelp"])
        assert result.exit_code == 0
        expected_headers = [
            "junoscfg\n",
            "junoscfg convert\n",
            "junoscfg edityaml\n",
            "junoscfg edityaml addvars\n",
            "junoscfg edityaml ansibilize\n",
            "junoscfg edityaml rename-root\n",
            "junoscfg schema\n",
            "junoscfg schema generate\n",
            "junoscfg schema makedoc\n",
            "junoscfg schema info\n",
        ]
        for header in expected_headers:
            assert header in result.output, f"Missing section header: {header.strip()}"


class TestCliRenameRoot:
    """Tests for edityaml rename-root command."""

    def test_rename_root_default_from(self) -> None:
        runner = CliRunner()
        yaml_input = "configuration:\n  system:\n    host-name: r1\n"
        result = runner.invoke(
            main, ["edityaml", "rename-root", "--to", "junos_config"], input=yaml_input
        )
        assert result.exit_code == 0
        assert "junos_config:" in result.output
        assert "configuration:" not in result.output
        assert "host-name: r1" in result.output

    def test_rename_root_explicit_from(self) -> None:
        runner = CliRunner()
        yaml_input = "my_root:\n  interfaces:\n    ge-0/0/0: up\n"
        result = runner.invoke(
            main,
            ["edityaml", "rename-root", "--from", "my_root", "--to", "device_config"],
            input=yaml_input,
        )
        assert result.exit_code == 0
        assert "device_config:" in result.output
        assert "my_root:" not in result.output
        assert "ge-0/0/0: up" in result.output

    def test_rename_root_missing_key_error(self) -> None:
        runner = CliRunner()
        yaml_input = "other_key:\n  value: 1\n"
        result = runner.invoke(
            main, ["edityaml", "rename-root", "--to", "new_name"], input=yaml_input
        )
        assert result.exit_code == 2
        assert "configuration" in result.output
        assert "not found" in result.output

    def test_rename_root_stdin(self) -> None:
        runner = CliRunner()
        yaml_input = "configuration:\n  system:\n    host-name: r1\n"
        result = runner.invoke(
            main, ["edityaml", "rename-root", "--to", "device_config"], input=yaml_input
        )
        assert result.exit_code == 0
        assert "device_config:" in result.output
        assert "host-name: r1" in result.output

    def test_rename_root_from_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        runner = CliRunner()
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("configuration:\n  system:\n    host-name: r1\n")
        result = runner.invoke(
            main, ["edityaml", "rename-root", "--to", "junos_config", str(yaml_file)]
        )
        assert result.exit_code == 0
        assert "junos_config:" in result.output

    def test_rename_root_preserves_other_keys(self) -> None:
        runner = CliRunner()
        yaml_input = "configuration:\n  system:\n    host-name: r1\nmetadata:\n  version: 1\n"
        result = runner.invoke(
            main, ["edityaml", "rename-root", "--to", "junos_config"], input=yaml_input
        )
        assert result.exit_code == 0
        assert "junos_config:" in result.output
        assert "metadata:" in result.output
        assert "configuration:" not in result.output

    def test_rename_root_dotted_path_extracts_subtree(self) -> None:
        runner = CliRunner()
        yaml_input = (
            "configuration:\n"
            "  '@':\n"
            "    junos:commit-seconds: '1771029110'\n"
            "    junos:commit-localtime: 2026-02-14 00:31:50 UTC\n"
            "    junos:commit-user: admin\n"
            "  groups:\n"
            "  - name: ansible-managed\n"
            "    interfaces:\n"
            "      ge-0/0/0:\n"
            "        unit: 0\n"
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "rename-root",
                "--from",
                "configuration.groups[ansible-managed].interfaces",
                "--to",
                "junos_interfaces",
            ],
            input=yaml_input,
        )
        assert result.exit_code == 0
        assert "junos_interfaces:" in result.output
        assert "ge-0/0/0:" in result.output
        assert "configuration:" not in result.output
        assert "groups:" not in result.output

    def test_rename_root_dotted_path_no_match(self) -> None:
        runner = CliRunner()
        yaml_input = (
            "configuration:\n"
            "  groups:\n"
            "  - name: other-group\n"
            "    interfaces:\n"
            "      ge-0/0/0:\n"
            "        unit: 0\n"
        )
        result = runner.invoke(
            main,
            [
                "edityaml",
                "rename-root",
                "--from",
                "configuration.groups[ansible-managed].interfaces",
                "--to",
                "junos_interfaces",
            ],
            input=yaml_input,
        )
        assert result.exit_code == 2
        assert "not found" in result.output
