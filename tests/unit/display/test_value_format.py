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
from typing import TYPE_CHECKING, Any
from xml.sax.saxutils import escape

import pytest
import yaml

from junoscfg import Format, convert_config, validate_config
from junoscfg.display import format_value

if TYPE_CHECKING:
    from collections.abc import Callable

#: A leaf the schema types `policy-algebra`, as the structure tree carries it
#: (`protocols bgp group neighbor import`).
_ALGEBRA = {"l": True, "ll": True, "tr": "policy-algebra"}
#: A free-text leaf (`interfaces interface description`).
_TEXT = {"l": True, "tr": "xsd:string"}


class TestAValueIsSpelledByItsLeaf:
    """The leaf's type decides how a value is written, never the value's look."""

    @pytest.mark.parametrize(
        "token",
        [
            "( P-A )",
            "( P-A && P-B )",
            "(( A && ! B ) || ( ! C && D ))",
            '( "P 1" && ! P-B )',
            '"( P-A )"',
            '"( P-A && P-B )"',
        ],
        ids=[
            "one-term",
            "two-terms",
            "nested",
            "a-quoted-name-inside",
            "quoted-name",
            "quoted-two-term-name",
        ],
    )
    def test_a_policy_algebra_token_is_written_as_it_is(self, token: str) -> None:
        """An expression, or a quoted name a reader keeps quoted, is the device's token.

        DEV-4, DEV-6. A quoted name inside an expression is the expression's
        and is never escaped (Test/Challenge F5).
        """
        assert format_value(token, _ALGEBRA) == token

    @pytest.mark.parametrize(
        ("name", "written"),
        [("PS-1", "PS-1"), ("P 1", '"P 1"'), ("P;1", '"P;1"')],
        ids=["plain", "spaced", "semicolon"],
    )
    def test_a_plain_name_is_quoted_only_where_it_must_be(self, name: str, written: str) -> None:
        """A name on a policy-algebra leaf is quoted as any value is.

        Base behaviour kept: on the base this fails only on the new `node`
        argument (a signature-only failure, Test/Challenge F6).
        """
        assert format_value(name, _ALGEBRA) == written

    @pytest.mark.parametrize(
        ("value", "written"),
        [
            ('"P 1"', '"\\"P 1\\""'),
            ('"P-1"', '"\\"P-1\\""'),
            ('"', '"\\""'),
            ('"a" "b"', '"\\"a\\" \\"b\\""'),
            ('"P-1', '"\\"P-1"'),
        ],
        ids=["quoted-spaced-name", "quoted-plain-name", "a-lone-quote", "two-quoted", "open"],
    )
    def test_any_other_policy_algebra_value_is_escaped(self, value: str, written: str) -> None:
        """Quotes the reader would strip are the value's, so they are escaped.

        A quoted name that cannot read as an expression reads without its
        quotes (spec conversion/value-quoting), so `"P 1"` held in the IR
        (from XML or JSON) is written `"\\"P 1\\""`, which reads back as
        written (specification challenge SC3, interim; probe P12 asks what the
        device holds). Test/Challenge F4, F5.
        """
        assert format_value(value, _ALGEBRA) == written

    @pytest.mark.parametrize("node", [_TEXT, None], ids=["description", "no-node"])
    @pytest.mark.parametrize("text", ["( P-A && P-B )", "( P-A || P-B )", "( ! P-A )"])
    def test_an_expression_on_another_leaf_is_quoted(self, text: str, node: object) -> None:
        """Text that looks like an expression is text where the leaf takes text."""
        assert format_value(text, node) == f'"{text}"'

    @pytest.mark.parametrize("node", [_TEXT, _ALGEBRA, None], ids=["text", "algebra", "no-node"])
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
    def test_a_quote_inside_a_value_is_escaped(
        self, value: str, written: str, node: object
    ) -> None:
        """`"` inside a quoted value is `\\"`, as the device writes it (DEV-7).

        Whether or not the caller passes a node: entry names, apply-macro
        values, `apply-groups` and the audit's rendering pass none
        (Test/Challenge F2).
        """
        assert format_value(value, node) == written

    def test_a_backslash_is_written_as_it_is(self) -> None:
        """The device writes the login message's `\\n` as is (pin: as on the base; P11)."""
        message = "Authorized use only.\\nAll access is logged."
        assert format_value(message) == f'"{message}"'

    @pytest.mark.parametrize("node", [None, _TEXT], ids=["no-node", "text"])
    def test_a_junos_variable_stays_quoted(self, node: object) -> None:
        """DEV-V7: junoscfg quotes `$junos-…`; the device loads it as the same.

        Pin (as on the base) whether or not a node is given (Test/Challenge F7).
        """
        assert format_value("$junos-interface-name", node) == '"$junos-interface-name"'


