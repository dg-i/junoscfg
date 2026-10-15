## Findings

Independent Test/Challenge (fresh agent, Opus, no Builder reasoning, high risk floor) on tests
commit `930e123` against base `adb6fb7`. It built a reference implementation of design.md and
18 wrong implementations (`private_test_data/makeover-work/yaml-depth-ceiling/tc/`): 14 caught.
Verdict: changes required. Resolutions, all in the tests and records commit after this one:

1. TC1 binding (test defect): `test_a_value_past_64_levels_is_invalid` asserted the eleven
   shared hosts valid, but the minimal schema rejects `syslog`. Fixed: the shared document is
   judged equal to the same document written out.
2. TC2 advisory: `validate_config` had no cycle row. Fixed: `CYCLE` row in
   `TestValidateConfig::test_a_yaml_new_shared_block_and_deep_document`.
3. TC3 advisory: anonymized doors `cli-read-yaml-new-cycle`, `cli-read-yaml-deep` missing.
   Fixed: both rows added.
4. TC4 advisory: the writer's ceiling through the pipeline was untested (JSON input 70 deep
   to `-e yaml-new`: exit 0 at base, refused now; `RuntimeError` when anonymizing, as for
   every writer refusal at base). Fixed:
   `TestJunosYamlWriter::test_json_input_past_64_levels_is_refused_as_yaml_new`; records
   (SC1).
5. TC5 advisory: a kept size bound of 1000x passed. Fixed: kernel row `ten-to-the-sixth`
   (10^6 values written out) must pass.
6. TC6 advisory: `test_an_ir_64_levels_deep_and_any_reuse_is_written` named in no delta.
   Fixed: named under both requirements.
7. TC7 advisory: meta-key content in the `yaml` reader untested. Fixed with SC1:
   `TestIrYamlReader::test_a_meta_key_subtree_is_not_walked`,
   `test_a_deep_sibling_of_the_configuration_is_refused`.
8. TC8 advisory: depth-before-cycle order and detected YAML uncovered. Fixed:
   `TestFindNonJsonValue::test_a_cycle_closing_at_step_65_is_a_cycle`,
   `TestConvertReadsAndWrites::test_detected_yaml_refuses_a_cycle`.

## Evidence

- Canonical full checkpoint at `a10ba71` (code head `431eb62`): every check passed, 351 s;
  13,417 passed, 22 xfailed, 37 skipped; coverage 93.12 %; schema-25.2 tiers exit 0.
- Byte identity base `adb6fb7` vs head: device corpus 0 of 96 conversions differ
  (tools/compare_device_outputs.py); catalogue 0 of 2,435 (every shape x reader x
  {set, structured, json, yaml, yaml-new}); device renderings written as yaml and yaml-new
  and read back into every writer 0 of 240.
- Door probe (doors-base.txt, doors-head.txt): the anchored-beside idiom, nested anchors and
  a 4^5 bomb read at head; cycles refused at every door, the `yaml` reader included; values
  past 64 levels refused with their path; the 10^9 bomb runs past 20 s (accepted).

## Specification challenges

### SC1 The `yaml` reader's reach, and the not-a-break reasoning (Test/Challenge, binding)

- Artifact: `.openspec.yaml` `declared-break`; proposal ("Not a break"); ADDED requirement.
- Counterexample (executed, tc/probe_doors.py): with `-i yaml`, a list 70 deep under
  `_meta_acme`, a cycle reached only through `_ansible_acme`, and a list 70 deep in a key
  beside `configuration` each convert at base to `set system host-name r1` and were refused
  by the draft. `-e yaml-new` from other readers newly refuses; anonymizing gives
  `RuntimeError`, not `ValueError`.
- User impact: the Ansible collection uses legacy `yaml` with `_ansible_*` keys.
- Proposed correction: (a) leave meta-key content out of the legacy check and restate the
  reasoning honestly, or (b) declare a break.
- Decision: (a), within the owner rule (fix junoscfg's own recursion; `_strip_meta_keys` never
  walks meta keys). Keys beside `configuration` stay checked: the cleanup walks them. The
  reasoning now names every newly refused case (data 65 to about 490 levels deep; beyond, PyYAML
  fails at base), the anonymized `RuntimeError` and `-e yaml-new`; patch kept, reported to the
  owner as overrulable to a minor.

### SC2 The writer's root (advisory)

- Artifact: ADDED requirement, "the IR as it will be wrapped".
- Counterexample: tests and design count a bare selection from its own root.
- Decision: adopted, "the IR as written: wrapped in `configuration`, or the bare selection".

### SC3 "has no JSON spelling" for a `yaml` cycle (advisory)

- Decision: kept (the `yaml` reader's IR is the JSON dict); the guide says so.

### SC4 64 against the evidence (advisory; holds)

- Decision: the freeze now states what its scripts do not count (a flag's `[null]` index,
  `@` annotations, an `rpc-reply` wrapper: at most about 4 steps) and that no schema node
  recurses.

## Pending owner decisions

- The break call (patch) for documents holding data 65 to about 490 levels deep; recorded
  default patch.
- C5, C6, C7, C8 of instruction-integrity.md.
