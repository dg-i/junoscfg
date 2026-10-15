## Findings

Independent Test/Challenge (fresh agent, no Builder reasoning, high risk floor) on tests
commit `af71973d567f99f765866c7513e0763a1baec576` against base `ea18fab`; probes under
`private_test_data/makeover-work/relative-null-flags/tc/` (base facts, a plugin swapping in
wrong implementations, proposed rows). Verdict: the test failed at base for the right reason
and caught most wrong fixes; two binding rows missing. Resolutions in the tests commit after
this record:

1. TC1 advisory: red at base for the right reason (4 failed, 6 passed). No change.
2. TC2 advisory: wrong fixes caught (top-level only, `{}` only, name order, json only,
   wrapped scalar, every `{}` with `wrap=True`). No change.
3. TC3 binding: a fix writing into the caller's selection passed the whole suite, because the
   purity law covered mappings only. Fixed: `TestNoWriterChangesTheIrItIsGiven::
   test_a_bare_selection_is_left_unchanged` (list, annotated list, `[true]`, `{}`, `true`;
   json, yaml and yaml-new bare doors).
4. TC4 binding: a normalizer that also turns an annotation's `true` into `[null]` passed,
   and would silently re-activate deactivated configuration. Fixed: annotated host entries in
   `_SELECTED_SOURCE` and `test_an_annotation_in_a_selected_list_stays_boolean`; spec names it.
5. TC5 advisory: a selected `[true]` uncovered. Fixed: row `a-list-of-true` (absolute
   `[[null]]`); spec says its device spelling stays open (NEW-R2).
6. TC6 advisory: set input in a selected `groups.group` uncovered. Fixed:
   `test_a_selected_group_list_from_set_input`.
7. TC7 advisory: scenario literals not asserted. Fixed: `test_the_scenarios_are_written_as_specified`;
   scenarios use the test's data.
8. TC8 advisory: other writers' relative output not pinned. Not adopted: the change edits
   only the JSON object stage, which set, structured and `yaml` do not call; pinning their
   base bytes would pin a pre-existing defect (relative set output of a selected list prints
   the Python repr), reported as a pending owner decision.
9. TC9 advisory: anonymizing conversion. Fixed: `test_an_anonymized_selection_is_spelled_alike`.
10. TC10 advisory: `from_dict({}, "json", wrap=False)` changes from `{}` to `[null]`.
    Decided option (b): `wrap=False` means a relative selection, the value under its last
    path key (the only caller is `pipeline_result`); stated in the spec, the `from_dict` and
    `junos_json_object` docstrings and `.openspec.yaml`. Option (a), normalizing in
    `pipeline_result` under the path, would re-wrap the selection and also change C5
    coercion, which the ruling does not cover.
11. TC11 advisory: docstrings over-claimed or went stale. Fixed in both tests.
12. TC12 advisory, pre-existing: a `None` value (YAML `ssh:`) selected relatively writes
    nothing, as `filter_dict_by_path` returns `None` for absent and null alike. Outside the
    ruling; reported as a pending owner decision.
13. TC13 advisory: non-break reasoning sound; residual risk for a program testing the
    relative object's truthiness (`{}` falsy, `[null]` truthy). Added to `.openspec.yaml`.

## Specification challenges

Raised by Test/Challenge against the Builder's unapproved draft delta (S1 to S4); the
Builder revised the draft before implementation, recorded in the freeze delta log. Each is
within the owner's PO-1 ruling and adds no behaviour beyond it.

- S1 Artifact: draft title "A relative selection is spelled as absolute output spells it".
  Counterexample (executed): set-input `groups` relative `{"group": [...]}` vs absolute list;
  C5 coercion. User impact: readers assume full equality. Proposed correction: retitle to
  presence flags and key order; name both exclusions. Decision: adopted in the draft (no
  owner ruling needed: narrows the Builder's own wording to the ruling).
- S2 Artifact: same, `[true]` wording. Counterexample: `[true]` reads as `[null]` or
  `[[null]]`. Proposed correction: follow absolute output, NEW-R2 open. Decision: adopted.
- S3 Artifact: same, no annotation exclusion. Counterexample: TC4. Decision: adopted.
- S4 Artifact: same, coercion "not covered". Proposed correction: "unchanged by this
  requirement". Decision: adopted (coercion forbidden here; pending owner decision C5).

## Pending owner decisions

- C5 (instruction-integrity): relative selections skip schema-context scalar-leaf coercion
  (`system.login` relative keeps `"class": ["super-user"]`). Recommended default: a
  follow-up fix rendering a relative JSON selection from the absolute object at its path.
- TC8: relative `set` output of a selected list prints the Python repr
  (`set "[{'explicit-priority': {}, ...}]"`). Recommended default: backlog entry.
- TC12: a selected `None` value writes nothing in relative output. Recommended default:
  backlog entry beside TC8.
- C8 (device question, open, not acted on): does a QFX5120 on 25.2R2-S1.5 accept `[null]`
  for `system services netconf ssh` via `load merge json`?
