---
status: accepted
scope: ["tests/data/device/**", "tests/corpus/test_device_renderings.py", "tests/corpus/test_set_corpus.py"]
enforced-by: tests
review-by: 2027-04-10
---

# Commit device captures, JVD's included, as the test oracle

## Context

junoscfg's tests judged it against data it had helped make: `router1.set` was
its own output, the set corpus was harvested from its own tests, and the
expected values of most cases were written by hand. On 2026-10-10 five JVD
configurations and four synthetic ones were loaded on four devices (vMX,
EX4600, EX4100, QFX5120), and the devices' four renderings of each show 16
defect classes no committed test had found. Third-party corpora were cloned
at test time, never vendored, to stay clear of licence questions and a stale
copy (`--jvd`).

## Decision

The devices' renderings are committed under `tests/data/device/` with their
sources, JVD's five unmodified and its Apache-2.0 `LICENSE` and `NOTICE` with
a statement of the derived files beside them; the jvd clone stays the opt-in
breadth tier. The secrets in both sets are public and are not masked: the
synthetic ones are invented, the JVD ones Juniper's published lab values,
an exception to `AGENTS.md`'s synthetic password value. Device output
outranks junoscfg's own: `router1` and the harvested set corpus retire from
the tests, and `examples/` holds a device's renderings.

## Consequences

Every expected value in the device tier comes from a device, so a defect
shared by all of junoscfg's readers shows. A failing case is a classified
line in `known-differences.json`, which shrinks as defects are fixed. A
refresh is a recapture and two tools, never a hand edit; the licence files
are checked by a test.
