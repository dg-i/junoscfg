## Findings

Independent Test/Challenge (fresh agent, high risk floor), on tests commit
`08139866e06ccdd71998e1234ba23fdbf90d9e3d` against base `332523c`; its probes ran on the
base code. Each finding and how the Builder resolved it, fixed in `c84d07d`:

1. B1 (binding) validation through the YAML schema went undetected: the every-door rows hold
   no meta key. Fixed: `TestValidateConfig::test_junos_yaml_is_judged_by_the_json_schema`,
   `TestJunosValidator::test_validate_yaml_as_json_uses_the_json_schema`, and the
   `cli-validate-only-yaml-new` message row now holds `_meta_acme`. Mutating `validate_config`
   to the YAML schema fails the first.
2. B2 (binding) validating a YAML-only value crashed (`on:` key, TypeError) or passed (date).
   Fixed: the check moved to the kernel, `junoscfg.input.find_non_json_value`, shared by the
   reader and `validate_yaml_as_json`, which returns an invalid result with kind and path;
   requirement and scenario added to validation/junos-json-yaml. Tests
   `test_a_value_json_cannot_hold_is_invalid`, `test_a_yaml_new_value_json_cannot_hold_exits_one`
   (4 fail with the check removed).
3. B3 (binding) refusal kinds: the implementation was already an allow-list; rows added for
   bool, null, float and date keys, `!!omap`, `!!pairs`, siblings of `configuration` and the
   document itself, with marker values checked absent from the message.
4. B4 (binding) the audit test passed under legacy routing. Fixed:
   `TestInputFormats::test_a_value_json_cannot_hold_is_refused` (yaml-new refuses, yaml reads).
5. B5 (binding) nothing proved dispatch goes through the table. Fixed: the table is a dict
   read at call time; `TestFormatEnum::test_the_rename_is_a_change_to_the_table` swaps the two
   YAML rows and checks to_dict, from_dict, convert_config, validate_config and the CLI.
6. B6 (binding) nothing pinned `yaml` as the IR dump. Fixed:
   `TestTheYamlWriterDumpsTheIr::test_the_output_is_the_ir_as_read` over every catalogue
   source; byte identity also measured (Evidence below).
7. B7 (binding) relative selection covered only mappings. Fixed: rows for `{}` and a selected
   list. The probe also showed relative JSON output of a selected list is not normalized
   (`"any": {}` where absolute output writes `[null]`); yaml-new matches it. Pending owner
   decision below.
8. B8 (binding) the anchor test could not fail. Fixed: a bare shared list, wrapped and bare.
9. Advisory: A1 left to the Reviewer (no JSON text round trip); A2 YAML 1.1 implicit typing
   kept (PyYAML's dumper quotes against it; a 1.2 loader would mis-read `1e3` the dumper leaves
   bare), pinned by `test_unquoted_words_are_read_as_pyyaml_reads_them` and documented; A3
   loader named in the spec, `_TRICKY` extended; A4 `.inf`/`.nan` read as JSON input reads
   `Infinity`/`NaN`, documented, in the property's value pool; A5 scope pinned; A6 meta keys
   and `apply-groups` in the property; A7 `test_the_device_spellings_are_written_as_json_writes_them`;
   A8 tests renamed by implementation, rename consequence in the decision record; A9 help test
   asserts the rename wording; A10 to A12 accepted as reported.

Fresh isolated Reviewer (separate agent, same model as the Builder, no Builder reasoning),
on records head `c95e67f`, code head `f5d677f`, base `332523c`. Verdict: **Changes required**,
three binding items; resolutions in the follow-up commit:

10. R1 (binding) the documented migration wrote yaml-new its reader refuses: a `yaml` file's
    unquoted date passed through `-i yaml -e yaml-new` (executed). Fixed: `dict_to_junos_yaml`
    runs `find_non_json_value` and raises `ValueError` with kind and path (CLI exit 2); tests
    `test_a_value_json_cannot_hold_is_refused_on_write`,
    `test_a_value_json_cannot_hold_stops_the_migration`; spec and guide updated.
11. R2 (binding) a self-referencing alias made yaml-new validation raise `RecursionError`
    (executed); an alias bomb walked the expanded tree. Fixed: `find_non_json_value` visits each
    container once and reports a container met again as kind `alias`, so cycles and aliased
    blocks are refused in linear time by reader, writer check and validation; rows for an alias and a cycle
    in the reader, kernel, validator and CLI tests. Interim policy pending the owner: SC-1, PO-2.
12. R3 (binding, documentation) the decision record said the rename changes no dispatch code.
    Fixed: its Consequences now name the alias-warning mechanism, detection, `validate_yaml`,
    `_READERS`/`_WRITERS` and CLI text; ARCHITECTURE.md points there.
13. Advisory: A1 developer guide updated (30 pairs, the table, the object stages); A2 NEL, LS
    and PS now written double-quoted (escaped) by yaml-new, test
    `test_a_yaml_only_line_break_reads_back_as_written`, `yaml` keeps PyYAML's behaviour (PO-4);
    A3 unknown implementation ids raise (`test_an_unknown_implementation_is_refused`);
    A4 accepted (secondary door, beta); A5 guide qualified for relative selections (PO-1);
    A6 pre-existing `yaml` date drop (PO-3); A7 ARCHITECTURE.md line checked, within cap.
    Re-measured by the Reviewer: base figures, 1,936/0 and 96/0, the 15 QFX `{}`; its legacy
    routing mutation failed 187 tests where the Builder counted 143 (both caught).

