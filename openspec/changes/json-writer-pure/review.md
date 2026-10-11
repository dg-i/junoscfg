## Findings

### Independent Test/Challenge (phase 4, STOP-T)

A fresh, context-isolated agent ran on `a05f314` (merge base `d1e804e`); its
report is copied to `test-challenge.md`. The orchestrator relayed the rulings of
2026-10-11: accept all four findings; the challenger accepted C4 and C5.
Disposition, all in the phase-5 commit:

1. F1 (high), the `wrap=False` door was not covered: a fix copying only when
   wrapped passed. `test_a_hand_built_ir_is_left_unchanged` now runs every
   spelling through six writer doors: set, structured, JSON, JSON with
   `wrap=False`, YAML, YAML with `wrap=False` (`pipeline_result` renders
   relative output bare).
2. F2 (high), the output half was not asserted: a fix that skipped a pass
   passed. Each door now also asserts its output equals the output for a fresh
   copy, and `test_the_json_writer_writes_the_device_spelling` pins the JSON
   `configuration` of every hand-built spelling a device rendering decides
   (`[null]` flags, scalar leaves, the native `groups` list of ARCH-C15). The
   one spelling left unpinned is `ssh: [True]`: no reader gives it and no
   device rendering decides its output, so pinning today's `[[null]]` would set
   an expected output nobody has evidence for; purity and output-equals-copy
   are asserted for it.
3. F3 (medium), mutation paths no spelling reached: the five spellings added
   (a flag inside a list, a one-element leaf in a wrapped group, the JSON/XML
   readers' `groups` list, a flag four lists deep, a tagged flag), plus the
   negative row `a-leaf-list-with-one-value` (`apply-groups ["G1"]` stays a
   list). The read-IR law is unchanged.
4. F4 (low), counts: corrected in `evidence-freeze.md` and `tasks.md`. Final
   counts: the class collects 384 cases (60 hand-built doors, 9 pinned
   outputs, 315 read sources); on the merge base 22 fail (the 18 JSON and
   JSON-bare hand-built doors whose spelling the writer rewrites, and the four
   `{}` read sources) and 362 pass by design (guard rows, pinned outputs the
   base already writes, and the leaf-list negative row).

## Already provided

`copy.deepcopy` from the standard library is the copy; no helper is added.

## Specification challenges

None.

## Verdict

Pending: the fresh Reviewer (yellow zone, `balanced`) at STOP-R.
