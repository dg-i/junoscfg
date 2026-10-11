# Test/Challenge: universal-statements-from-tree (STOP-T)

Role: independent Test/Challenge (phase 4), working only from the committed artefacts
at `b18c652` (base `dd7c8c4`). Nothing tracked was edited. All probes are in this folder
and use synthetic values only:

| Probe | What it shows | Base output |
|---|---|---|
| `tc_probe_doors.py` | each capture's universal statements per reader, against the device's own JSON | `tc_probe_doors.base.out` |
| `tc_probe_legacy.py` | the legacy and consumer spellings of `apply-flags` | `tc_probe_legacy.base.out` |
| `tc_probe_via_structured.py` | capture to curly to set, against capture to set (the curly half of `dict_walker`) | `tc_probe_via_structured.base.out` |
| `tc_wrong_impls.py` | a pytest plugin that injects wrong `schema_child` and `universal_statements` implementations (`TC_IMPL=...`) | inline below |

## Summary of the checks the role brief asks for

- **Do the tests fail on the merge base for the right reason?** Yes. I sampled these failures: dropped keywords in `TestUnplacedContentKeepsItsKeywords`, the generator's union in `test_the_tree_is_authoritative`, the empty diagnostics in `test_an_unknown_flag_under_apply_flags_is_unplaced`, and the scalar `apply-groups` in the XML and YAML rows. The guards the freeze names pass on both sides, as the freeze says they do. Ran: 25 failed, 34 passed over the unit, tooling and corpus nodes, and 86 failed, 28 passed over the contract nodes of the two rows.
- **Is any oracle weakened?** No. The two corrected tests (C5, C9) replace an assertion with a stronger one.
- **Do the tests assert meaning, not layout?** Yes. The writer checks read the output back. The only layout claim is the spec's "curly output SHALL write `apply-flags omit;`", and no test pins it, which is correct.
- **Gaps.** They are ranked below.

## Findings, ranked

### 1. High: nothing tests the head differences against the device for each door

The device law (`tests/corpus/test_device_renderings.py`) compares **set output only**. It therefore passes on the base, where `apply-flags omit` is kept whole and written back verbatim. It cannot see a scalar-versus-list difference either. The two catalogue rows are synthetic.

**Executed** (`tc_probe_doors.py` on the base): 28 differences between a reader's IR and the device's JSON, in 3 of the 6 captures:
- 26 in the XML door. A nested `apply-groups` or `apply-groups-except` with one group reads as a scalar where the device JSON writes a list, for example `protocols apply-groups` and `interfaces … apply-groups-except` in both oracle captures, and 16 such statements in `jvd/…/mdr1_acx7509.xml`.
- 2 in the set door: `GR-OMIT` is unplaced, on both platforms.

The curly door shows 0 differences. The list change is therefore device-backed, but the evidence sits in tracked captures that no test reads for it.

**Proposed test:** `tests/corpus/test_device_truth.py::test_every_door_reads_the_devices_universal_statements`, parametrized over `captures()` × {conf, set, xml}.
- It compares each (path, value) map of `apply-*` with the map from the device's JSON. It skips `GR-OMIT` for conf (class `omitted-curly`).
- It asserts that the scan found more than 0 statements per capture.
- Expected result: 28 failures on the base, 0 at the head.

**Gap for the JSON door:** a nested JSON scalar `"apply-groups": "G1"` still reads as `"G1"` on the base, and ARCH-C10 is a non-goal. The YAML row, however, reads the same scalar as a list, so the YAML and JSON doors would diverge. Pin the JSON behaviour explicitly, for example with an xfail-strict test citing ARCH-C10.

### 2. High: the tripwire does not trip at runtime

`test_the_bundled_tree_never_runs_on_the_floor` only calls `universal_statements(bundled_tree)` directly. By design the floor equals the bundled nodes. So a walker that threads the wrong root (the current node, a subtree, or `{}`) is answered by the floor and produces byte-identical output.

**Executed** (`tc_wrong_impls.py`, using the correct implementation):
- `universal_statements(tree["c"]["system"]) is FLOOR` gives True.
- `universal_statements({}) is FLOOR` gives True.
- floor == bundled nodes gives True.

No output test can detect this.

**Proposed test:** `test_conversion_never_answers_from_the_floor`. It monkeypatches the floor in `junoscfg.display.constants` with a poisoned mapping, for example `apply-flags` set to `{"l": True}` and the other three removed, or a Mapping that raises on access. It then runs both catalogue rows through every reader, every writer and field validation on the bundled tree, and they must still pass.