## Already provided

The JSON writer's and reader's normalization (reused, not copied); PyYAML `SafeDumper`;
`find_configuration`; the shape catalogue and device captures; `tools/compare_device_outputs.py`.

## Specification challenges

None recorded by Test/Challenge as a criteria contradiction; B2's omitted criterion was
added to validation/junos-json-yaml before review.

### SC-1 Aliases in yaml-new input

- Artifact: specs/conversion/junos-json-yaml, "A YAML value JSON cannot hold is refused"; D4.
- Counterexample: `configuration: &a\n  system:\n    x: *a\n` validated as yaml-new raised
  `RecursionError` (executed by the Reviewer on `c95e67f`).
- User impact: a crash on hostile or mistaken input; refusing aliased blocks also refuses
  hand-written yaml-new that shares a block through an alias, which the YAML parser accepts.
- Proposed correction: refuse a mapping or list reached through an alias (implemented as the
  interim: JSON has no shared blocks, the writer emits none, it ends cycles and alias bombs,
  and relaxing later is additive), or refuse cycles only. Scalar aliases and merge keys of flat
  mappings expand to a JSON tree and are accepted either way (Reviewer N1, executed).
- Decision: Pending owner decision (PO-2).

## Pending owner decisions

- PO-1 (from B7): relative JSON output of a selected list keeps `{}` and `true` where absolute
  output writes `[null]` (base behaviour, `junos_json_object` normalizes mappings only).
  Fixing it changes `json` output, a non-goal of this change; yaml-new keeps equivalence.
  Options: a follow-up fix in the JSON writer, or a backlog entry. Not backlogged by the Builder.
- PO-2 (SC-1): alias policy for yaml-new input. Interim: a mapping or list reached through an
  alias is refused; scalar aliases and flat merge keys are accepted.
- PO-3 (Reviewer A6, pre-existing): `yaml` input with an unquoted date drops the statement from
  set output (`host-name: 2026-10-15` gives no line). Out of scope (`yaml` stays as it is);
  follow-up fix or backlog entry is the owner's choice. Not backlogged by the Builder.
- PO-4 (Reviewer A2, pre-existing): `yaml` output writes NEL/LS/PS unescaped and reads them back
  as line breaks; yaml-new escapes them. Out of scope for `yaml`; owner's choice as above.

## Evidence

- Catalogue, base vs head, every shape x reader x {set, structured, json, yaml}: 1,936
  conversions, 0 differ (484 yaml outputs byte-identical).
- Device corpus, `tools/compare_device_outputs.py`: 0 of 96 conversions differ.
- Canonical full checkpoint `agent-ready check --set full --base 332523c` at `c95e67f`
  (code head `f5d677f`): every check passed, 360 s wall clock; suite 13,276 passed, 22 xfailed,
  37 skipped on 10 workers (72 s), coverage 93.09 %; schema-25.2 qualification and generation
  selected by `src/junoscfg/__init__.py`, both exit 0, run with physical dumps.
- Follow-up canonical full checkpoint at `a55c960`: every check passed, 170 s; suite 13,288
  passed, 22 xfailed, 37 skipped; coverage 93.11 %; schema-25.2 tiers exit 0. Base vs head
  rerun: catalogue 1,936/0, device 96/0.
- Earlier attempts, kept as evidence: the first refused admission (branch unassessed, fixed by
  declaring readiness in `27940a0`); the next two failed only the expensive tier (a symlinked
  dump directory; a vulture-whitelist edit that selected the tier, dropped in `f5d677f`).

## Verdict

Reviewer verdict on `c95e67f`: Changes required (R1 to R3). All three resolved as above; the
Reviewer named the follow-up obligations: focused tests and the fast set, and the full set
again because runtime code changed. Follow-up evidence below.

Correction review on `a55c960` (same Reviewer, archive copies, no git state change): R1, R2,
R3 resolved (executed: date migration refused, exit 2; cycle invalid via `validate_config` and
`-v`, exit 1; a 10^9-leaf alias bomb refused in 0.001 s); A1, A2 (yaml-new), A3, A5 fixed.
New N1 (binding, documentation): the interim was described as "every alias refused" while
code and spec refuse a mapping or list reached through an alias and accept scalar aliases and
flat merge keys (executed). Fixed by rewording SC-1, PO-2, the freeze delta, design 8 and the
guide (option a, documentation only). The Reviewer's verdict for that wording fix: **Merge**.

## Scope dispositions and follow-up evidence

Test/Challenge B1 to B8 and Reviewer R1 to R3 and N1 resolved in the change. Awaiting the
owner, none backlogged by the Builder: PO-1 (relative JSON list output), PO-2/SC-1 (alias
policy, interim in effect), PO-3 (`yaml` drops unquoted dates from set output), PO-4 (`yaml`
NEL/LS/PS), and the device question C8 (QFX5120 25.2R2-S1.5 loading `[null]` for `{}`).
