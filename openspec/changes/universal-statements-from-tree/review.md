## Findings

### Independent Test/Challenge (phase 4, STOP-T)

Report: `test-challenge.md` (fresh isolated role, at `b18c652` against base `dd7c8c4`). Rulings relayed by the orchestrator, with what the Builder did:

| Finding | Ruling | Disposition |
|---|---|---|
| 1 High: no test compares each door's universal statements with the device's own JSON; the JSON door's nested scalar | Accept; ARCH-C10 stays with change 13, pinned as a named carry-forward | `tests/corpus/test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements::test_every_door_reads_the_devices_universal_statements` over every capture × conf, set, XML (GR-OMIT skipped for conf, class `omitted-curly`); `tests/unit/convert/test_convert_api.py::TestLeafListPromotion::test_a_nested_json_scalar_universal_leaf_list_is_a_list`, strict xfail naming change 13 |
| 2 High: the tripwire does not trip at runtime | Accept | `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_conversion_never_answers_from_the_floor` poisons the floor and runs both catalogue rows through every reader, writer and strict validation (door exception in `tools/check_test_doors.py`, keyed to that file) |
| 3 High: `replace` rests on junoscfg's own output | No device evidence; keep the base's acceptance, mark the JSON/XML shape EVIDENCE_BLOCKED on P8, tag the test ids, record the specification challenge, add the consumer YAML test | `replace` cases carry `P8` in their ids (`...[replace-P8]`, `test_replace_is_clean_p8`); challenge S1 below; `TestApplyFlagsSpellingsAreKept::test_the_consumers_apply_flags_spelling_is_kept` |
| 4 High/Medium: the old scalar spelling is not pinned | Accept: read or reported, never dropped | `TestApplyFlagsSpellingsAreKept::test_the_old_scalar_spelling_is_not_lost` (top and `system` × JSON, YAML, XML); field validation reports a value on a container node (`'apply-flags' holding a value`) |
| 5 Medium: wrong helpers pass the helper tests | Accept all | `schema_child(system, "interfaces")` and `schema_child(None, "system")` are None; a fifth flagged `apply-x` and an unflagged `apply-flags`; `test_a_nodes_own_statement_wins_in_every_reader` (every door, a `system`-level `apply-macro` leaf); `test_the_tree_is_authoritative` covers the generator |
| 6 Medium: Group-H deletions covered for set output only | Pin the curly writer at the head (the same 96 lines) in a test or a measurement; wait for `base-jvd.json` before claiming C4 | measurement recorded in `evidence-freeze.md` and `metrics.md` |
| 7 Low: bare and doubled `apply-flags`; name-scan blind spots | Pin bare `set system apply-flags` as reported or rejected; leave `apply-flags omit replace` untested and ledgered; extend the scan to `startswith("apply-")` and f-strings | corrected after Reviewer finding 2: at 81ff738 no such test existed and the grammar accepted a bare `apply-flags`; now `test_an_apply_statement_is_rejected[apply-flags-needs-a-flag]` and `[apply-flags-needs-a-flag-at-the-top]` pin the grammar's rejection beside the field-validation report; the doubled form ledgered; the scan reads a prefix of a name and an f-string's literal part (`test_the_scan_sees_each_retired_reading`) |

### Fresh Reviewer (phase 6, STOP-R)

Report: `private_test_data/makeover-work/universal-statements-from-tree/roles/review.md` (fresh isolated role, head `81ff738` against base `dd7c8c4`). Verdict: CHANGES REQUIRED. Every ruling relayed by the orchestrator was accepted:

