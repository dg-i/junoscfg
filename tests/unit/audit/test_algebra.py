"""The policy-expression tokenizer: which names a policy-algebra value holds.

Reached through collect_occurrences, which tokenizes the value of every
policy-algebra leaf: the names are its ``algebra`` occurrences, in order.
"""

from __future__ import annotations

from typing import Any

import pytest

from junoscfg.audit import collect_occurrences

# Names with spaces, found in the adversarial review of the audit; the
# end-to-end case is TestAPolicyNameWithSpacesIsReferenced in test_types.py.
QUOTED_NAME_CASES = [
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


def algebra_names(expr: str, schema_root: dict[str, Any]) -> list[str]:
    """The names collected from *expr* as the import policy of a BGP group."""
    ir = {"protocols": {"bgp": {"group": [{"name": "g", "import": [expr]}]}}}
    return [o.value for o in collect_occurrences(ir, schema_root) if o.kind == "algebra"]


class TestExtractNames:
    """Plain names, boolean expressions and bracket lists give their names."""

    @pytest.mark.parametrize(("expr", "expected"), EXTRACT_NAMES_CASES)
    def test_extract(self, schema_root: dict[str, Any], expr: str, expected: list[str]) -> None:
        assert algebra_names(expr, schema_root) == expected

    @pytest.mark.parametrize(("expr", "expected"), QUOTED_NAME_CASES)
    def test_quoted_and_spaced_names(
        self, schema_root: dict[str, Any], expr: str, expected: list[str]
    ) -> None:
        assert algebra_names(expr, schema_root) == expected
