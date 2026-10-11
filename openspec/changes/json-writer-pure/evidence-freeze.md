<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): IDs ARCH-C11 (open) and ARCH-C15 (INTENTIONAL: `_native_groups` keeps its output shape and stops touching caller data); no writer may mutate caller-owned IR; every writer is checked.
- C3: type `bug`, standard lane (the version bump and changelog exceed the fix lane's two-file cap). C4: the writer law lives at the owning door, `tests/unit/convert/test_convert_roundtrip.py`, because contract tests may reach only `junoscfg` and `junoscfg.cli`, and those never hand a writer a caller-owned IR. C5: patch 0.16.1, the `consumer` entry is version-only and not a break. C6: the JSON writer copies once on entry.

## Requirements

- `specs/conversion/writers/spec.md` (new capability): "A writer leaves the IR it is given unchanged"; "JSON output writes groups as the device does" (ARCH-C15 recorded at the owning layer with its captures).
- Contradicted requirement: none. `conversion/path-filtering` ("Filter the shared IR before rendering") and `conversion/entry-keys` ("Writers follow the declared order") hold unchanged: the output is the same.

## Evidence

- Observed on `d1e804e` (`private_test_data/makeover-work/c11_mutation.py`, synthetic values): `from_dict(ir, "json")` mutates the caller's IR in all four probes (`ssh: true` and `ssh: {}` to `[null]`; `class: ["super-user"]` to `"super-user"`; a group entry inside `groups: {group: [...]}` normalized in place); YAML, set and structured leave it unchanged. `to_dict(..., "set")` gives `ssh: {}`, so the read-then-render flow is affected, not only hand-built IR.
- Owning code: `src/junoscfg/convert/output/json_output.py` `dict_to_json` (in-place `_normalize_presence_flags`, `_coerce_scalar_leaves`; `_native_groups` copies only the top-level mapping, so the passes reach the caller's group list). `from_dict` is called inside `src/` only by `pipeline_result`, as its last step, on an IR it read itself: the named surfaces are unaffected.
- ARCH-C15 device evidence: native JSON `"groups": [ {"name": ...} ]` in `tests/data/device/jvd/vmx-23.2R2-S7.5/mdr1_acx7509.json.gz`, `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz`, `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.json.gz`; the catalogue row `groups` (`tests/support/shapes.py`) pins it.

## Non-goals

As `proposal.md`: no output changes; the reader-side `groups` IR split (NEW-A3, change 13); rewriting the three passes as one.

## Acceptance criteria

- Both test ids of the delta's first requirement exist, fail on the merge base `d1e804e` for the JSON writer and pass after the change. The set, structured and YAML parameters of the hand-built test pass on both sides by design: they are the family law's guard rows that keep the other writers pure.
- The second requirement's test (`test_format_matrix.py::TestEveryReaderGivesTheShapeIr`) passes before and after: JSON output is unchanged.
- No other test changes; the whole suite and the device law stay green with `known-differences.json` untouched.
- `balanced` policy: independent Test/Challenge (behavioural change, STOP-T) and a fresh Reviewer (yellow zone, STOP-R).

## Performance expectations

The JSON writer gains one deep copy of the IR per call. JSON output time on the largest device JSON capture may grow by at most the copy's cost; measured before and after in phase 5 and recorded in `metrics.md`.

## Outstanding decisions

None, because C3–C6 are resolved by repository rules and the task's own conditions.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: normal (one domain, yellow zones, no declared break, no trust boundary)
- Roles required: Builder; independent Test/Challenge (behavioural, `balanced`); fresh Reviewer (yellow zone); Finalizer duties run by the Builder under the owner's brief
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `e7cd402`. Approved under the owner's unattended-run instruction of 2026-10-11.
