"""Tests for structured-to-set converter (SetConverter)."""

from __future__ import annotations

from junoscfg.display.set_converter import SetConverter


def struct_to_set(config: str) -> str:
    return SetConverter(config).to_set()


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


class TestSetConverterExampleValidation:
    def test_structured_produces_set_lines(self, structured_config: str, set_lines: str) -> None:
        """Validate structured→set converter against the synthetic example.

        Characterization: examples/router1.set is generated from
        examples/router1.conf by this implementation, so the two agree line for
        line. The count and the per-line match are recorded as they are today.
        """
        result = struct_to_set(structured_config)
        result_lines = result.strip().splitlines()
        expected_lines = set_lines.strip().splitlines()

        assert len(result_lines) == 61, f"Expected 61 lines, got {len(result_lines)}"

        # Every line matches: the fixtures are generated from one another.
        for i in range(min(160, len(result_lines), len(expected_lines))):
            assert result_lines[i] == expected_lines[i], (
                f"Line {i + 1} differs:\n  got:  {result_lines[i]}\n  want: {expected_lines[i]}"
            )
