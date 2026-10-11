---
status: accepted
scope: ["tests/corpus/test_jvd_corpus.py", "tests/support/jvd_data.py", "tests/conftest.py", ".github/workflows/corpus.yml", "docs/how-to/run-a-batch-of-changes.md"]
enforced-by: none
review-by: 2027-04-11
---

# Retire the JVD tier from per-change verification

## Context

Changes touching the set reader, the grammar or the field validator ran the
JVD tier before review: `--jvd` over Juniper's 1,535-file corpus, cloned at
test time. On the nightly makeover of 2026-10-11 it cost 45 to 90 minutes per
run, the longest step of every such change. The committed device evidence
covers the same ground faster. `tests/data/device/` holds the devices' own
renderings, with three JVD configurations among them. Its device-evidence tests
take under twenty seconds. On 2026-10-11 the owner asked for the JVD check to give
way to checks over `tests/data/device/` or `examples/junoscfg-oracle.*`.

## Decision

The JVD tier is retired: the JVD corpus clone and `--jvd` are no longer used
for any change's verification or any claim about output. Their place is taken
by the device-evidence checks and the before/after comparison over `tests/data/device/`
in [run a batch of changes](../how-to/run-a-batch-of-changes.md), which every
change touching the schema, grammar, readers, writers or anonymizer runs.
Hand-written text, which device captures never exercise, is covered by
synthetic adversarial rows in the owning test catalogue.

Removing the tier's code is its own change, `retire-jvd-tier`, typed `bug`
as the owner asked. It removes the `--jvd` option and its `jvd` marker,
`tests/corpus/test_jvd_corpus.py`, `tests/support/jvd_data.py` with its
`BROKEN_FILES` exception, and the nightly corpus workflow's JVD run. It also
modifies the `validation/set-command-validation` requirement that names
`--jvd`. Until it merges, the code stays, no change runs it, and only the
nightly CI job does.

## Consequences

Per-change corpus evidence drops from 45–90 minutes to about a minute: the
device-evidence check files in about 18 seconds, plus the comparison, which runs in
3 seconds, or about 40 seconds with every anonymize rule. A defect that shows only on
a JVD file outside the three committed ones is no longer found by any run.
That loss is accepted for the time it saves. Device captures are the evidence
that outranks the schema; synthetic rows guard the lexing that the JVD corpus
exercised through hand-written text.

Some checks are not yet committed tests over the device evidence: check 1, the
parts of checks 3 and 5 not yet covered, and the comparison as a shared tool.
Until test-only changes add them, the how-to writes down what stands in for
each. This record supersedes, for the jvd clone only, "the jvd clone stays the
opt-in breadth tier" in
[2026-10-10](2026-10-10-commit-device-captures-as-the-oracle.md).
