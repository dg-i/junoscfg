"""Structured (curly) input through its conversion doors.

`convert/input/structured_input.py` lexes curly text with
`junoscfg.display.SetConverter` and builds the IR with the set reader's schema
walk. Each test drives every door the behaviour reaches: `to_dict`,
`convert_config_result`, `pipeline_result`, the CLI's `convert` and `audit
unused`, and `validate_structured`. Synthetic values only, as AGENTS.md names
them. Provenance: the makeover run of 2026-10-11, change
structured-one-line-blocks (OPEN-1, DEV-18, NEW-B5).
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config_result, validate_structured
from junoscfg.cli import main
from junoscfg.convert import pipeline_result, to_dict

_ONE_LINE = (
    (
        "class-of-service { forwarding-classes { class fc0 queue-num 0; } }",
        "class-of-service {\n    forwarding-classes {\n        class fc0 queue-num 0;\n    }\n}\n",
    ),
    (
        "system { host-name router1; domain-name example.net; } "
        "interfaces { ge-0/0/0 { description uplink; } }",
        "system {\n    host-name router1;\n    domain-name example.net;\n}\n"
        "interfaces {\n    ge-0/0/0 {\n        description uplink;\n    }\n}\n",
    ),
)


class TestABlockOnOneLine:
    """Spec: conversion/structured-input, "Structured text is read by tokens, not lines".

    OPEN-1: a block on one line converted to nothing, and validated, without
    a word.
    """

    @pytest.mark.parametrize(
        ("one_line", "laid_out"), _ONE_LINE, ids=["a-nested-block", "two-blocks-and-two-leaves"]
    )
    def test_every_door_converts_it(self, one_line: str, laid_out: str) -> None:
        expected = to_dict(laid_out, "structured")
        assert expected, "the laid-out text read as nothing"
        assert to_dict(one_line, "structured") == expected

        wanted = convert_config_result(
            laid_out, from_format=Format.STRUCTURED, to_format=Format.SET
        )
        result = convert_config_result(
            one_line, from_format=Format.STRUCTURED, to_format=Format.SET
        )
        assert result.output == wanted.output
        assert result.diagnostics == wanted.diagnostics
        assert pipeline_result(one_line, from_format="structured", to_format="set") == result

        cli = CliRunner().invoke(main, ["-i", "structured", "-e", "set"], input=one_line)
        assert cli.exit_code == 0, cli.output
        assert cli.stdout == wanted.output


class TestMalformedTextIsRefused:
    """Spec: conversion/structured-input, "Malformed structured text is refused".

    A brace too many was read past: the configuration converted and validated
    as if it were whole.
    """

    TEXT = "system {\n    host-name router1;\n}\n}\n"
    FAULT = "line 4: '}' closes no block"

    def test_every_door_refuses_it(self) -> None:
        with pytest.raises(ValueError, match="closes no block"):
            to_dict(self.TEXT, "structured")
        with pytest.raises(ValueError, match="closes no block"):
            convert_config_result(self.TEXT, from_format=Format.STRUCTURED, to_format=Format.SET)
        with pytest.raises(ValueError, match="closes no block"):
            pipeline_result(self.TEXT, from_format="structured", to_format="json")

        cli = CliRunner().invoke(main, ["-i", "structured", "-e", "set"], input=self.TEXT)
        assert cli.exit_code == 2
        assert self.FAULT in cli.stderr

        result = validate_structured(self.TEXT)
        assert result.valid is False
        assert any(self.FAULT in error.message for error in result.errors)


_OMITTED = (
    "groups {\n    GR-OMIT {\n        system { /* OMITTED */ };\n    }\n"
    "    GR-A {\n        system {\n            host-name router1;\n        }\n    }\n}\n"
)
_EMPTY = "system {\n    host-name router1;\n    services { }\n}\n"


class TestWhatYieldsNoStatementIsReported:
    """Spec: conversion/structured-input, "What yields no statement is reported, never written".

    DEV-18: the device's `{ /* OMITTED */ }` placeholder for `apply-flags
    omit` (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5, group `GR-OMIT`) was written
    as `set groups GR-OMIT system { /* OMITTED */ }` and reported only as a
    statement the schema could not place.
    """

    @pytest.mark.parametrize(
        ("text", "warning", "kept"),
        [
            (
                _OMITTED,
                "groups GR-OMIT system: `apply-flags omit` hides this block's content",
                "set groups GR-A system host-name router1",
            ),
            (_EMPTY, "system services: an empty block", "set system host-name router1"),
        ],
        ids=["the-devices-placeholder", "an-empty-block"],
    )
    def test_every_door_warns_and_writes_nothing(self, text: str, warning: str, kept: str) -> None:
        heard: list[str] = []
        ir = to_dict(text, "structured", diagnostic_sink=heard.append)
        assert "OMITTED" not in repr(ir)
        assert "services" not in repr(ir)
        assert [message for message in heard if message.startswith(warning)] == heard
        assert len(heard) == 1

        result = convert_config_result(text, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert kept in result.output.splitlines()
        assert "OMITTED" not in result.output
        assert "services" not in result.output
        reported = [d for d in result.diagnostics if d.source == "structured-input"]
        assert len(reported) == 1
        assert reported[0].severity == "warning"
        assert reported[0].render().startswith(warning)
        assert not [
            d for d in result.diagnostics if "OMITTED" in d.render() and d is not reported[0]
        ]
        assert pipeline_result(text, from_format="structured", to_format="set") == result

        cli = CliRunner().invoke(main, ["-i", "structured", "-e", "set"], input=text)
        assert cli.exit_code == 0, cli.output
        assert warning in cli.stderr
        assert "OMITTED" not in cli.stdout

        audit = CliRunner().invoke(main, ["audit", "unused", "-i", "structured"], input=text)
        assert audit.exit_code == 0, audit.output
        assert warning in audit.stderr

        verdict = validate_structured(text)
        assert verdict.valid is True, verdict.errors
        assert [w.message for w in verdict.warnings if w.message.startswith(warning)]


class TestTheSetLinesOfAStatement:
    """Spec: validation/structured-validation, "Curly text is validated as the conversion
    walk reads it".

    NEW-B5: the device's curly prints `hold-time up 2000 down 0;` on one line
    and its display set prints two lines (vMX 23.2R2-S7.5); validation read
    the curly statement as one set line, which the grammar rejects. The walk
    that builds the IR says where each sibling statement starts; the lines
    keep the input's own tokens.
    """

    @pytest.mark.parametrize(
        ("curly", "lines"),
        [
            (
                "interfaces {\n    ge-0/0/0 {\n        hold-time up 2000 down 0;\n    }\n}\n",
                (
                    "set interfaces ge-0/0/0 hold-time up 2000",
                    "set interfaces ge-0/0/0 hold-time down 0",
                ),
            ),
            (
                "interfaces { ge-0/0/0 { description a b c; } }",
                ("set interfaces ge-0/0/0 description a b c",),
            ),
            (
                'system {\n    inactive: host-name "router 1";\n}\n',
                ('set system host-name "router 1"',),
            ),
            (
                "protocols {\n    isis {\n        overload timeout 300;\n    }\n}\n",
                ("set protocols isis overload timeout 300",),
            ),
        ],
        ids=[
            "siblings-on-one-line",
            "an-unquoted-multi-word-value",
            "a-tag-and-a-quoted-value",
            "a-keyword-leaf",
        ],
    )
    def test_the_walk_splits_at_each_sibling(self, curly: str, lines: tuple[str, ...]) -> None:
        from junoscfg.convert import structured_set_lines

        assert structured_set_lines(curly) == lines
