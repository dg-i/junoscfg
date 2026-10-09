"""Tests for CLI validation and schema commands."""

from __future__ import annotations

from click.testing import CliRunner

from junoscfg.cli import main
from junoscfg.validate.grammar_generator import generate_lark_grammar
from junoscfg.validate.schema_node import SchemaNode


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

    def test_validate_set_with_multiple_siblings(self, tmp_path):
        server = SchemaNode(
            name="server",
            is_list=True,
            children={
                "version": SchemaNode(name="version", is_leaf=True),
                "prefer": SchemaNode(name="prefer", is_presence=True),
            },
        )
        server.flags.add("oneliner")
        root = SchemaNode(
            name="configuration",
            children={
                "system": SchemaNode(
                    name="system",
                    children={"ntp": SchemaNode(name="ntp", children={"server": server})},
                )
            },
        )
        (tmp_path / "junos-set.lark").write_text(generate_lark_grammar(root), encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["-v", "-i", "set", "--artifacts", str(tmp_path)],
            input="set system ntp server 198.51.100.1 version 4 prefer",
        )
        assert result.exit_code == 0, result.output

    def test_validate_json_with_an_as_list_reference(self):
        """Spec: identifier-key-fields, validation/keyed-entries. Bundled artefacts."""
        import json

        def document(entry: dict) -> str:
            return json.dumps(
                {
                    "configuration": {
                        "policy-options": {
                            "policy-statement": [
                                {
                                    "name": "SAMPLE-POLICY",
                                    "term": [
                                        {"name": "T1", "from": {"as-path-neighbors": [entry]}}
                                    ],
                                }
                            ]
                        }
                    }
                }
            )

        runner = CliRunner()
        good = document({"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"})
        result = runner.invoke(main, ["-v", "-i", "json"], input=good)
        assert result.exit_code == 0, result.output
        bad = document({"name": "as-list"})
        result = runner.invoke(main, ["-v", "-i", "json"], input=bad)
        assert result.exit_code != 0, result.output

    def test_validate_set_with_an_as_list_reference(self):
        """Spec: identifier-key-fields, set-command-validation. Bundled grammar."""
        term = "set policy-options policy-statement SAMPLE-POLICY term T1 from"
        runner = CliRunner()
        for line in (
            f"{term} as-path-neighbors as-list SAMPLE-AS-LIST",
            f"{term} as-path-origins as-list-group SAMPLE-ASG",
            f"{term} route-filter 198.51.100.0/24 exact accept",
        ):
            result = runner.invoke(main, ["-v", "-i", "set"], input=line + "\n")
            assert result.exit_code == 0, (line, result.output)
        for line in (
            f"{term} as-path-neighbors as-list",
            f"{term} as-path-neighbors as-list SAMPLE-AS-LIST SAMPLE-EXTRA",
        ):
            result = runner.invoke(main, ["-v", "-i", "set"], input=line + "\n")
            assert result.exit_code != 0, (line, result.output)


class TestCliSchemaInfo:
    def test_schema_info(self, artifacts_dir):
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "info", "--artifacts", artifacts_dir])
        assert result.exit_code == 0
        assert "21.4R0" in result.output


class TestSetBracketSyntaxRejection:
    def test_validation_only_exits_one_with_complete_diagnostic(self, artifacts_dir: str) -> None:
        runner = CliRunner()
        line = "set system apply-groups [ foo bar ]"

        result = runner.invoke(
            main,
            ["-v", "-i", "set", "--artifacts", artifacts_dir],
            input=line,
        )

        assert result.exit_code == 1
        assert f"Unsupported bracket syntax in set input on line 1:\n{line}" in result.output


# ── identifier-key-fields: CLI `-v` on keyed entries (bundled artefacts) ──


def _validate(fmt: str, text: str):
    return CliRunner().invoke(main, ["-v", "-i", fmt], input=text)


class TestCliValidationOfKeyedEntries:
    """Spec: identifier-key-fields, validation/keyed-entries and
    set-command-validation. The delta's two test ids live in
    `TestCliValidation`; these extend them to the other keyed lists."""

    def test_validate_yaml_with_an_as_list_reference(self) -> None:
        import yaml

        document = {
            "configuration": {
                "policy-options": {
                    "policy-statement": [
                        {
                            "name": "SAMPLE-POLICY",
                            "from": {
                                "as-path-origins": [
                                    {"list-type": "as-list-group", "list-name": "SAMPLE-ASG"}
                                ]
                            },
                        }
                    ]
                }
            }
        }
        assert _validate("yaml", yaml.safe_dump(document)).exit_code == 0
        document["configuration"]["policy-options"]["policy-statement"][0]["from"][
            "as-path-origins"
        ] = [{"name": "as-list-group"}]
        assert _validate("yaml", yaml.safe_dump(document)).exit_code != 0
