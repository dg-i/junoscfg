"""How a writer spells a value: by its leaf's type, quoted where it must be, `"` escaped.

`format_value` is the one answer every set and curly writer asks (spec
conversion/value-quoting). The device's own renderings settle each spelling:
vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 `junoscfg-oracle.{set,conf,json,xml}.gz`
write `import ( P-A )` bare, `description "uplink to sw1 \\"core\\""` with the
quote escaped and `message "...only.\\nAll..."` with its backslash as is; vMX
`synthetic-probes.{xml,json}.gz` keep a quoted policy name's quotes in the
value (`<import>"( P-A )"</import>`). DEV-4, DEV-5, DEV-6, DEV-7, NEW-C6,
ANON-P4 (change value-quoting-by-type).
"""

from __future__ import annotations

import itertools
import json

import pytest

from junoscfg import Format, convert_config
from junoscfg.display import format_value

#: A leaf the schema types `policy-algebra`, as the structure tree carries it
#: (`protocols bgp group neighbor import`).
_ALGEBRA = {"l": True, "ll": True, "tr": "policy-algebra"}
#: A free-text leaf (`interfaces interface description`).
_TEXT = {"l": True, "tr": "xsd:string"}


class TestAValueIsSpelledByItsLeaf:
    """The leaf's type decides how a value is written, never the value's look."""

    @pytest.mark.parametrize(
        "token",
        ["( P-A )", "( P-A && P-B )", "(( A && ! B ) || ( ! C && D ))", '"( P-A )"', '"P 1"'],
        ids=["one-term", "two-terms", "nested", "quoted-name", "quoted-spaced-name"],
    )
    def test_a_policy_algebra_token_is_written_as_it_is(self, token: str) -> None:
        """An expression or a quoted name is the device's own token (DEV-4, DEV-6)."""
        assert format_value(token, _ALGEBRA) == token

    @pytest.mark.parametrize(
        ("name", "written"),
        [("PS-1", "PS-1"), ("P 1", '"P 1"'), ("P;1", '"P;1"')],
        ids=["plain", "spaced", "semicolon"],
    )
    def test_a_plain_name_is_quoted_only_where_it_must_be(self, name: str, written: str) -> None:
        """A name on a policy-algebra leaf is quoted as any value is (pin: as on the base)."""
        assert format_value(name, _ALGEBRA) == written

    @pytest.mark.parametrize("node", [_TEXT, None], ids=["description", "no-node"])
    @pytest.mark.parametrize("text", ["( P-A && P-B )", "( P-A || P-B )", "( ! P-A )"])
    def test_an_expression_on_another_leaf_is_quoted(self, text: str, node: object) -> None:
        """Text that looks like an expression is text where the leaf takes text."""
        assert format_value(text, node) == f'"{text}"'

    @pytest.mark.parametrize(
        ("value", "written"),
        [
            ('uplink to sw1 "core"', '"uplink to sw1 \\"core\\""'),
            ('a"b', '"a\\"b"'),
            ('"', '"\\""'),
            ('say "hi"; then {go} #1', '"say \\"hi\\"; then {go} #1"'),
        ],
        ids=["device-description", "inside-a-word", "alone", "beside-delimiters"],
    )
    def test_a_quote_inside_a_value_is_escaped(self, value: str, written: str) -> None:
        """`"` inside a quoted value is `\\"`, as the device writes it (DEV-7)."""
        assert format_value(value, _TEXT) == written

    def test_a_backslash_is_written_as_it_is(self) -> None:
        """The device writes the login message's `\\n` as is (pin: as on the base; P11)."""
        message = "Authorized use only.\\nAll access is logged."
        assert format_value(message) == f'"{message}"'

    def test_a_junos_variable_stays_quoted(self) -> None:
        """DEV-V7: junoscfg quotes `$junos-…`; the device loads it as the same (pin)."""
        assert format_value("$junos-interface-name") == '"$junos-interface-name"'

    @staticmethod
    def _values() -> list[str]:
        """Every value of one to three characters over the characters quoting turns on.

        Space, quote, the curly delimiters, comment and template starts,
        brackets, the expression characters and a letter; `\\` is left out
        while its spelling is open (probe P11).
        """
        alphabet = 'a "{};#$[(&|!'
        return [
            "".join(chars)
            for size in (1, 2, 3)
            for chars in itertools.product(alphabet, repeat=size)
        ]

    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED])
    def test_every_short_value_reads_back(self, writer: Format) -> None:
        """Written by either writer, every value reads back as itself (DEV-7 round trip)."""
        values = self._values()
        source = json.dumps(
            {
                "configuration": {
                    "interfaces": {
                        "interface": [
                            {"name": f"ge-0/0/{n}", "description": value}
                            for n, value in enumerate(values)
                        ]
                    }
                }
            }
        )
        written = convert_config(source, from_format=Format.JSON, to_format=writer, validate=False)
        read = json.loads(
            convert_config(written, from_format=writer, to_format=Format.JSON, validate=False)
        )
        entries = read["configuration"]["interfaces"]["interface"]
        got = [entry.get("description") for entry in entries]
        assert len(values) == 13 + 13**2 + 13**3
        assert len(got) == len(values)
        mismatched = [(want, have) for want, have in zip(values, got, strict=True) if want != have]
        assert not mismatched, mismatched[:10]
