"""Tests for structured-to-set converter (SetConverter)."""

from __future__ import annotations

import json

import pytest

from junoscfg import Format, convert_config
from junoscfg.display import SetConverter
from tests.support.devices import example, recorded_lines


def struct_to_set(config: str) -> str:
    """`to_set()`, deprecated since the change structured-one-line-blocks."""
    with pytest.deprecated_call():
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
        reason="PRODUCT DEFECT of a deprecated door, removed in the next minor release "
        "(follow-up of change structured-one-line-blocks): no known-differences class (the "
        "device law reads curly through SetConverter.statements, not to_set): to_set() "
        "writes the tag of a "
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
        reason="PRODUCT DEFECT of a deprecated door, removed in the next minor release "
        "(follow-up of change structured-one-line-blocks): no known-differences class: "
        "SetConverter.to_set() writes the tag on the whole line (see "
        "TestTheExampleConfigurationConvertsToSet)",
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


# ── The token lexer (makeover run 2026-10-11, change structured-one-line-blocks) ──

_LAID_OUT_ROUTE = (
    "routing-options {\n    static {\n        inactive: route 10.98.0.0/16 reject;\n    }\n}\n"
)


class TestTheLexerReadsTokensNotLines:
    """Spec: conversion/structured-input, "Structured text is read by tokens, not lines".

    OPEN-1 (= NEW-A1): the line reader dropped a block written on one line,
    read `a; b;` on one line as one statement and dropped the block after a
    `}` on the same line, without a word. Layout is free (`ARCHITECTURE.md`
    §1), so one-line text reads as the same statements, tags included.
    """

    @pytest.mark.parametrize(
        ("one_line", "laid_out"),
        [
            (
                "class-of-service { forwarding-classes { class fc0 queue-num 0; } }",
                "class-of-service {\n    forwarding-classes {\n"
                "        class fc0 queue-num 0;\n    }\n}\n",
            ),
            (
                "system { host-name router1; domain-name example.net; }",
                "system {\n    host-name router1;\n    domain-name example.net;\n}\n",
            ),
            (
                "system {\n    host-name router1;\n} "
                "interfaces { ge-0/0/0 { description uplink; } }",
                "system {\n    host-name router1;\n}\n"
                "interfaces {\n    ge-0/0/0 {\n        description uplink;\n    }\n}\n",
            ),
            (
                "routing-options { static { inactive: route 10.98.0.0/16 reject; } }",
                _LAID_OUT_ROUTE,
            ),
            ("snmp { apply-groups [ G1 G2 ]; }", "snmp {\n    apply-groups [ G1 G2 ];\n}\n"),
            (
                'interfaces { ge-0/0/0 { description "a; b { c } # d"; } }',
                'interfaces {\n    ge-0/0/0 {\n        description "a; b { c } # d";\n    }\n}\n',
            ),
        ],
        ids=[
            "a-nested-block",
            "two-statements",
            "a-block-after-a-closing-brace",
            "a-tagged-entry",
            "a-bracket-list",
            "delimiters-inside-quotes",
        ],
    )
    def test_one_line_text_reads_as_its_lines(self, one_line: str, laid_out: str) -> None:
        statements = SetConverter(one_line).statements()
        assert statements, "the one-line text read as nothing"
        assert statements == SetConverter(laid_out).statements()

    @pytest.mark.parametrize(
        ("text", "statements"),
        [
            (
                "routing-options { static { inactive: route 10.98.0.0/16 reject; } }",
                [
                    [
                        ("routing-options", frozenset()),
                        ("static", frozenset()),
                        ("route 10.98.0.0/16 reject", frozenset({"inactive"})),
                    ]
                ],
            ),
            (
                'interfaces { protect: ge-0/0/0 { description "a; b { c } # d /* e */"; } }',
                [
                    [
                        ("interfaces", frozenset()),
                        ("ge-0/0/0", frozenset({"protect"})),
                        ('description "a; b { c } # d /* e */"', frozenset()),
                    ]
                ],
            ),
            (
                "interfaces {\n    ${PHY_PORT}:0 { mtu 9216; }\n}\n",
                [
                    [
                        ("interfaces", frozenset()),
                        ("${PHY_PORT}:0", frozenset()),
                        ("mtu 9216", frozenset()),
                    ]
                ],
            ),
            (
                'snmp { inactive: apply-groups [ G1 "G 2" ]; }',
                [
                    [("snmp", frozenset()), ("apply-groups G1", frozenset({"inactive"}))],
                    [("snmp", frozenset()), ('apply-groups "G 2"', frozenset({"inactive"}))],
                ],
            ),
        ],
        ids=[
            "a-tagged-entry",
            "a-quoted-value-holding-delimiters",
            "a-template-variable",
            "a-tagged-bracket-list",
        ],
    )
    def test_tags_and_quoted_values_read_exactly(
        self, text: str, statements: list[list[tuple[str, frozenset[str]]]]
    ) -> None:
        """F7 (Test/Challenge): comparing two layouts lets a lexer that drops
        tags and ignores quotes pass; these name the statements."""
        assert SetConverter(text).statements() == statements


