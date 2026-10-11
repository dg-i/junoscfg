<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): IDs OPEN-2, NEW-C1, OPEN-3 (plan row 3, inventory group G2); assurance `balanced`; fast-forward into local `master`, archive, tag, never push.
- C3 one change. C4 one reserved record for every kept statement, a declared break on `consumer` and `cli`, minor 0.17.0 (C8). C5 the valid statement after a bare one is placed (the approved scenario and two tests are corrected by the delta). C6 the key is `junoscfg:unplaced`, never `@`-prefixed. C7 a value-less leaf is reported on every door; DEV-16 stays with change 9. C9 kept meta commands share the record; the meta walk is change 14's.

## Requirements

- `specs/conversion/entry-keys/spec.md`, MODIFIED "A statement the reader cannot complete is kept whole" (governing `openspec/specs/conversion/entry-keys/spec.md`).
- Contradicted requirement, quoted: the current requirement says the reader "SHALL keep it whole from its keyword at its parent", and its tests pin "a group after a bare one is kept whole as well". The delta keeps it at its parent, in the parent's record, and places the valid statement.
- Unchanged and still binding: `conversion/writers` ("A writer leaves the IR it is given unchanged"), `validation/keyed-entries` (an entry without its key field is `UNPLACED`), `conversion/curly-meta-tags` (a tagged macro data line is kept whole and reported).

## Evidence

- Observed on `f0bb6aa` (`private_test_data/makeover-work/kept-whole-statements/repro.py`, `repro-master.out`, `doors.py`; synthetic values): the three reproductions below.
  - OPEN-2: `set apply-groups G1` + bare `set apply-groups` gives IR `{"apply-groups": ["G1"]}`, output `set apply-groups G1`, no diagnostic; reversed, IR `{"apply-groups": true, "apply-groups G1": true}`, both reported. Same for `apply-groups-except`.
  - NEW-C1: `host-name router1` then bare `host-name` gives `"host-name": null`, output `set system host-name`, no diagnostic; same for `members`; JSON `null`, YAML empty, XML `<host-name/>` and curly `host-name;` all write `set system host-name` silently.
  - OPEN-3: `apply-macro 12345 "KADJBF KU!H" balks XXXXX` and `shell "c sh"` lose their quotes in set, curly and the JSON key.
- Owning code: `convert/input/set_input.py` `_keep_whole` (`current.setdefault(key, True)`, `_parse_value` per token), the leaf branch of `_merge_tokens` (`current[token] = None`), `_keep_meta_whole`; `convert/field_validator.py` `_walk` (a value-less leaf is validated as nothing); writers in `convert/output/dict_walker.py`.
- `@` keys: `validate/schema_generator.py` gives every container `patternProperties: {"^@": {}}`, so an `@`-prefixed record would validate where the joined key was rejected; `dict_walker`, `field_validator`, `json_output`, `normalization`, `anonymize/walker`, `audit/walker` skip `@` keys (C6).
- Blast radius of the value-less-leaf report (`private_test_data/makeover-work/kept-whole-statements/null_leaves.py`, every device JSON/XML capture in `tests/data/device/` and the private JVD derivations, 100 files): 12 hits, all `interfaces unit description` from XML `<description></description>`, the DEV-16 reader defect (the device writes `description ""`, recorded as `xml-empty-value-lost`); no JSON capture holds a value-less leaf.
- Device: the corpus marks a leaf with no value and a bare `apply-groups` `CORRECTLY_REJECTED` (`tests/corpus/test_set_corpus.py`); the fourth `apply-macro` value is rejected (vMX 23.2R2-S7.5, recorded in the entry-keys spec). A statement the device rejects has no device spelling, so the record's spelling is junoscfg's.

## Non-goals

As `proposal.md`: the meta walk (change 14), XML empty text (DEV-16, change 9), a reader-wide `true`/`[null]` spelling (change 13), anonymizing inside a kept statement (change 5), unsupported set verbs (change 15).

## Acceptance criteria

