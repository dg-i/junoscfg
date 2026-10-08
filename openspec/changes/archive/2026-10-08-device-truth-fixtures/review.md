# Review

Fresh agent session, read-only, against commit `d999a9f` before it was
amended and tagged `v0.9.1`. The reviewer ran the tier as is, with the
captures moved aside, and against the previous 24.4R0 artifacts, and probed
the helpers for vacuous passes.

## Confirmed exact

Two pairs pass on the shipped artifacts and the tier skips cleanly without
them. On the 24.4R0 artifacts the `firewall family inet6` pair fails on the
`hop-limit` path, 1 missing and 3 extra: the defect the tier was built to
see. A wrong header path fails loudly, not vacuously. `_reroot` takes blank
lines and a trailing newline; the reader ignores the header if left in. The
committed location is picked up by no other glob. Full suite green.

## Findings

1. **A failure printed configuration values.** An extra path is by
   construction a line the converter could not split, so the value sat in
   the key; the design claimed otherwise. **Applied**: a list entry's name and
   anything after a space are elided, so a failure names element paths only.
2. **List entries pooled their children**: two terms equalled one, and a
   `then` under the wrong term passed. Shape, which is the stated purpose.
   **Applied**: an entry is told by its `name` or `address`; both probes now
   differ.
3. **No committed pair**, so the helpers ran only where private data is.
   **Applied**: one synthetic pair under `tests/data/captures/`, shaped after
   a device's rendering in the documentation ranges; self-consistent, not an
   oracle, and said so.
4. **The guide's sentence called the new tier opt-in.** **Applied**.
5. **The README never showed the header line.** **Applied**.
6. **An `rpc-reply` wrapper raised a bare `KeyError`.** **Applied**:
   `find_configuration` unwraps it, with a message when nothing is there.
7. **A fragment that did not parse read as "N missing".** **Applied**: an
   empty rendering is named as such.
8. **Minor**: discovery sorted private before committed; a quoted name with a
   space split into crumbs. **Applied**: directory order, `shlex`. Same-stem
   pairs in both directories get pytest's suffix; accepted.

## Already provided

`find_configuration` in `convert.ir` for the wrapper, used.

## Specification challenges

None.

## Verdict

A genuine schema-independent oracle that catches the defect it was built for;
ship with 1, 2 and 3 applied, which the amended commit does.

## Owner acceptance

Accepted by the owner on 2026-10-08, in one pass over the eight live reviews,
on the summary that each review's findings were resolved or recorded as
accepted-as-is. The owner did not sign off per finding.

Decision: the real capture pairs may be public. All three (the two bordergw
subtrees and the uplink-failure-detection capture that arrived in step 4)
are cleared to move to `tests/data/captures/`. The agent's tooling refused
to move real-device files out of `private_test_data/` itself, so the owner
performs the `git mv`; the test already reads both locations, so nothing
changes until then and the move is a rename when it happens.
