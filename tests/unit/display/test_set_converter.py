"""Tests for structured-to-set converter (SetConverter)."""

from __future__ import annotations

import json

import pytest

from junoscfg import Format, convert_config
from junoscfg.display import SetConverter
from tests.support.devices import example, recorded_lines


def struct_to_set(config: str) -> str:
    return SetConverter(config).to_set()


class TestStructuredBracketLists:
    def test_structured_bracket_list_emits_repeated_set_commands(self) -> None:
        config = (
            "interfaces {\n"
            "    ge-0/0/0 {\n"
            "        unit 0 {\n"
            "            family ethernet-switching {\n"
            "                vlan {\n"
            "                    members [ v10 v20 ];\n"
            "                }\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "}\n"
        )

        result = struct_to_set(config)

        assert result.splitlines() == [
            "set interfaces ge-0/0/0 unit 0 family ethernet-switching vlan members v10",
            "set interfaces ge-0/0/0 unit 0 family ethernet-switching vlan members v20",
        ]


class TestSetConverter:
    def test_simple_structured(self) -> None:
        config = "interfaces {\n    ge-0/0/0 {\n        description uplink;\n    }\n}"
        result = struct_to_set(config)
        assert result == "set interfaces ge-0/0/0 description uplink\n"

    def test_deactivate_from_inactive_prefix(self) -> None:
        config = (
            "interfaces {\n"
            "    ge-0/0/0 {\n"
            "        inactive: unit 0 {\n"
            "            family inet {\n"
            "                dhcp;\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "}"
        )
        result = struct_to_set(config)
        assert "set interfaces ge-0/0/0 unit 0 family inet dhcp\n" in result
        assert "deactivate interfaces ge-0/0/0 unit 0\n" in result

    def test_replace_tag_stripped(self) -> None:
        config = (
            "interfaces {\n"
            "    ge-0/0/0 {\n"
            "        replace: unit 0 {\n"
            "            family inet {\n"
            "                replace: dhcp;\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "}"
        )
        result = struct_to_set(config)
        assert "set interfaces ge-0/0/0 unit 0 family inet dhcp\n" in result
        assert "replace:" not in result

    def test_bracket_expansion(self) -> None:
        config = "snmp {\n    apply-groups [ foo bar ];\n}"
        result = struct_to_set(config)
        assert "set snmp apply-groups foo\n" in result
        assert "set snmp apply-groups bar\n" in result

    def test_bracket_expansion_with_quoted_brackets(self) -> None:
        """Brackets inside quoted strings don't break bracket expansion."""
        config = (
            "policy-options {\n"
            '    community FOO members [ "64498:[2-6]....$" large:64498:.*:.* ];\n'
            "}"
        )
        result = struct_to_set(config)
        assert 'set policy-options community FOO members "64498:[2-6]....$"\n' in result
        assert "set policy-options community FOO members large:64498:.*:.*\n" in result

    def test_groups_transform_to_set(self) -> None:
        config = (
            'groups foo {\n    snmp {\n        location "foo";\n    }\n}\n'
            "groups bar {\n    snmp {\n        location bar;\n    }\n}\n"
            "groups baz {\n    snmp {\n        inactive: location baz;\n    }\n}\n"
        )
        result = struct_to_set(config)
        assert 'set groups foo snmp location "foo"\n' in result
        assert "set groups bar snmp location bar\n" in result
        assert "set groups baz snmp location baz\n" in result
        assert "deactivate groups baz snmp location baz\n" in result

    def test_apply_groups_to_set(self) -> None:
        config = (
            "apply-groups foo;\n"
            "apply-groups [ foo bar ];\n"
            "snmp {\n    apply-groups foo;\n    apply-groups [ foo bar ];\n}\n"
        )
        result = struct_to_set(config)
        assert "set apply-groups foo\n" in result
        assert "set snmp apply-groups foo\n" in result
        assert "set snmp apply-groups bar\n" in result

    def test_inactive_apply_groups_to_set(self) -> None:
        config = (
            "inactive: apply-groups foo;\n"
            "inactive: apply-groups [ foo bar ];\n"
            "snmp {\n"
            "    inactive: apply-groups foo;\n"
            "    inactive: apply-groups [ foo bar ];\n"
            "}\n"
        )
        result = struct_to_set(config)
        assert "set apply-groups foo\n" in result
        assert "deactivate apply-groups foo\n" in result
        assert "set snmp apply-groups foo\n" in result
        assert "deactivate snmp apply-groups foo\n" in result
        assert "set snmp apply-groups bar\n" in result
        assert "deactivate snmp apply-groups bar\n" in result

    def test_protect_prefix_emits_command(self) -> None:
        config = (
            "interfaces {\n"
            "    ge-0/0/0 {\n"
            "        protect: unit 0 {\n"
            "            family inet {\n"
            "                dhcp;\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "}"
        )
        result = struct_to_set(config)
        assert "set interfaces ge-0/0/0 unit 0 family inet dhcp\n" in result
        assert "protect interfaces ge-0/0/0 unit 0\n" in result

    def test_protect_leaf_emits_command(self) -> None:
        config = "system {\n    protect: host-name router1;\n}"
        result = struct_to_set(config)
        assert "set system host-name router1\n" in result
        assert "protect system host-name router1\n" in result

    def test_combined_replace_protect_inactive(self) -> None:
        config = (
            "interfaces {\n"
            "    replace: protect: inactive: ge-0/0/0 {\n"
            "        description uplink;\n"
            "    }\n"
            "}"
        )
        result = struct_to_set(config)
        assert "set interfaces ge-0/0/0 description uplink\n" in result
        assert "protect interfaces ge-0/0/0\n" in result
        assert "deactivate interfaces ge-0/0/0\n" in result
        assert "replace:" not in result

    def test_comment_lines_ignored(self) -> None:
        config = (
            "interfaces {  /* a comment */\n"
            '/* a comment */  lo0 {\n    description "/*";  /* a comment */\n  }\n'
            '  ge-0/0/0 {  # a comment\n    description "#";  # a comment\n  }\n}'
        )
        result = struct_to_set(config)
        assert 'set interfaces lo0 description "/*"\n' in result
        assert 'set interfaces ge-0/0/0 description "#"\n' in result