- Every test id the delta names exists; the new and corrected ones fail on the merge base `f0bb6aa` and pass after the change; `agent-ready reconcile` passes.
- Catalogue rows in `tests/support/shapes.py` for OPEN-2, NEW-C1 and OPEN-3 read the same IR from set, structured, JSON and YAML, every writer's output reads back as it, set output is pinned, and the JSON/YAML renderings are rejected by the bundled schemas (`valid=False`).
- Tests that pinned the old key spelling move to the record with the declared break; none is weakened, and every other kept-whole test keeps its meaning.
- The device law (`tests/corpus/test_device_renderings.py`) passes; `known-differences.json` changes only through `tools/device_differences.py`, and every class it loses is explained by this change.
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

None, because the reader adds one dict lookup per kept statement and the writers one branch per level; the full suite's runtime is the check.

## Outstanding decisions

None, because C1–C9 are resolved by precedence and repository rules.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high (declared break on `consumer` and `cli`; zones conversion, kernel, surface)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer at least as capable as the Builder; Finalizer duties run by the Builder under the owner's brief
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `574b982` and the delta. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, phase 4: acceptance tests written. On the merge base `f0bb6aa`, `tests/unit/convert/test_set_input.py`, `test_field_validator.py`, `tests/contract/test_format_matrix.py` and `test_round_trip_validates.py` give 172 failed, 3,857 passed: every new acceptance node and every moved spelling fails; the six `test_a_leaf_with_a_value_is_clean` guards pass. Added during the phase: a kept meta command that names no whole kept statement cannot be tagged in curly text (on the base, structured output dropped it silently or moved the tag onto the longer statement), so the delta's quotes scenario says structured output leaves it out with a note; the test ids for the lone and curly value-less leaf and for meta commands joined the requirement. The main spec's `Tests:` line names the two renamed tests (`..._is_placed`), an id correction `agent-ready reconcile` requires; the requirement text is applied in phase 7. Approved under the owner's unattended-run instruction of 2026-10-11. Resume point: STOP-T, independent Test/Challenge.
- 2026-10-11, Test/Challenge (`test-challenge.md`, findings F1–F8), every finding accepted by the orchestrator. Consistency: C6's rationale was false (170 schema statements carry a YANG module prefix with `:`); corrected, the key itself stands (no name equals it). C7 changed: fix A, DEV-16 folded into this change (an empty XML element of a value-taking leaf reads as `""`, cited capture `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.{set,json,xml}.gz`), so the XML door leaves the value-less sources and `<description></description>`/`<description/>` are clean cases; `xml-empty-value-lost` leaves `known-differences.json` through the tool. New criteria: the public `anonymize()` refuses a non-empty record (F2); a record that is not one line of words or no record is refused on read and by the writers, with a line-count bound (F3, F4); `edityaml` wildcards skip the record (F5); stronger quote, multiple-report, presence-leaf, JSON value-less spellings, YAML source, revert, audit and CLI cases (F6, F7); line order is layout, so the rows pin lines with `written` and the unit tests compare sorted lines (F7); the C5 challenge recorded in `review.md` and two non-colliding siblings added (F8). Invalidated: the XML parameters of `TestALeafWithoutItsValueIsUnplaced` and the `apply-macro` bare case of `test_a_bare_keyword_never_meets_its_placed_node` (a bare `apply-macro` is the generic bare name-keyed list, read as before; no device evidence for it), removed from the delta. No assertion weakened. Rerun: unit, contract, corpus with `--jvd --device-grammar`, full check.
- 2026-10-11, phase 5: implemented. The set reader's refusal of a statement it would keep with an unquoted `;`, `{` or `}` measured over 1,716 device and JVD set/curly files (`refusal_radius.py`): none refused (a JVD template's `${NAME}` is a word, as the lexer reads it). `known-differences.json`: 932 → 928 lines, class `xml-empty-value-lost` removed by `tools/device_differences.py`.
- 2026-10-11, phase 5 complete: full check green at f8ea357 (6,768 passed, 45 skipped, 21 xfailed; the one warning is the pre-existing `FutureWarning: Possible nested set` from `field_validator.py`, DEV-V5, change 20); `agent-ready lane`, `fields`, `reconcile` pass; `tests/corpus --jvd --device-grammar` 109 passed, 36 skipped. Resume point: STOP-R, the fresh Reviewer on f8ea357 against the merge base f0bb6aa.