| Finding | Ruling and disposition |
|---|---|
| 1 High: a universal statement resolves inside `apply-flags` (`set system apply-flags apply-groups G1` valid and placed; `apply-macro M1 peer 203.0.114.7` inside it passed `--anonymize-ips` verbatim where 0.17.0 refused) | Fixed in the helper: `schema_child` gives no universal fallback inside a universal statement (the ids of every node inside one, kept with the tree's declared answer). `set_input` calls `schema_child` (both inline copies gone, finding 4). The grammar generator adds `universal_statement` to no rule that only a universal statement reaches (`_rules_only_inside`; `apply_flags`, `apply_macro__list`, `data__list` lose it), artifacts regenerated. Tests: `test_nothing_resolves_inside_a_universal_statement`, `TestApplyFlagsIsAContainerOfFlags::test_no_universal_statement_inside_apply_flags` (set ×2, curly, JSON), `TestAUniversalStatementIsValidatedWithItsNode::test_a_universal_statement_inside_apply_flags_never_passes` (set, JSON, XML: reported, strict raises, the anonymized run refuses without the address), and two rejected grammar lines |
| 2 High: a bare `apply-flags` newly accepted by the grammar; the cited test did not exist; a tag-only `apply-flags` unreported | The grammar requires a flag after a universal statement of flags (`"apply-flags" apply_flags`); the emptiness check ignores `@` keys. Tests: `test_an_apply_statement_is_rejected[apply-flags-needs-a-flag, apply-flags-needs-a-flag-at-the-top]`, `test_a_flag_known_only_by_its_tag_is_reported`; the Test/Challenge disposition row corrected above |
| 3 Medium: the cache holds the floor, so the poison test depends on order | Only a declared answer is cached; the tripwire asks an old tree before poisoning and then expects it to trip |
| 4 Low: `set_input` inlines the helper | With finding 1 |
| 5 Low: the generators answer a tree declaring none differently | Recorded beside `_universal_properties`: generation always runs the fixes, so the two agree on every tree `junoscfg schema generate` builds; the floor there serves only a bare `SchemaNode` handed to the public function |
| 6 Low: the migration note omits custom artifacts | "Regenerate custom artifacts" added to the removal fragment and both `declared-break` migrations |
| 7 Low: stale docstring in `anonymize/rules/group.py` | Carry-forward to change 5, which owns the anonymize walkers (C7) |
| 8 Carry-forward: tags on nested universal statements (`deactivate system apply-groups G1` with two groups widens to the whole leaf-list; a lone tag writes `set system`) | Ledgered as NEW-R7 for change 14 (the meta walk); probe P9 appended to `private_test_data/makeover-probes.md` |
| JVD rerun not completed by the Reviewer | Rerun by the Builder at the fixed head with a 120-minute limit (`evidence-freeze.md`) |

### Reviewer report, verbatim: Fresh Reviewer (phase 6, STOP-R): universal-statements-from-tree

Reviewer: fresh, isolated role (no Builder reasoning). Head `81ff738` against merge base
`dd7c8c4` (v0.17.0). Read in order: evidence freeze, delta
(`specs/schema-pipeline/universal-statements/spec.md`), `display/CONTRACT.md`, the
Test/Challenge report and its dispositions (`review.md`), the new and corrected tests,
the diff. Probes and outputs are in this folder (`rv_*`), synthetic values only.

#### Verdict

**CHANGES REQUIRED.** Two High findings: the change makes the universal statements valid
*inside* `apply-flags` (a spec violation that also lets an address through
`--anonymize-ips` where 0.17.0 refused), and it loosens the grammar to accept a bare
`apply-flags` that 0.17.0 rejected. The Test/Challenge disposition cites a test for the
second that does not exist. The rest is sound: the helper's semantics, regeneration,
device and JVD measurements, the name-fallback figures and the docs all check out.

#### Ranked findings

##### 1. High: a universal statement resolves inside `apply-flags`, so all three layers accept `apply-flags apply-groups G1`

- Violates: the delta, "apply-flags is the container the device writes": "Any other word
  under `apply-flags` SHALL be kept whole and reported `UNPLACED` by the set and curly
  readers, reported `UNPLACED` by field validation from JSON, YAML and XML, and rejected
  by the grammar."
- Diff lines: `src/junoscfg/display/constants.py:527-541` (`schema_child` falls back to
  the root's statements below *any* node, the universal node itself included);
  `src/junoscfg/convert/input/set_input.py:463-469` (the same rule inlined);
  `src/junoscfg/validate/grammar_generator.py:361-365`, which adds `universal_statement`
  to every rule. The shipped grammar has `apply_flags: "omit" | "replace" | universal_statement`.
- Counterexample (executed, `rv_probe_fv.py`, the probe in this file's section "Prompts"):
  `set system apply-flags apply-groups G1` and `set system apply-flags apply-flags omit`:
  head `validate_config` is valid, the IR is `{"apply-flags": {"apply-groups": ["G1"]}}`,
  there are no diagnostics, and `strict=True` passes from set, curly, JSON and XML. At
  base all four doors keep the line whole, report it, and reject it.
- Trust boundary: with `--anonymize-ips`, `set system apply-flags apply-macro M1 peer
  203.0.114.7` leaves the address verbatim at head. At base the run refused
  (`rv_anon_in.set`).
- Fix: one rule in the helper. A node flagged `u` gets no universal fallback, so
  `schema_child` answers only its own children there. `set_input` calls `schema_child`
  instead of its two inline copies (also finding 4). The grammar generator does not add
  `_UNIVERSAL_RULE` to a rule reached from a universal node. Add the two lines to
  `test_an_apply_statement_is_rejected`, and add set, curly and JSON cases to
  `TestApplyFlagsIsAContainerOfFlags` and `TestAUniversalStatementIsValidatedWithItsNode`.

##### 2. High: a bare `apply-flags` is newly accepted by `validate_config`; it is unpinned, undeclared, and the disposition cites a test that does not exist

- At base, `set system apply-flags` and `set apply-flags` are invalid (the leaf needed a
  value). At head both are valid: the grammar rule is `"apply-flags" apply_flags?`, in
  `junos-set.lark` line 6.
- `openspec/changes/universal-statements-from-tree/review.md:15` claims that
  `test_an_apply_statement_is_rejected[apply-flags-needs-a-flag]` pins it. The
  parametrisation at `tests/corpus/test_shipped_artifacts.py:155-168` has no such id and
  no bare line.
- This is a second answer. Field validation reports the same IR as
  `'apply-flags' without its value` (`src/junoscfg/convert/field_validator.py:259-271`),
  while the grammar accepts it.
- The emptiness check misses a dict that holds only a tag. A lone `deactivate system
  apply-flags omit` reads as `{"apply-flags": {"@omit": …}}`, is written as `set system
  apply-flags`, and nothing reports it. The base kept the line and reported it.
- Fix: render a universal container whose children are all flags as mandatory in the
  grammar (`"apply-flags" apply_flags`). At `field_validator.py:266`, ignore `@` keys
  when deciding whether the container is empty. Add the missing row with
  `set system apply-flags` and `set apply-flags`, and correct the disposition. If a device
  probe shows that Junos accepts a bare `apply-flags`, drop the field-validation report
  instead. Either way there must be one answer.

##### 3. Medium: the runtime tripwire can be defeated by the cache

- `universal_statements` caches the *floor* answer per root id
  (`src/junoscfg/display/constants.py:517-523`).
- `test_conversion_never_answers_from_the_floor`
  (`tests/unit/display/test_universal_statements.py:160`) poisons the floor without
  clearing `_universal_cache`. A walker that passes the wrong root and was answered
  earlier in the same process gets the cached floor under the poison.
- Executed: `rv_probe_tripwire.py` prints `NOT TRIPPED`. The tripwire's result depends on
  test order.
- Fix (product, simpler): cache only a declared answer
  (`if declared and isinstance(root, dict)`), so the floor is never cached.

##### 4. Low: `set_input` inlines the helper instead of calling it

- At `set_input.py:463-469` and `:804-809`, the reader looks up `universal_statements`
  directly, although the delta says the readers "SHALL use the helper".
- The two copies already disagree: the second resolves `KEY_ALIASES` first and the first
  does not.
- Fix: use `schema_child`, together with finding 1.

##### 5. Low: the two generators give two answers for a tree that declares none

- `grammar_generator.py:330-332` reads only the flag. `schema_generator.py:44` adds the
  floor.
- Unreachable in production, since generation always runs the fixes. Record the reason
  beside `_universal_properties`, or let the floor serve only loaded trees.

##### 6. Low: the migration note omits custom artifacts

- A tree from `junoscfg schema generate` 0.8.0-0.17.0 (under `JUNOSCFG_ARTIFACTS` or
  `--artifacts`) is authoritative, so it keeps the leaf `"apply-flags": "omit"`
  (`rv_probe_017tree.py`).
- Fix: add "regenerate custom artifacts" to the removal fragment and to `.openspec.yaml`
  `migration`.

##### 7. Low (carry to change 5): a stale docstring in the anonymizer

- `src/junoscfg/anonymize/rules/group.py:11-14` still says that only the generators read
  the `universal` flag and that the bundled artifacts predate the fix.
- C7 keeps `anonymize/` untouched, so this belongs to change 5.

##### 8. Carry-forward: tags on nested universal statements

- `deactivate system apply-groups G1`, with G1 and G2 set, is now written
  `deactivate system apply-groups` (curly: `inactive: apply-groups [ G1 G2 ]`).
- A lone `deactivate` or `protect` of one writes `set system` and drops the tag without
  a diagnostic, where the base kept the line and reported it (`rv_probe_tag.*`).
- The root already behaved so at base. These are mission candidates 4 and 6 (the leaf-tag
  reader), now reaching below the root.
- Device artefact needed: `deactivate system apply-groups G1` with two groups, in set,
  XML and JSON.

#### What I checked and found sound

- **Helper semantics.** `schema_child` answers the node's own child first; the test and
  every door confirm it.
- **Name lists.** No `apply-*` name list remains in `src/`, outside `xsd_fixes`, the
  floor and the `anonymize`/`audit` exemptions.
- **Regeneration (3 min 30 s).** The structure tree, grammar and both JSON schemas are
  byte-identical to the committed artifacts. The metadata differs only in
  `generated_at`.
- **Device comparison, rerun.** 18 of 236 differ. The output and the diff are
  byte-identical to the Builder's `head-device.json` and `diff-device.txt`.
- **Field validation on the captures.** Every door's diagnostics only lose the 12
  `UNPLACED` warnings, so the new reports raise no false positive there. The
  "holding a value" rule is also clean on `pkf`, `k` and `fd` containers
  (`rv_probe_fv.*`).
- **Name fallbacks, rerun on the base.** 678 consulted (294/260/40/84), 0 fired, over 236
  conversions.
- **Targeted tests.** 5,077 passed and 15 xfailed: the change's nine files plus
  `tests/contract/`.
- **The `replace` decision (S1).** The grammar keeps the base's acceptance, which is
  consistent with the evidence hierarchy. However, nested `apply-flags replace` loses
  the base's `UNPLACED` report and takes an inferred JSON shape. That is declared in the
  changelog and tagged P8. S1 stays pending.
- **Floor.** The retirement trigger is named and the static tripwire is sound (finding 3
  covers the runtime one).
- **Records.** Version 0.18.0 is in both files and the lock. The changelog fragments,
  CONTRACT and docs are coherent apart from findings 2, 6 and 7.

JVD rerun: **not completed.** The background limit stopped it at 30 minutes, before it
wrote its result; the Builder's run took about 40 minutes. The figure "11 of 4,605 differ"
rests on the Builder's `head-jvd.json` and `diff-jvd.txt` alone. It goes to the
carry-forward list: rerun `outputs.py --jvd` with a timeout of at least 60 minutes.

#### Prompts

1. **Trust boundary.** Configuration text under `--anonymize-*`. Finding 1 turns a
   refused run into a verbatim address. Separately, the anonymizer never rewrites a
   nested `apply-macro` value, at base and head alike (`rv_anon_in2.set`). That is
   change 5's, carried.
2. **Incompatible-but-valid input.** A custom tree from 0.8-0.17 (finding 6).
3. **Shared blind spot.** The tests and the implementation share the "universal
   everywhere" assumption, so no test puts a universal statement under `apply-flags`
   (finding 1). The independent evidence is the delta's own sentence and the base's
   grammar.
4. **Second answer.** The grammar against field validation on a bare `apply-flags`
   (finding 2); `set_input` against `schema_child` (finding 4); the grammar generator
   against the JSON-schema generator on the floor (finding 5).
5. **Figures.** 678/0, 18/236, regeneration and the JVD rerun are reproduced. Timing was
   not rerun, so the 2-6 % figure rests on the Builder's `timing.py`; that goes to the
   carry-forward list. The non-goals hold.

#### Specification challenge

- Artifact: the delta's scenario "A statement below the root" asserts the statements are
  valid "at every level" without excluding the universal statements' own subtrees.
- Counterexample: finding 1.
- User impact: grammar, reader and field validation accept and place content that the
  device's `apply-flags` cannot hold, and anonymization lets it through.
- Proposed correction: add "A universal statement is not resolved inside another
  universal statement", with the two rejected lines as its tests.
- Decision: pending owner.

## Specification challenges

### S1: `apply-flags replace` is modelled without device evidence

- Artifact: delta `specs/schema-pipeline/universal-statements/spec.md`, requirement "apply-flags is the container the device writes", and the floor in `src/junoscfg/display/constants.py`.
- Counterexample: proposed probe (P8 in `private_test_data/makeover-probes.md`), not executed. The only source of `apply-flags replace` is the downstream collection's example, which junoscfg itself generated (Test/Challenge finding 3). No capture shows that a device accepts `replace` or how it writes it in JSON or XML.
- User impact: if the device writes `replace` in some other shape, JSON and YAML output of a set or curly `apply-flags replace` would not load as written. If the device rejects `replace`, the grammar accepts a line that the device refuses. Both were already true on the base, which accepted it as a leaf value.
- Proposed correction: answer P8. Keep `replace` as a flag if the device prints it so; otherwise drop it from the fix and the floor, and reject it.
- Decision: Pending owner decision. Interim action: the base's acceptance is kept. `replace` is the second presence flag beside `omit`, so the grammar and the consumer's configuration keep validating. Its JSON/XML shape is EVIDENCE_BLOCKED on P8, and its tests carry `P8` in their ids, so they can be reverted alone (owner intake 2026-10-11: merge with recorded interim action).

### S2: a universal statement inside another (Reviewer)

- Artifact: delta `specs/schema-pipeline/universal-statements/spec.md`, scenario "A statement below the root" ("valid at every level", with no exclusion for the universal statements' own subtrees).
- Counterexample: executed by the Reviewer (`rv_probe_fv.py`, `rv_anon_in.set`). At `81ff738`, `set system apply-flags apply-groups G1` and `set system apply-flags apply-flags omit` validate and are placed with no diagnostic from set, curly, JSON and XML. `set system apply-flags apply-macro M1 peer 203.0.114.7` passes `--anonymize-ips` with the address verbatim. 0.17.0 rejected, reported and refused all of them.
- User impact: grammar, readers and field validation accept and place content the device's `apply-flags` cannot hold, and anonymization lets an address through.
- Proposed correction: "A universal statement is not resolved inside another universal statement", with the two rejected lines as its tests.
- Decision: Pending owner decision. Interim action: applied in the delta (requirement "One helper resolves a universal statement at every level", scenario "Not inside a universal statement"), the helper, the reader and the grammar. This restores the base's rejection, and it is reversible by dropping the inside-set check (owner intake 2026-10-11: merge with recorded interim action; orchestrator ruling 1).

## Verdict

Pending.
