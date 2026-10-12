"""The schema parity assertion permits only evidenced sibling placement.

schema-parity-sibling-order: controls remain cheap ordinary tests, independent
of the schema marker on the module whose assertion they exercise.
"""

import pytest

from tests.corpus.test_schema_data import assert_schema_set_parity
from tests.support.devices import captures

PREFIX = "set routing-options transport-class "
CONTROLS = PREFIX + "auto-create\n" + PREFIX + "fallback none\n"
GOLD = PREFIX + "name gold color 4000\n" + PREFIX + "name gold tunnel-egress end-point 10.255.0.3\n"
BRONZE = PREFIX + "name bronze color 6000\n"
ENTRIES = GOLD + BRONZE
BASELINE = CONTROLS + ENTRIES


@pytest.mark.parametrize(
    "capture",
    [c for c in captures() if c.source == "synthetic" and c.name == "junoscfg-oracle"],
    ids=lambda c: c.device,
)
def test_captured_siblings_can_move_around_ordered_entries(capture) -> None:
    raw = "".join(
        line
        for line in capture.rendering("set").splitlines(keepends=True)
        if line.startswith(PREFIX)
    )
    assert raw == BASELINE
    assert_schema_set_parity(raw, ENTRIES + CONTROLS)
    assert_schema_set_parity(raw, GOLD + CONTROLS + BRONZE)
    assert_schema_set_parity(raw, raw)


@pytest.mark.parametrize(
    "changed",
    [
        CONTROLS + BRONZE + GOLD,
        CONTROLS + ENTRIES + BRONZE,
        CONTROLS + GOLD,
        BASELINE.replace(
            "set routing-options transport-class auto-create",
            "deactivate routing-options transport-class auto-create",
        ),
        BASELINE.replace("4000", "4001"),
        BASELINE.replace("10.255.0.3", "10.255.0.4"),
        BASELINE.replace("color 4000", "color  4000"),
        BASELINE.replace("name gold", 'name "gold"'),
        BASELINE.replace("name gold", 'name "go\\ld"'),
        PREFIX + "fallback none\n" + PREFIX + "auto-create\n" + ENTRIES,
        BASELINE.rstrip("\n"),
        BASELINE.replace("\n", "\r\n"),
    ],
    ids=[
        "entry-order",
        "duplicate",
        "missing-entry",
        "activation",
        "value",
        "reference",
        "spacing",
        "quoting",
        "escaping",
        "control-order",
        "final-newline",
        "line-endings",
    ],
)
def test_parity_rejects_changes_outside_the_sibling_allowance(changed: str) -> None:
    assert changed != BASELINE
    with pytest.raises(AssertionError):
        assert_schema_set_parity(BASELINE, changed)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (
            "set policy-options policy-statement P term first then accept\n"
            "set policy-options policy-statement P term last then reject\n",
            "set policy-options policy-statement P term last then reject\n"
            "set policy-options policy-statement P term first then accept\n",
        ),
        (
            "set protocols bgp group G import [ A B ]\n",
            "set protocols bgp group G import [ B A ]\n",
        ),
        ("set unknown a\nset unknown b\n", "set unknown b\nset unknown a\n"),
        (
            CONTROLS + "set system host-name router1\n" + ENTRIES,
            ENTRIES + "set system host-name router1\n" + CONTROLS,
        ),
        ("set system host-name router1\n" + BASELINE, BASELINE + "set system host-name router1\n"),
    ],
    ids=[
        "policy-order",
        "leaf-list-order",
        "unplaced-order",
        "noncontiguous-block",
        "outside-block",
    ],
)
def test_parity_preserves_all_other_raw_order(left: str, right: str) -> None:
    with pytest.raises(AssertionError):
        assert_schema_set_parity(left, right)
