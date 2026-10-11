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
   one spelling left unpinned is `ssh: [True]`. Corrected after review (F1
   below): the JSON and YAML readers do give it, and today's output is
   `"ssh": [[null]]` in JSON and `set system services ssh True` in set, on the
   merge base and the head alike. No device rendering decides what it should
   be, so pinning today's output would set an expected output nobody has
   evidence for; purity and output-equals-copy are asserted for it, and the
   reader/writer handling is carried forward as NEW-R2 (change 13).
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

### Fresh Reviewer (phase 6, STOP-R)

A fresh, isolated Reviewer ran on code head `5f9934f`, branch head `8145e1d`
(merge base `d1e804e`). Verdict: CHANGES REQUIRED, the code fix correct and
complete for every writer; only F1 blocks, and it touches the record and the
spec. The orchestrator relayed the rulings of 2026-10-11. Points checked
without a finding: C5 (patch; the lane gate needs a `declared-break` entry for
any edit of a surface path), every writer and caller of the IR
(`validate_ir`, `filter_dict_by_path`, `find_unused`, edityaml), the ARCH-C15
citations (a writer keeping the `group` wrapper fails 26 rows of
`test_the_source_reads_as_the_ir` and 2 of the pinned-output test), and every
rerun figure (384/384 on head; 22 fail, 362 pass on the base writer; 5.8 ms
with the copy, 1.5 ms for the copy).

1. F1 (medium, specification and record): the `ssh: [True]` rationale "no
   reader gives it" was false. Executed: JSON or YAML input `ssh: [true]`
   gives JSON `"ssh": [[null]]` and set `ssh True`, on base and head. Fixed:
   the Test/Challenge F2 disposition above is corrected; the spec's
   device-spelling clause no longer lists a flag inside a list, which is held
   only to purity and output-equals-copy; the challenge is below. Carry-forward
   NEW-R2 (change 13): the `[true]` flag in the JSON and YAML readers and the
   JSON and set writers, with a device question on `system services ssh`
   (does `load json` accept `"ssh": [true]`, and what does it render).
2. F2 (low, outside the writer scope): `anonymize()` rewrites the IR its
   caller passes and returns the same object, with no contract line saying so
   (`apply_revert` says "mutated in place"). `pipeline_result` owns the IR it
   passes, so no named surface is affected. Carry-forward NEW-R3 (change 5):
   state the in-place rewrite in `src/junoscfg/anonymize/CONTRACT.md`, or copy
   on entry.