### 3. High: `replace` rests on junoscfg's own output, not on device evidence

The only source is `examples/playbook/group_vars/routers.yml` of the downstream collection. Its header reads "Generated with: junoscfg convert -e yaml …", and it holds the kept key `apply-flags replace: true`.
- That is an artefact, which ranks below the schema model in the evidence hierarchy (ARCHITECTURE.md §8).
- Nothing shows that a device accepts `apply-flags replace` at all. P8's `?` will answer that.

Yet 8 set and curly nodes, the field-validator fixture and the floor literal pin `{"replace": [null]}` as the IR for every door.

**Proposals:**
- Record a specification challenge in `review.md`.
- Give the `replace` cases their own ids tagged `P8`, so that a P8 answer reverts only those cases.
- Keep `set … apply-flags replace` valid, since it is pinned.

**Missing consumer door.** Executed on the base: the downstream YAML shape, `apply-flags replace: true` in a BGP group (synthetic values), gives `set protocols bgp group G1 apply-flags replace` plus one `UNPLACED` diagnostic.

**Proposed test:** `test_the_consumers_apply_flags_spelling_is_kept`. It feeds that YAML through `convert_config`, expects the set line unchanged with nothing dropped, and pins whether the head reads it as the container or still reports it.

### 4. High/Medium: the old scalar spelling of `apply-flags` is not pinned

Executed on the base:
- `set apply-flags omit` and curly `apply-flags omit;` wrote JSON `{"apply-flags": "omit"}`.
- A nested `"apply-flags": "omit"` passed silently.

This is the IR that consumers stored, and a container writer may drop it silently.

**Proposed test:** `test_the_old_scalar_spelling_is_not_lost`. It runs top level and `system` × JSON, YAML and XML (`<apply-flags>omit</apply-flags>`). Each case must either read as `{"omit": [null]}` or be reported `UNPLACED`, and set output must still contain `apply-flags omit`. Add a migration note.

### 5. Medium: wrong helpers pass the helper's unit tests

**Executed** (`TC_IMPL=…` with `tc_wrong_impls.py`, 7 helper tests):

| Wrong implementation | Result |
|---|---|
| W1b: falls back to any root child, then the floor | passes 7/7 |
| W2: ignores `u`; the floor's names filter the root's children | passes 7/7 |
| W1: any root child, no floor | fails, but only by accident, through `OLD_TREE` |
| W4: universal first, own child second | caught |

The bundled tree has 1,026 nested children named like a root child, for example `system/services`. W1b misresolves all of them.

**Add these tests:**
- `schema_child(system, "interfaces", tree) is None`
- `schema_child(None, "system", tree) is None`
- A tree with a fifth `u`-flagged child `apply-x` and an unflagged `apply-flags`: `universal_statements` must equal {`apply-groups`, `apply-x`}. The same tree in `test_the_tree_is_authoritative`.
- At pipeline level, with `using_tree`: a tree whose `system` declares its own `apply-macro` leaf must read as that leaf in every reader. The bundled tree has no such collision, so a reader with a local universal-first lookup passes everything else.

### 6. Medium: the Group-H deletions are covered for set output only

`dict_walker` serves both set and curly output. The committed coverage is:
- the set-only device law;
- one synthetic JSON test, `bogus-container`.

The "0 firings" figure comes from a private instrumented run.

**Executed:** capture to curly to set, against capture to set, differs in 96 lines on the base. These are existing quoting and range defects in the curly writer, and they form a baseline to hold.

**Proposals:**
- Rerun `tc_probe_via_structured.py` at the head. The result must be the identical 96 lines, or commit the probe as a corpus test with a pinned baseline.
- Diff `outputs.py` at the head against `base-device.json`.

**The JVD baseline is not ready.** `base-jvd.json`, which the freeze cites, does not exist yet. `outputs.py --jvd` was still running at 05:38, PID 89191, started 05:13. C4 cannot be judged until it finishes.

### 7. Low: over-acceptance and gaps in the name scan

- **Bare and doubled `apply-flags` are not pinned.** The old grammar rejected a bare `set system apply-flags` (the leaf needed a value), and neither it nor `apply-flags omit replace` is pinned now. Add both to `test_an_apply_statement_is_rejected` unless a device shows otherwise. Add JSON `"apply-flags": {}` and `true` to the field-validation cases.
- **The name scan has blind spots.** It misses `startswith("apply-")`, f-strings and regexes. Add one of them to `test_the_scan_sees_each_retired_reading`, or document the limit.
