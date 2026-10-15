## Resolved instructions

instruction-integrity.md governs: owner ruling on PO-1 (fix as its own change, regression
test observed failing first, user-visible effect stated, break decision recorded); standard
lane as type `bug` because the fix-lane file cap and the branch's activation entry cannot
both hold (C1); worktree and finalisation order from the owner (C2, C3); the path-filtering
spec gains the requirement the ruling sets (C4); schema-context coercion and the device
question C8 are reported, not acted on (C5, C6).

## Requirements

- specs/conversion/path-filtering/spec.md, ADDED "A relative selection is spelled as absolute
  output spells it".
- Contradicted text: path-filtering "preserve the existing relative and path-wrapped output
  semantics" (selection semantics kept; only the JSON spelling of a relative selection
  changes, by the owner's ruling). conversion/writers ("A writer leaves the IR it is given
  unchanged": the JSON output stays the device's spelling, `[null]` flags) and
  conversion/junos-json-yaml (yaml-new equals JSON output, relative selections included)
  stay as written and now hold for relative selections too.

## Evidence

- Base `ea18fab`. Probe (scratchpad po1.py, po1d.py, re-runnable with the public API):
  path `system.syslog.host` relative writes `[{"any": {}, ...}]` and keeps `name` second
  where absolute output writes `[{"name": ..., "any": [null]}]`; `system.services.netconf.ssh`
  relative writes `{}` where absolute writes `"ssh": [null]`; `system.services.ssh` (`true`)
  is already `[null]`; mapping selections are already normalized.
- Equivalence: `{}`, `true` and `[null]` under `system syslog host 198.51.100.9 any` all read
  to `set system syslog host 198.51.100.9 any` (po1c.py).
- Owning layer: `junos_json_object` in src/junoscfg/convert/output/json_output.py normalizes
  only a mapping and special-cases a selected `true`; `pipeline_result` passes the relative
  selection with `wrap=False` (src/junoscfg/convert/__init__.py).
- C5 probe (po1b.py): relative `system.login` keeps `"class": ["super-user"]` where absolute
  writes `"class": "super-user"`; context-dependent, out of scope.
- Device comparison base record: private_test_data/makeover-work/relative-null-flags/base.json
  (96 conversions, `tools/compare_device_outputs.py`, which does not select paths); a relative
  probe over the captures is run at base and head in phase 5.

## Non-goals

Schema-context scalar-leaf coercion of relative selections; any device claim; set,
structured and `yaml` output; absolute output.

## Acceptance criteria

`test_a_relative_selection_is_spelled_as_absolute_output_spells_it` observed failing at the
base and passing at head; existing TestPathFiltering and yaml-new tests pass; device
comparison 0 differences (no path selection); relative probe differences all explained.
Independent Test/Challenge on the test and a fresh Reviewer record verdicts in review.md.

## Performance expectations

None, because the relative object stage adds one walk of the selection it already copies.

## Outstanding decisions

None blocking. Reported: C5 (coercion), C6/C8 (device question).

## Execution and checkpoint

- Roles required: instruction-integrity.md Assurance (Builder, independent Test/Challenge,
  fresh Reviewer, Finalizer).
- Resume point: phase 4 tests (type `bug` has no design phase).

## Delta log

- Freeze established at the commit adding this file, on base `ea18fab`.

## Scope and completion

Outcome: relative JSON and yaml-new output of any selection spells presence flags and entry
key order as absolute output does at the path. Exclusions above. No binding carry-forward.
