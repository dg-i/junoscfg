"""Tests for the policy-expression tokenizer (extract_names)."""

from __future__ import annotations

import pytest

from junoscfg.audit.algebra import extract_names

REGRESSION_CASES = [
    # A single quoted policy name keeps its spaces (the set parser strips
    # the surrounding quotes, so the value has no structure to tokenize).
    ("my pol", ["my pol"]),
    ("customer export v4", ["customer export v4"]),
    # Quoted names inside an expression stay atomic.
    ('( "my pol" && ! POL-B )', ["my pol", "POL-B"]),
    ('( "a b" || "c d" )', ["a b", "c d"]),
]

# (expression, expected names in order of appearance)
EXTRACT_NAMES_CASES: list[tuple[str, list[str]]] = [
    # Plain and quoted names
    ("export-v4", ["export-v4"]),
    ('"my-pol"', ["my-pol"]),
    # Boolean expressions with spaces
    ("( pol-a && ! pol-b )", ["pol-a", "pol-b"]),
    ("( pol-a || pol-b )", ["pol-a", "pol-b"]),
    # Operators without surrounding whitespace
    ("pol-a&&pol-b", ["pol-a", "pol-b"]),
    ("pol-a||!pol-b", ["pol-a", "pol-b"]),
    ("(pol-a&&!pol-b)", ["pol-a", "pol-b"]),
    # Nested parentheses
    ("(( pol-a && pol-b ) || pol-c)", ["pol-a", "pol-b", "pol-c"]),
    ("( ( pol-a || ! pol-b ) && ( pol-c ) )", ["pol-a", "pol-b", "pol-c"]),
    # Bracket lists
    ("[ imp-a imp-b ]", ["imp-a", "imp-b"]),
    ("[imp-a imp-b]", ["imp-a", "imp-b"]),
    # Nothing to extract
    ("", []),
    ("( && || ! )", []),
    ("()[]!&&||", []),
    ("   ", []),
    # Punctuation inside names survives intact
    ("pol.v4", ["pol.v4"]),
    ("export_customer-1", ["export_customer-1"]),
    ("( r1.export-v4_new && ! r1.import-v4_old )", ["r1.export-v4_new", "r1.import-v4_old"]),
]


class TestExtractNames:
    """extract_names() tokenizes plain names, algebra, and bracket lists."""

    @pytest.mark.parametrize(("expr", "expected"), EXTRACT_NAMES_CASES)
    def test_extract(self, expr: str, expected: list[str]) -> None:
        assert extract_names(expr) == expected

    @pytest.mark.parametrize(("expr", "expected"), REGRESSION_CASES)
    def test_quoted_and_spaced_names(self, expr: str, expected: list[str]) -> None:
        assert extract_names(expr) == expected