#: Every character quoting turns on: space, quote, the curly delimiters,
#: comment and template starts, a bracket, the expression characters and a
#: letter. `\` is left out while its spelling is open (probe P11).
_ALPHABET = 'a "{};#$[(&|!'


def _values(alphabet: str, sizes: tuple[int, ...]) -> list[str]:
    """Every value of the given sizes over *alphabet*, in a fixed order."""
    return ["".join(chars) for size in sizes for chars in itertools.product(alphabet, repeat=size)]


def _round_trip(
    values: list[str],
    writer: Format,
    config: Callable[[list[str]], dict[str, Any]],
    read: Callable[[dict[str, Any]], list[object]],
) -> list[tuple[str, object]]:
    """The values *writer*'s output does not read back as: (written, read)."""
    source = json.dumps({"configuration": config(values)})
    written = convert_config(source, from_format=Format.JSON, to_format=writer, validate=False)
    got = read(
        json.loads(
            convert_config(written, from_format=writer, to_format=Format.JSON, validate=False)
        )["configuration"]
    )
    assert len(got) == len(values)
    return [(want, have) for want, have in zip(values, got, strict=True) if want != have]


def _descriptions(values: list[str]) -> dict[str, Any]:
    interfaces = [{"name": f"ge-0/0/{n}", "description": v} for n, v in enumerate(values)]
    return {"interfaces": {"interface": interfaces}}


def _read_descriptions(config: dict[str, Any]) -> list[object]:
    return [entry.get("description") for entry in config["interfaces"]["interface"]]


def _policies(values: list[str]) -> dict[str, Any]:
    statements = [{"name": v, "then": {"accept": [None]}} for v in values]
    return {"policy-options": {"policy-statement": statements}}


def _read_policies(config: dict[str, Any]) -> list[object]:
    return [entry["name"] for entry in config["policy-options"]["policy-statement"]]


def _macros(values: list[str]) -> dict[str, Any]:
    macros = [{"name": f"M{n}", "data": [{"name": "k", "value": v}]} for n, v in enumerate(values)]
    return {"system": {"apply-macro": macros}}


def _read_macros(config: dict[str, Any]) -> list[object]:
    return [entry["data"][0].get("value") for entry in config["system"]["apply-macro"]]


def _imports(values: list[str]) -> dict[str, Any]:
    groups = [{"name": f"G{n}", "import": [v]} for n, v in enumerate(values)]
    return {"protocols": {"bgp": {"group": groups}}}


def _read_imports(config: dict[str, Any]) -> list[object]:
    return [entry["import"][0] for entry in config["protocols"]["bgp"]["group"]]


_PLACES = {
    "description": (_descriptions, _read_descriptions),
    "entry-name": (_policies, _read_policies),
    "apply-macro-value": (_macros, _read_macros),
}


