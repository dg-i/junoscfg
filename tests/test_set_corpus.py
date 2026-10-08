"""The shipped grammar against set commands this repository already had.

`examples/router1.set` is a fixture written alongside the grammar work, so it
cannot say much about the grammar. These commands come from the test suite,
which predates it. Two independent reviewers of the grammar changes could not
reproduce the accept-rate figures in their records, because the corpus lived
only in a scratch directory; it is committed now, with its derivation in the
header of `data/set_corpus.txt`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from junoscfg.validate.set_validator import SetValidator  # noqa: TC001

CORPUS = Path(__file__).parent / "data" / "set_corpus.txt"

# Commands the grammar rejects. Keeping the full list, rather than a count,
# means a new false positive and a fixed one are both visible in the diff.
#
# Correctly rejected — malformed fixtures the corpus inherited from the tests
# they were harvested from:
CORRECTLY_REJECTED = {
    "set interfaces ge-0/0/0 bogus-thing 5": "element does not exist",
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
}

# Over-rejected — valid Junos the structural grammar cannot express. Each code
# is a limitation listed in docs/guide/validation.md; shrinking this set is
# progress. The codes:
#
#   merged    a rule merged from several tree positions offers one choice
#   brackets  a `[ a b ]` value list; VALUE is /\S+/, so `[` is its own token
OVER_REJECTED = {
    "set groups foo snmp location": "merged",
    "set policy-options community FOO members": "brackets",
    "set system location dc-a": "merged",
    "set system name-server": "merged",
}


def _corpus() -> list[str]:
    return [
        line
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


@pytest.fixture(scope="module")
def validator(bundled_set_validator: SetValidator) -> SetValidator:
    """The session's one grammar compile; it costs about four seconds."""
    return bundled_set_validator


class TestShippedGrammarAgainstTheCorpus:
    def test_corpus_is_not_empty(self) -> None:
        assert len(_corpus()) > 100

    def test_rejections_are_exactly_the_recorded_ones(self, validator: SetValidator) -> None:
        rejected = {c for c in _corpus() if not validator.validate(c).valid}
        expected = set(CORRECTLY_REJECTED) | set(OVER_REJECTED)
        assert rejected == expected, (
            f"newly rejected: {sorted(rejected - expected)}\n"
            f"no longer rejected: {sorted(expected - rejected)}"
        )

    def test_the_recorded_rejections_are_still_in_the_corpus(self) -> None:
        """A command dropped from the corpus must not linger in the lists above."""
        corpus = set(_corpus())
        stale = (set(CORRECTLY_REJECTED) | set(OVER_REJECTED)) - corpus
        assert not stale, f"recorded but absent from the corpus: {sorted(stale)}"