class TestTheExampleConfigurationConvertsToSet:
    """The example, curly to set, means what the device's own display set means.

    `examples/junoscfg-oracle.conf` and `.set` are what a vMX printed for one
    configuration (`tests/data/device/README.md`); the device law holds
    junoscfg's set rendering of all four, the JSON and XML among them, to the
    device's set. This converter writes set from curly on its own, for the
    structured validator, so it is held to the same oracle: its output reads
    to the IR the device's set reads to, both less the lines
    `known-differences.json` records for the curly rendering.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="PRODUCT DEFECT: no known-differences class (the device law reads curly "
        "through SetConverter.statements, not to_set): to_set() writes the tag of a "
        "one-line statement on the whole line, `inactive: route 10.98.0.0/16 reject;` as "
        "`deactivate ... route 10.98.0.0/16 reject` and `protect: autonomous-system 64496;` "
        "as `protect ... autonomous-system 64496`",
    )
    def test_the_set_output_means_what_the_devices_set_means(self, structured_config: str) -> None:
        capture = example()
        skip = recorded_lines(capture, "conf")

        def ir(lines: list[str]) -> dict:
            text = "".join(f"{line}\n" for line in lines if line not in skip)
            return json.loads(convert_config(text, from_format=Format.SET, to_format=Format.JSON))

        ours = ir(struct_to_set(structured_config).splitlines())
        assert ours["configuration"], "the example converted to nothing"
        assert ours == ir(capture.device_set())


class TestATagOnAOneLineStatementCoversTheStatement:
    """`inactive:` or `protect:` before a one-line statement tags the statement.

    The device's display set of `examples/junoscfg-oracle.conf` writes the tag
    on the statement's path, never on its value or child: `deactivate
    routing-options static route 10.98.0.0/16`, `protect routing-options
    autonomous-system`. Tagging the whole line deactivates `reject`, not the
    route.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="PRODUCT DEFECT: no known-differences class: SetConverter.to_set() writes "
        "the tag on the whole line (see TestTheExampleConfigurationConvertsToSet)",
    )
    @pytest.mark.parametrize(
        ("curly", "tag_line"),
        [
            (
                "routing-options {\n    static {\n        inactive: route 10.98.0.0/16 reject;\n"
                "    }\n}\n",
                "deactivate routing-options static route 10.98.0.0/16",
            ),
            (
                "routing-options {\n    protect: autonomous-system 64496;\n}\n",
                "protect routing-options autonomous-system",
            ),
        ],
        ids=["an-inactive-entry-with-a-flag", "a-protected-statement-with-a-value"],
    )
    def test_the_tag_names_the_statement(self, curly: str, tag_line: str) -> None:
        tags = [
            line
            for line in struct_to_set(curly).splitlines()
            if line.startswith(("deactivate ", "protect "))
        ]
        assert tags == [tag_line]