3. F3 (low): the three Precedent bullets of `src/junoscfg/convert/CONTRACT.md`
   were reflowed onto one line each because the pre-commit `document caps`
   hook refused the file at 34 lines (cap 30) with the invariant's first,
   four-line draft; with the invariant compacted to two lines, the base
   wrapping still gives 32 lines (the Reviewer's count), over the cap, so the
   reflow stays. The content is unchanged (the Reviewer compared it with
   whitespace normalized).

## Already provided

`copy.deepcopy` from the standard library is the copy; no helper is added.

## Specification challenges

### A presence flag inside a list does not get the device's spelling

- Artifact: `specs/conversion/writers/spec.md`, requirement "A writer leaves the IR it is given unchanged", the sentence listing a flag "inside a list" among the spellings whose JSON output "stays the device's spelling".
- Counterexample: executed on base `d1e804e` and head `5f9934f`: `convert_config('{"configuration":{"system":{"services":{"ssh":[true]}}}}', from_format=Format.JSON, to_format=Format.JSON)` gives `"ssh": [[null]]`, not `[null]`; YAML `ssh: [true]` gives the same, and both give `set system services ssh True`. The requirement claimed a device spelling the output does not have.
- User impact: the main spec would promise the device's spelling for an input that renders differently; the output itself is unchanged by this change.
- Proposed correction: the device-spelling clause lists `true`, `{}`, tagged and four-lists-deep flags only; a flag inside a list is held to purity and output-equals-copy; NEW-R2 (change 13) takes the reader and writer handling with a device artefact for `system services ssh`.
- Decision: Pending owner decision. Interim action: the proposed correction is applied to the delta (a narrowing that claims less, reversible, no code or output change), and NEW-R2 is ledgered for change 13 (owner intake 2026-10-11: merge with recorded interim action)

## Verdict

CHANGES REQUIRED at `8145e1d` (fresh Reviewer); F1–F3 addressed in
`012943b`. The same Reviewer confirmed every fix and **APPROVES at
`879ef61`**: no finding remains unresolved; NEW-R2 and NEW-R3 are carried
forward to changes 13 and 5; the specification challenge awaits the owner's
decision, and its interim action is reversible. Its one nit (the F3 line
count) is corrected above. Merge.

## Appendix: the fresh Reviewer's report (phase 6, verbatim)

Merge base `d1e804e` (v0.16.0), code head `5f9934f`, branch head `8145e1d`.
Read in order: evidence freeze, delta, `src/junoscfg/convert/CONTRACT.md`,
`test-challenge.md`, the tests, the diff. Probes (synthetic values) live next to
this file: `review_probe_callers.py`, `review_wrong_groups.py`,
`review_rerun_counts.py`.

### Verdict

**CHANGES REQUIRED**. The code fix is correct and complete for every writer.
Only F1 blocks, and its fix touches only the record and the spec, not the code.
F2 and F3 do not block.

### Ranked findings

#### F1 (medium, specification and record): the unpinned `ssh: [True]` exception rests on a false premise

- **Violated line:** `openspec/changes/json-writer-pure/specs/conversion/writers/spec.md:18-22`.
  The requirement lists "a presence flag ... inside a list" among the spellings
  the JSON writer "normalizes for the device" and says "the JSON output stays the
  device's spelling (`[null]` flags ...)". Separately,
  `openspec/changes/json-writer-pure/review.md:20` justifies leaving it unpinned
  with "no reader gives it".
- **Counterexample (executed on head and on the base; the output is identical
  on both):**
  `convert_config('{"configuration":{"system":{"services":{"ssh":[true]}}}}', from_format=Format.JSON, to_format=Format.JSON)`
  gives `"ssh": [[null]]`. YAML input `ssh: [true]` gives the same result. Both
  JSON and YAML input render to set as `set system services ssh True`. The JSON
  and YAML readers both produce `ssh: [True]` (`to_dict`), and the result
  reaches the named `consumer` surface.
- **Impact:** At archive, a requirement goes into the main specs that is false
  for one of the spellings it lists. The test leaves that row unpinned
  (`tests/unit/convert/test_convert_roundtrip.py:73`), so the false sentence and
  the tests agree with each other (shared blind spot).
- **Fix:**
  1. Correct the F2 disposition in `review.md:19-23`: the JSON and YAML readers
     do give `[True]`, and the pre-existing output is `[[null]]` / `ssh True`.
  2. In the spec, move "inside a list" out of the "device's spelling" clause.
     For that spelling, the spec should claim only purity and output-equals-copy.
  3. Open a carry-forward ID for the handling of `[true]` in the readers and
     writers. Request one device artefact for the path `system services ssh`:
     does `load json` accept `"ssh": [true]`, and what does it render?
     Changing the output is out of scope here, as the proposal's non-goal says.

#### F2 (low, carry-forward, outside the writer scope): `anonymize()` rewrites the IR its caller passes

- `src/junoscfg/anonymize/__init__.py:61-119` walks the input and returns the
  same object as `result.ir`. The probe reports `MUTATES`. Its docstring says
  "the modified IR", and `src/junoscfg/anonymize/CONTRACT.md` "Not for" mentions
  only the salt. `apply_revert` (`src/junoscfg/anonymize/revert.py:51`) also
  mutates, but its docstring says so ("mutated in place").
- `pipeline_result` owns the IR it hands to both functions, so neither the
  named surfaces nor this change is affected. The mission rule ("unless the
  public contract explicitly promises mutation") still applies to the
  `junoscfg.anonymize` door.
- **Fix:** open a new ID. Either state the in-place rewrite in the anonymize
  CONTRACT "Not for" section, or copy on entry.

#### F3 (low, residue): the Precedent section of `src/junoscfg/convert/CONTRACT.md:27-29` was reflowed

- I compared the base and head with whitespace normalized. The only content
  difference is the added invariant, so the content is preserved verbatim.
- No check requires the reflow. The codemap `BULLET` regex reads only
  bullets that are bare dotted names, and markdownlint passes either way. The
  record gives no reason for it.
- **Fix:** restore the base wrapping of the three bullets, or record the reason.

### Points checked, no finding

- **C5 patch versus declared break: sound.** The `consumer` surface path is
  only `src/junoscfg/__init__.py` (`pyproject.toml:249`), and the head changes
  only `__version__` there. The lane check (`agent_ready_checks/lane.py:584`)
  requires a `declared-break` entry for any edit of a surface path, even a
  non-breaking one. Precedent: `archive/2026-10-10-test-architecture`, also
  version-only and also a patch. `convert_config` reads a fresh IR, so its
  behaviour does not change, and `break-bumps` does not apply.
- **Writers and callers:** the set, structured, JSON (wrapped and bare) and
  YAML (wrapped and bare) writers all leave the IR unchanged. So do
  `validate_ir`, `filter_dict_by_path`, `find_unused` and `edityaml.apply_rules`,
  which deep-copies. `ansibilize*` deep-copies on entry (`ansibilize.py:162`
  and `:241`). `pipeline_result` mutates only the IR it read itself.
- **ARCH-C15 citations: verified.** All three captures hold `groups` as a list
  of entries with `name` first, while `interfaces`, `routing-instances` and
  `vlans` keep their wrappers. The vMX (23.2R2-S7.5) and QFX5120 (25.2R2-S1.5)
  releases are named.
  - Counterexample: a writer that keeps the `group` wrapper fails 26 rows of
    the cited `test_the_source_reads_as_the_ir`, because `read_ir` renders
    through JSON. It also fails 2 rows of
    `test_the_json_writer_writes_the_device_spelling`. Both tests guard the
    requirement.
- **Figures rerun:**

  | Figure | Result |
  |---|---|
  | Test class on head | 384 of 384 pass |
  | Test class on the base writer (deepcopy as identity, the only code difference) | 22 fail, 362 pass, the exact IDs the freeze lists |
  | Performance on the largest capture | 5.8 ms; the copy alone 1.5 ms |
  | `c11_mutation.py` | every JSON row reports `mutated=False` |
  | Full check | not rerun, as the brief instructs |

- **Version files and docs:** `pyproject.toml`, `__init__.py` and `uv.lock` all
  read 0.16.1. The changelog fragment and the `docs/guide/conversion.md` line
  are present. `known-differences.json` is untouched.

### Five prompts

1. **Trust boundary:** none crossed. The change only adds a copy, and it adds no
   new parsing.
2. **Incompatible-but-valid input:** `ssh: [true]` in JSON or YAML input, as
   described in F1.
3. **Shared blind spot:** F1. The spec sentence and the unpinned test row agree
   with each other. The independent evidence is the executed `convert_config`
   probe.
4. **Second answer:** none. `copy.deepcopy` comes from the standard library.
   No other presence normalizer was added: `dict_walker` only reads `[None]`.
5. **Stated figures and non-goals:** every figure I could rerun matches. The
   full check was not rerun, as the brief instructs.

### Specification challenge (for `openspec/changes/json-writer-pure/review.md`)

| Field | Value |
|---|---|
| Artifact | `specs/conversion/writers/spec.md:18-22`, requirement "A writer leaves the IR it is given unchanged" |
| Counterexample | JSON or YAML input `ssh: [true]` renders as JSON `"ssh": [[null]]`, not the device's `[null]` |
| User impact | The main spec would promise device spelling for an input that gets a different result |
| Proposed correction | Limit the device-spelling clause to `true`, `{}`, tagged and four-lists-deep flags. For a flag inside a list, claim only purity and output-equals-copy. Open a carry-forward ID with a device question on `system services ssh`. |
| Decision | Owner |

### Context expansion rows for `metrics.md`

| Field | Value |
|---|---|
| Context expansion: src/junoscfg/anonymize/__init__.py, src/junoscfg/anonymize/revert.py | caller check: does anonymize or revert mutate the caller's IR (F2) |
| Context expansion: src/junoscfg/edityaml/__init__.py, src/junoscfg/audit/__init__.py | caller check: edityaml and audit purity |
| Context expansion: .venv agent_ready_checks lane.py, codemap.py | C5 lane rule; whether the CONTRACT reflow is required (F3) |
| Context expansion: tests/data/device/{jvd,synthetic} captures | ARCH-C15 citations |

### Carry-forward

- F1 item 3: the `[true]` presence flag in the JSON and YAML readers, the JSON
  writer (`[[null]]`) and the set writer (`ssh True`). Needs a device artefact
  for `system services ssh`.
- F2: `anonymize()` mutates the IR without a contract line saying so.

### Confirmation of the review fixes (fix commit 012943b, branch head 879ef61)

Diff read: `git diff 8145e1d..879ef61`. Code head unchanged: no file under
`src/` changed since `5f9934f`.

| Finding | Fix | Confirmed by |
|---|---|---|
| F1 | `spec.md:18-26` now limits the device-spelling clause to `true`, `{}`, tagged and four-lists-deep flags. A flag inside a list (`[true]`, which the JSON and YAML readers give) is held only to purity and output-equals-copy, with NEW-R2 for change 13. `review.md` corrects the "no reader gives it" rationale. The test comment at `test_convert_roundtrip.py:73` names NEW-R2. The challenge is recorded in the required five-field format, with a reversible interim action. | Every spelling still in the device clause is pinned by `test_the_json_writer_writes_the_device_spelling`. The class passes 384/384 at 879ef61. `openspec validate json-writer-pure` is valid. |
| F2 | NEW-R3 is ledgered in `private_test_data/makeover-ledger.md:16` (change 5). | Ledger row present. |
| F3 | The reason for the reflow is recorded: the document cap. | `pyproject.toml:213` caps `src/**/CONTRACT.md` at 30 lines. The base file has 30 lines, base wrapping plus the invariant gives 32, and head has 29. `agent-ready caps` passes. |

The F1 narrowing claims less than before and weakens no assertion, because the
`[true]` row was never pinned. The metrics rows and the delta log entries are
present. The full check is not needed, because only the spec, the records and
one test comment changed.

Nit, not blocking: `review.md` F3 says the hook refused the file "at 34 lines".
My reconstruction gives 32. Both are over the cap, so the conclusion holds.

#### Verdict

**APPROVE** at 879ef61. No finding remains unresolved. NEW-R2 and NEW-R3 are
carried forward to changes 13 and 5. The specification challenge awaits the
owner's decision, and its interim action is reversible.
