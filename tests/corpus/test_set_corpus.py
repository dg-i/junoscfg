"""The shipped grammar against what devices print, and against what they would refuse.

Every `set` line a device printed is valid Junos. All of them through the
Earley grammar take minutes, so `tests/data/device/grammar-corpus.json` holds
the few that exercise every grammar rule the many do
(`tools/device_grammar_corpus.py`), and every line the grammar rejects, each
a false rejection of valid configuration. Every line, by hand:
`pytest tests/corpus/test_set_corpus.py --device-grammar`.

The corpus this replaces, `tests/data/set_corpus.txt`, was harvested from the
repository's own tests and from `examples/router1.set`, junoscfg's own output;
the example is now the device's (`examples/junoscfg-oracle.set`).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.support.devices import DEVICE_DATA, captures
from tests.support.paths import PRIVATE_DATA

GRAMMAR_CORPUS = json.loads((DEVICE_DATA / "grammar-corpus.json").read_text(encoding="utf-8"))

# Commands the grammar must reject or cannot take, written by hand: a device
# prints only valid configuration, so the device corpus has no negative cases.
#
# Correctly rejected: malformed Junos.
CORRECTLY_REJECTED = {
    "set interfaces ge-0/0/0 bogus-thing 5": "element does not exist",
    "set policy-options community FOO members": "leaf-list with no value",
    "set system host-name": "leaf with no value",
    "set system host-name foo bar baz": "leaf with three values",
    # `apply-groups` after a leaf's value is not Junos. The validator used to
    # cut the statement off the line before parsing, which hid these four
    # behind the leaf they trailed; since 0.8.0 the grammar models the
    # statement and sees them for what they are.
    "set system host-name r1 apply-groups [foo bar]": "apply-groups after a leaf value",
    "set system host-name r1 apply-groups foo": "apply-groups after a leaf value",
    "set system host-name r1 apply-groups-except foo": "apply-groups after a leaf value",
    "set system host-name router1 apply-groups mygroup": "apply-groups after a leaf value",
    # The device rejects a bare value under `system location` and takes
    # `location building <name>` (device probe, vMX 23.2R2-S7.5). Listed as
    # an over-rejection until that probe; the grammar rejects it again since
    # any `maxOccurs` but 1 is a list (phase-6 review, challenge A).
    "set system location dc-a": "location takes keyworded children, not a value",
}

# Intentionally unsupported — device-valid syntax that raw junoscfg set input
# deliberately excludes. This is neither malformed Junos nor an accidental
# validator over-rejection.
INTENTIONALLY_UNSUPPORTED = {
    "set system apply-groups [ foo bar ]": "interactive bracket-list shorthand",
}

# Over-rejected — valid Junos the structural grammar cannot express. Each code
# is a limitation listed in docs/guide/validation.md; shrinking this set is
# progress. The code:
#
#   merged    a rule merged from several tree positions offers one choice
OVER_REJECTED = {
    "set groups foo snmp location": "merged",
    "set system name-server": "merged",
}


@pytest.fixture(scope="module")
def validator(bundled_set_validator: Any) -> Any:
    """The session's one grammar compile."""
    return bundled_set_validator


class TestTheGrammarTakesWhatDevicesPrint:
    def test_the_corpus_covers_the_grammar_the_devices_use(self) -> None:
        assert len(GRAMMAR_CORPUS["accepted"]) > 100
        assert GRAMMAR_CORPUS["rules"] > 300

    def test_every_covering_line_is_accepted(self, validator: Any) -> None:
        refused = [
            line for line in GRAMMAR_CORPUS["accepted"] if not validator.validate(line).valid
        ]
        assert not refused, "\n".join(refused)

    def test_the_false_rejections_are_exactly_the_recorded_ones(self, validator: Any) -> None:
        """A device printed each of these; a fix accepts one and fails here until
        `tools/device_grammar_corpus.py` drops it from the record."""
        accepted = [line for line in GRAMMAR_CORPUS["rejected"] if validator.validate(line).valid]
        assert not accepted, "now accepted, regenerate the corpus:\n" + "\n".join(accepted)


class TestTheGrammarRefusesWhatIsNotJunos:
    @pytest.mark.parametrize("line", sorted(CORRECTLY_REJECTED))
    def test_malformed_junos_is_rejected(self, validator: Any, line: str) -> None:
        assert not validator.validate(line).valid, CORRECTLY_REJECTED[line]

    @pytest.mark.parametrize("line", sorted(INTENTIONALLY_UNSUPPORTED))
    def test_bracket_shorthand_is_refused_with_its_reason(self, validator: Any, line: str) -> None:
        assert validator.validate(line).errors[0].message == (
            f"Unsupported bracket syntax in set input on line 1:\n{line}"
        )

    @pytest.mark.parametrize("line", sorted(OVER_REJECTED))
    def test_a_known_limitation_is_still_rejected(self, validator: Any, line: str) -> None:
        """Valid Junos the structural grammar cannot express (docs/guide/validation.md);
        a fix moves the line out of OVER_REJECTED."""
        assert not validator.validate(line).valid, OVER_REJECTED[line]


#: Every verb a device's display set prints, each validated as its statement path.
_VERBS = ("set ", "deactivate ", "protect ", "activate ", "delete ")


def _every_device_line() -> list[str]:
    """Every line of the private captures where they exist, and of the committed ones."""
    lines = {
        line
        for folder in PRIVATE_DATA.glob("jvd_derived_data*")
        for path in folder.glob("*.set")
        if ".device." not in path.name
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(_VERBS)
    } | {line for c in captures() for line in c.device_set()}
    return sorted(lines)


@pytest.mark.device_grammar
class TestEveryDeviceLine:
    """By hand: every device line, minutes through the Earley grammar."""

    def test_only_the_recorded_lines_are_rejected(self, validator: Any) -> None:
        rejected = {line for line in _every_device_line() if not validator.validate(line).valid}
        recorded = set(GRAMMAR_CORPUS["rejected"])
        assert rejected == recorded, (
            f"newly rejected: {sorted(rejected - recorded)}\n"
            f"no longer rejected: {sorted(recorded - rejected)}"
        )
