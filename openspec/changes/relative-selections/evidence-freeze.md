## Resolved instructions

instruction-integrity.md governs: the PO-1 ruling (fix (a) to (d) with regression tests
observed failing first; (e) only without new syntax and without a cli break) under the owner
rule; one rule for every writer (C2); dotted keys resolved against the keys present (C3).

## Requirements

- specs/conversion/path-filtering: MODIFIED "Filter the shared IR before rendering" (the
  renderer receives the path-wrapped IR and the path; a `null` value is selected; dotted
  keys); RENAMED and MODIFIED "A relative selection spells presence flags and entry key order
  as absolute output does" to "A relative selection is written as absolute output writes
  it, without its path" (every writer; its exclusions, annotation selections, the `groups`
  wrapper, coercion and dotted keys, are now covered).
- Contradicted text: "the renderer receives the contents below `system`"; "This requirement
  does not cover ... (four exclusions)".

## Evidence

- Base `d3ed627` (the relative path code is unchanged since `adb6fb7`). Probe
  (private_test_data/makeover-work/relative-selections/probe.py): `system.login` relative
  json and yaml-new keep `class: [super-user]` (absolute: scalar); `system.login.user` and
  `system.syslog.host` relative set print `set "[{'name': ...}]"`, structured writes nothing;
  a YAML `ssh:` (null) writes nothing relative in every writer (absolute writes it); `system.@` relative json
  and yaml-new write `inactive: [null]` (absolute `true`); relative structured of
  `system.host-name` writes nothing (set `set r1`).
- Device corpus (probe_all.py, probe-base.json): of 2,875 selections (every mapping-key path
  to depth 5 over the device JSON captures, x 5 writers) compared with the absolute output
  at the path: json and yaml-new differ only for 2 annotation selections; set differs for
  64 mapping, 234 list, 28 scalar and 17 annotation selections; structured for 110, 139, 1
  and 17. Example: `--path interfaces --relative -e set` writes `set interface et-0/0/2 ...`.
- Dotted keys (schema tree): `802.3ad`, `ieee-802.1`, `ieee-802.1ad`, `ieee-802.1p`,
  `ieee-802.3`, `ieee802.1-priority-map`, `inet.0`, `inet.3`, `inet6.0`, `inet6.3`,
  `to-802.1p-from-dscp`, `version-1.1`. Prefix and address names are list entries, which no
  path addresses, before or after.
- Prototype of the rule (scratchpad, discarded): json, yaml-new and yaml equal the absolute
  value at the path for all 2,875 selections.

## Non-goals

`from_dict(wrap=False)`; display's text filters; absolute output;
device claims.

## Acceptance criteria

Regression tests for (a) to (e) observed failing at base, then passing; existing path tests
pass (updated where they pinned the defects: structured relative leaf, the pipeline's
renderer input); a device-corpus law: every relative selection, put back under its path,
reads as the absolute output; device comparison (tools/compare_device_outputs.py, absolute
output) 0 differences; independent Test/Challenge and a fresh Reviewer in review.md.

## Performance expectations

A relative selection renders the path-wrapped IR once, as absolute output does; no reparse.

## Outstanding decisions

None blocking.

## Execution and checkpoint

- Roles: Builder, independent Test/Challenge, fresh Reviewer, Finalizer.
- Resume point: phase 4 tests.

## Delta log

- Freeze established at the commit adding this file, on base `d3ed627`.
- Test/Challenge delta (report on `1370b2c`; review.md TC1 to TC11, SC1 to SC5). The ruling
  is unchanged. Criteria added: coercion of list and leaf selections; groups from set input
  (json, yaml-new, set, structured); hidden list names as unit rows; a mid-path dotted key;
  the exact key winning, and a dotted key beside a shorter one; paths through a list or a
  leaf; the kept-statements key; annotation selections in set and structured (a note for
  the dropped tag); writer purity under `below=`; `from_dict(wrap=False)` output; anonymized
  coercion, annotation and set list; a stronger corpus law (set lines less the path's
  words; structured put back and read; depth 4). Records: the claim of put-back narrowed,
  the yaml writer's value stated, the dotted rule stated as the shortest join that resolves,
  the two deliberate output changes named. Invalidated: the acceptance-test list; rerun:
  the red run (64 failed at base for the intended reasons).

## Scope and completion

Outcome: `--path --relative` writes, in every format, what absolute output writes at the
path without the path; a `null` value and a dotted key are selectable.