class TestACommentIsNeverPartOfAStatement:
    """Spec: conversion/structured-input, "A comment is never part of a statement".

    NEW-B6: the line reader matched `(.*);` on the raw line, so a trailing
    comment holding `;` joined the value (`host-name "r1; ## note"`).
    """

    @pytest.mark.parametrize(
        "text",
        [
            "system {\n    host-name router1; ## note; see ticket\n}\n",
            "system {\n    host-name router1; /* a; b */\n}\n",
            "system {\n    host-name /* a; { b } */ router1;\n}\n",
            "system {\n    /* a note;\n       over two lines } */\n    host-name router1;\n}\n",
            "system { # a; b {\n    host-name router1;\n}\n",
            'system {\n    host-name router1; ## say "hi\n}\n',
            "system {\n    ## Warning: missing mandatory statement(s): 'secret'\n"
            "    host-name router1;\n}\n",
            'system {\n    /* a "quoted; } comment */ host-name router1;\n}\n',
        ],
        ids=[
            "hash",
            "block",
            "between-tokens",
            "over-two-lines",
            "after-an-opening-brace",
            "an-open-quote-in-a-comment",
            "the-devices-warning-comment",
            "a-quote-in-a-block-comment",
        ],
    )
    def test_a_comment_holding_a_delimiter(self, text: str) -> None:
        assert SetConverter(text).statements() == [
            [("system", frozenset()), ("host-name router1", frozenset())]
        ]


class TestMalformedTextIsRefused:
    """Spec: conversion/structured-input, "Malformed structured text is refused".

    The line reader passed an unmatched `}` and an unclosed block silently and
    read an open quote as a value; a device rejects each of them on load.
    """

    @pytest.mark.parametrize(
        ("text", "fault"),
        [
            ("system {\n    host-name router1;\n}\n}\n", r"line 4: '\}' closes no block"),
            ("system {\n    host-name router1;\n", r"line 1: block 'system' is never closed"),
            (
                "system {\n    host-name router1\n}\n",
                r"line 2: statement 'host-name router1' has no ';'",
            ),
            ('system {\n    host-name "router1;\n}\n', r"line 2: a quoted value is never closed"),
            ("system {\n    host-name router1; /* note\n}\n", r"line 2: a comment is never closed"),
            ("snmp {\n    apply-groups [ G1 G2;\n}\n", r"line 2: '\[' is never closed"),
            ("{\n    host-name router1;\n}\n", r"line 1: '\{' opens a block with no name"),
            (
                "AN3:\nsystem {\n    host-name router1;\n}\n",
                r"line 1: statement 'AN3:' has no ';'\nAN3:$",
            ),
        ],
        ids=[
            "a-brace-too-many",
            "an-unclosed-block",
            "a-statement-without-a-semicolon",
            "an-open-quote",
            "an-open-comment",
            "an-open-bracket-list",
            "a-block-without-a-name",
            "a-label-above-a-block",
        ],
    )
    def test_it_raises(self, text: str, fault: str) -> None:
        """The message names the fault, its line, and the line's text.

        A statement ends on its own line, as every device writes it, so prose
        or a CLI prompt above a dump (Juniper's published JVD files carry
        both) is refused, not read into the next statement's path.
        """
        with pytest.raises(ValueError, match=fault):
            SetConverter(text).statements()


class TestWhatYieldsNoStatementIsReported:
    """Spec: conversion/structured-input, "What yields no statement is reported, not
    silently dropped".

    DEV-18: the device's curly prints a statement under `apply-flags omit` as
    `{ /* OMITTED */ }` (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5,
    `tests/data/device/synthetic/*/junoscfg-oracle.conf.gz`, group `GR-OMIT`);
    the line reader wrote the placeholder as a statement. What the device makes
    of an empty block is evidence-blocked (probe P6, Test/Challenge F2): the
    test asserts the report, not what is read for it.
    """

    @pytest.mark.parametrize(
        ("text", "note"),
        [
            (
                "groups {\n    GR-OMIT {\n        system { /* OMITTED */ };\n    }\n}\n",
                "groups GR-OMIT system: `apply-flags omit` hides this block's content",
            ),
            ("system {\n    inactive: services { }\n}\n", "system services: an empty block"),
        ],
        ids=["the-devices-placeholder", "an-empty-block"],
    )
    def test_the_lexer_names_the_block(self, text: str, note: str) -> None:
        converter = SetConverter(text)
        if "OMITTED" in text:
            assert converter.statements() == []
        notes = converter.notes()
        assert len(notes) == 1
        assert notes[0].startswith(note)


class TestAnEmptyStatementReadsAsNothing:
    """Test/Challenge F10: a `;` with no statement before it carries nothing.

    The device prints one after its `{ /* OMITTED */ }` placeholder (`};`);
    the line reader wrote `set system }` for `};` after a block and
    `host-name "router1;"` for `;;`.
    """

    @pytest.mark.parametrize(
        "text",
        [
            "system {\n    host-name router1;;\n}\n",
            "system {\n    host-name router1;\n};\n",
            ";\nsystem {\n    ;\n    host-name router1;\n}\n",
        ],
        ids=["a-doubled-semicolon", "after-a-closing-brace", "a-lone-semicolon"],
    )
    def test_a_stray_semicolon(self, text: str) -> None:
        assert SetConverter(text).statements() == [
            [("system", frozenset()), ("host-name router1", frozenset())]
        ]
        assert SetConverter(text).notes() == ()


class TestToSetIsDeprecated:
    """Spec: conversion/structured-input, "The schema-free set writer of the lexer is deprecated".

    OPEN-10: `to_set()` places a one-line statement's tag on its last node
    (the strict xfails above); conversion reads the statement through the
    schema. Its one caller, the structured validator, is deprecated with it.
    """

    def test_it_warns_and_keeps_its_output(self) -> None:
        with pytest.deprecated_call(match="convert_config"):
            output = SetConverter("system {\n    host-name router1;\n}\n").to_set()
        assert output == "set system host-name router1\n"