class TestEveryValueReadsBackAsWritten:
    """Whatever a writer writes reads back as the value it wrote (DEV-7 round trip).

    Every value of up to three characters over `_ALPHABET`, the empty value
    included (Test/Challenge F9), at a free-text leaf, an entry's name and an
    apply-macro value, which pass no node to the formatter (F2).
    """

    @pytest.mark.parametrize("place", list(_PLACES))
    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED], ids=["set", "structured"])
    def test_every_short_value_reads_back(self, writer: Format, place: str) -> None:
        sizes = (1, 2, 3) if place == "entry-name" else (0, 1, 2, 3)
        values = _values(_ALPHABET, sizes)
        assert len(values) == sum(13**size for size in sizes)
        build, read = _PLACES[place]
        mismatched = _round_trip(values, writer, build, read)
        assert not mismatched, mismatched[:10]

    @pytest.mark.xfail(
        strict=True,
        reason="EVIDENCE_BLOCKED: probe P11: how the device writes `\\\\`, a backslash "
        "before a quote and a trailing backslash is unknown; junoscfg writes `\\` as is, "
        "so some values holding one do not read back (specification challenge SC2)",
    )
    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED], ids=["set", "structured"])
    def test_a_value_holding_a_backslash_reads_back(self, writer: Format) -> None:
        values = [value for value in _values('a "\\', (1, 2, 3)) if "\\" in value]
        assert len(values) == 45
        mismatched = _round_trip(values, writer, _descriptions, _read_descriptions)
        assert not mismatched, mismatched[:10]

    @pytest.mark.parametrize(
        "value",
        [
            "( P-A )",
            "( P-A && P-B )",
            '( "P 1" && ! P-B )',
            '"( P-A )"',
            '"( P-A && P-B )"',
            '"P 1"',
            '"P-1"',
            "P-1",
            "P 1",
            '"',
            '"a" "b"',
            '"P-1',
        ],
    )
    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED], ids=["set", "structured"])
    def test_a_policy_algebra_value_reads_back(self, writer: Format, value: str) -> None:
        """An import value from JSON or XML reads back as written (SC3 interim, F4, F5)."""

        assert not _round_trip([value], writer, _imports, _read_imports)


_BAD_EXPRESSIONS = [
    "( A ) ; export P-B",
    "( A ; export P-B )",
    "( A ) { export P-B; }",
    "( A } )",
    "( A ) # comment",
    "( A /* comment */ )",
    "( A )\nexport P-B",
    "( A [ P-B ] )",
    "( A",
    "( A ) ( B )",
    '( "P-A )',
]


def _policy_source(value: str, source: Format) -> str:
    ir = {"configuration": _imports([value])}
    if source == Format.JSON:
        return json.dumps(ir)
    if source == Format.YAML:
        return yaml.safe_dump(ir)
    return (
        "<configuration><protocols><bgp><group><name>G0</name><import>"
        + escape(value)
        + "</import></group></bgp></protocols></configuration>"
    )


class TestAPolicyValueOccupiesOneExpression:
    """Review F1: caller data must never introduce statements in either writer.

    These synthetic negatives make no device-validity claim. The existing
    preservation and structural-error contracts require refusal when quoting
    would instead create the quoted-name IR. SC4 does not change the spec.
    """

    @pytest.mark.parametrize("value", _BAD_EXPRESSIONS)
    @pytest.mark.parametrize("source", [Format.JSON, Format.YAML, Format.XML])
    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED])
    def test_an_expression_crossing_the_value_boundary_is_refused(
        self, value: str, source: Format, writer: Format
    ) -> None:
        text = _policy_source(value, source)
        if source in (Format.JSON, Format.YAML):
            assert validate_config(text, format=source).valid
        with pytest.raises(ValueError, match="one complete policy-algebra expression"):
            convert_config(text, from_format=source, to_format=writer, strict=True)

    @pytest.mark.parametrize(
        "value",
        [
            '( "P;1" && P-B )',
            '( "P{1}#/*[2]" && P-B )',
            '( "P(1)" && ( P-B || P-C ) )',
            r'( "P \"1\"" && P-B )',
        ],
    )
    @pytest.mark.parametrize("source", [Format.JSON, Format.YAML, Format.XML])
    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED])
    def test_delimiters_in_quoted_names_stay_in_the_expression(
        self, value: str, source: Format, writer: Format
    ) -> None:
        assert format_value(value, _ALGEBRA) == value
        written = convert_config(
            _policy_source(value, source), from_format=source, to_format=writer, strict=True
        )
        back = json.loads(
            convert_config(written, from_format=writer, to_format=Format.JSON, strict=True)
        )
        assert back == {"configuration": _imports([value])}
