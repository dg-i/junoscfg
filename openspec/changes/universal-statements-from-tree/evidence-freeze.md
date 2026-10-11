<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): IDs ARCH-C06, ARCH-C08, DEV-V2 apply-flags half (plan row 4, inventory group G1); assurance `balanced`; fast-forward into local `master`, archive, tag, never push.
- C3 one change. C4 head outputs are compared with the base over the device captures and the JVD corpus, and every difference is explained or its cause reverted. C5 `apply-flags` is the device's container of presence flags `omit` and `replace`. C6 the floor stays without a warning, with its retirement trigger named and a tripwire. C7 `anonymize/` and `audit/` are untouched. C8 a declared break on `consumer` and `cli`, minor 0.18.0. C9 the JSON-schema generator follows the tree; the floor only for a tree declaring none.

## Requirements

- `specs/schema-pipeline/universal-statements/spec.md`, a new capability: ADDED "One helper resolves a universal statement at every level", "A tree that declares none runs on a compatibility floor", "A flag helper reads the node, never a name", "apply-flags is the container the device writes".
- Contradicted, quoted: `tests/unit/validate/test_schema_generator.py::TestUniversalStatementsReachEveryContainer` ("The names come from `UNIVERSAL_STATEMENTS` in the kernel, with any the tree declares through the `universal` flag added"), and `tests/unit/validate/test_xsd_fixes.py::TestGroupDMissingElements::test_apply_statements_are_modelled_once_on_the_root` (`assert root.children["apply-flags"].is_leaf`). The delta makes the tree authoritative and `apply-flags` a container; both tests are corrected to it, with the reason in their docstrings.
- Unchanged and still binding: `conversion/entry-keys` (`apply-groups` takes one name, `apply-macro` at most three values, a statement the reader cannot complete is kept whole), `conversion/structured-input` (the device's `{ /* OMITTED */ }` placeholder is reported), `conversion/writers` (a writer leaves its IR unchanged).

## Evidence

- Observed on `dd7c8c4` (`private_test_data/makeover-work/universal-statements-from-tree/repro.py`, `repro-base.out`; synthetic values): set and curly `set groups GR-OMIT system apply-flags omit` and `set system apply-flags omit` go to the `junoscfg:unplaced` record with one `UNPLACED` warning each; strict raises. At the top, `set apply-flags omit` reads as `"apply-flags": "omit"`. JSON, YAML and XML read `{"apply-flags": {"omit": [null]}}` at every level and report nothing. XML and YAML read a nested `apply-groups` with one group as the scalar `"G1"`, the top level and set input as `["G1"]`.
- Device: `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.{set,xml,json}.gz` and `.../qfx5120-25.2R2-S1.5/...` (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5), group `GR-OMIT`: set `set groups GR-OMIT system apply-flags omit`, XML `<apply-flags><omit/></apply-flags>`, JSON `"apply-flags": {"omit": [null]}`; the device JSON writes a nested `apply-groups` as a list (`["GR-MACRO"]`). The source curly is `apply-flags omit;` (`tests/data/device/synthetic/sources/junoscfg-oracle.conf.gz`).
- `apply-flags replace`: pinned valid by `tests/corpus/test_shipped_artifacts.py` since change `validate-ansible-output` (0.7.0). It comes from a production configuration the downstream collection renders: `examples/playbook/group_vars/routers.yml` of `dg-i/ansible-collection-junos-config`, `apply-flags replace` under `protocols bgp group`. There is no device JSON or XML of it: probe P8 (`private_test_data/makeover-probes.md`).
- Blast radius of closing `apply-flags` to two words: the JVD clone holds no `apply-flags`; the device captures hold only `omit` (4 groups, 2 releases); `tests/data/device/grammar-corpus.json` holds none.
- Name fallbacks (inventory `inv-a-schema.md`, `c08_fallbacks.py`, `c08_plugin.py`): consulted 678 times and fired 0 times over 236 conversions of every `tests/data` capture, and 0 times over 5,869 unit and contract tests. Every consulted key is a universal statement below the root or a key the 25.2R2 tree lacks.
- Regeneration on the base reproduces the committed artifacts byte for byte (`metrics.md`).
- Base outputs: `base-device.json` (236 conversions: every `tests/data` capture to set, structured, JSON and YAML, with diagnostics) and `base-jvd.json` (every JVD `.conf` to set, structured and JSON, hashed, with diagnostics), both from a worktree of `dd7c8c4`.

## Non-goals

As `proposal.md`: the anonymizer's traversal and `_replace_apply_groups` (change 5); the audit walker's group references; the name-wide Group-H matchers (NEW-A-S1, change 10); JSON scalar leaf-lists (ARCH-C10) and `KEY_ALIASES` (ARCH-C09), change 13.

## Acceptance criteria

- Every test id the delta names exists. The new and corrected ones fail on the merge base `dd7c8c4` and pass after the change, except the stated guards (the floor test of the schema generator, the old tree's `apply-groups`). `agent-ready reconcile` passes.
- Catalogue rows in `tests/support/shapes.py` for `apply-flags omit` (the device's GR-OMIT, every reader, set output pinned to the device line, valid JSON/YAML) and for universal statements below the root.
- Head and base outputs agree over `tests/data` and the JVD corpus, except differences each explained by the device or the requirement (C4).
- Artifacts regenerated with `junoscfg schema generate` from `25.2R2-S1.5_qfx5120.xsd`; a second regeneration leaves them unchanged; schema tier (`--schema`) and JVD tier (`--jvd`) pass; the device law passes, and `known-differences.json` changes only through `tools/device_differences.py`.
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

A lookup that misses a node's children now asks the root's universal statements: one dict lookup on the tree, or one pass over the root's ~80 children for a tree read through `SchemaNode`. The full suite's runtime and the JVD tier are the check; the largest JVD file is timed at base and head (developer guide, "Entry lookup or a schema-wide walk").

## Outstanding decisions

None, because C1–C9 are resolved by precedence and repository rules. P8 (the JSON/XML shape of `apply-flags replace`) is recorded as an inference with a probe, and it decides nothing this change ships for `omit`.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high (cross-domain: schema-pipeline, conversion, validation; declared break on `consumer` and `cli`)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer at least as capable as the Builder; Finalizer duties run by the Builder under the owner's brief
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `ce24d30` and the delta. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, phase 4: acceptance tests written. On the merge base `dd7c8c4`: `tests/unit/display/test_universal_statements.py` fails to import (`schema_child`, `universal_statements` do not exist), so its nine tests fail; over the other eight files and `tests/contract/`, 111 failed, 4,891 passed. Every new acceptance node fails except these guards, which pass on both sides by design: `test_another_word_is_kept_whole_and_reported[system,group]` (the nested line was already kept), `TestAUniversalStatementIsValidatedWithItsNode::test_nested_statements_are_clean` and `::test_a_bare_nested_statement_is_unplaced` (the exemption hid both), `TestUnplacedContentKeepsItsKeywords::test_it_is_still_reported`, the two new valid lines of `test_an_apply_statement_validates` (the old grammar took any value), and the rows' JSON and YAML readers of `apply-flags-omit-as-the-device-writes-it` (JSON, YAML and XML already read the device's shape). Corrected by the delta (C5, C9): `test_apply_statements_are_modelled_once_on_the_root` loses its two single-leaf assertions on `apply-flags`, now `test_apply_flags_is_the_devices_container_of_flags`; `TestUniversalStatementsReachEveryContainer._tree` declares the four statements as the fixed tree does, and its docstrings no longer say the shipped tree lacks them. No other assertion changed. Approved under the owner's unattended-run instruction of 2026-10-11. Resume point: STOP-T, independent Test/Challenge.
- 2026-10-11, Test/Challenge (`test-challenge.md`, findings 1–7), rulings relayed by the orchestrator, all applied (`review.md`).
  - Consistency: C5 narrowed. `replace` stays a flag, so the grammar keeps the base's acceptance, but its JSON/XML shape is EVIDENCE_BLOCKED on P8. The delta says so; the cases are `[replace-P8]` and `test_replace_is_clean_p8`. Specification challenge S1 is pending the owner.
  - New criteria, each pinned by a test, follow.
    - every capture's set, curly and XML door reads the device JSON's universal statements (`TestEveryDoorReadsTheDevicesUniversalStatements`: 5 of 18 fail on the base, 0 at the head);
    - a poisoned floor leaves both catalogue rows converting;
    - 0.17.0's scalar `"apply-flags": "omit"` is reported (field validation reports a value on a non-presence, non-list container) and written back;
    - a bare `apply-flags` is reported (a universal statement with no content);
    - the consumer's kept key is written back and reported;
    - a node's own child wins in every reader;
    - the name scan reads a prefix of a name and an f-string's literal part;
    - the JSON door's nested scalar is a strict xfail naming change 13.
  - Ledgered, untested by ruling: `set apply-flags omit replace` (no evidence either way; the head grammar rejects it).
  - Golden `tests/data/name-keyed.lark` regenerated from the generator (the `apply-flags` rule only), its docstring updated.
  - Invalidated: `test_another_word_is_kept_whole_and_reported` now asserts the general container rule (the unknown word is kept from itself, inside `apply-flags`) where it asserted the record at the parent.
  - No assertion weakened. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, phase 5, measurements at the head, taken on the tree before the phase-5 commit.
  - Artifacts regenerated with `junoscfg schema generate` from `25.2R2-S1.5_qfx5120.xsd`; a second regeneration is byte-identical (tree, grammar, both JSON schemas).
  - Diff against the base: the structure tree changes only `apply-flags` (`{l,u}` to `{u, c: {omit: p, replace: p}}`). The grammar changes only the `universal_statement` `apply-flags` alternative and the new `apply_flags` rule. The JSON schema changes the top-level `apply-flags` property to an object with `omit`/`replace` (nested ones keep the `patternProperties` entry).
  - Device outputs (`outputs.py`, 236 conversions, `diff-device.txt`): 18 differ, every one explained.
    - 12 are set/curly sources of `GR-OMIT`. `apply-flags omit` is placed: set and curly output move it before `location`, in the device's own order. JSON and YAML change to `{"omit": [null]}`. The one `UNPLACED` warning per conversion goes (12 warnings removed, none added).
    - 6 are XML-to-JSON/YAML. A nested `apply-groups[-except]` with one group becomes a list, as the device JSON writes it.
  - Curly writer (`tc_probe_via_structured.py`, capture → curly → set against capture → set): the same 96 lines at the head as on the base, byte-identical output.
  - `tc_probe_doors.py`: 28 differences on the base, 0 at the head.
  - JVD corpus (`outputs.py --jvd`: every `.conf` of the clone to set, curly and JSON, with diagnostics; `base-jvd.json` from a worktree of `dd7c8c4`, `head-jvd.json`, `diff-jvd.txt`). Of 4,605 conversions, 11 differ; set and JSON output and every diagnostic are identical, as are the 108 refusals of broken or documentation files. The 11 are curly output of files whose nested `apply-groups` holds two groups (14 such statements): the head writes `apply-groups [ A B ];`, the leaf-list spelling the device writes and these JVD sources write themselves, where the base wrote one line per group. A container holding nothing else is merged onto one line (`interfaces apply-groups [ "$GROUP_A" "$GROUP_B" ];`), as for any container. Meaning is unchanged: for these 11 files, curly → set against direct set differs in the same 51 lines on the base and at the head (pre-existing curly-writer defects; `rt-base.json`, `rt-head.json`). C4 holds: every difference is explained, and no set or JSON output and no diagnostic moved beyond the apply-flags fix.
  - Timing (`timing.py`, median of 3 on one machine). Inputs: the largest JVD file (296,365 lines, curly to set and to JSON) and a synthetic 40,000-line set list (20,000 prefix-list entries and 20,000 interface units carrying `apply-groups`, set to set and to curly).
    - First head: 5.38/5.73/1.93/2.17 s, against base 4.94/5.27/1.44/1.67 s. Cause: `universal_statements` passed over the root's children for every token a node's children miss, which in the set reader means every value and entry name.
    - Fix: the answer is kept per structure tree (by identity, with the root's child count as a guard, cleared by `forget_loaded_artifacts`; a `SchemaNode` tree under construction is not cached).
    - Head after the fix: 5.01/5.35/1.52/1.75 s, within 2–6 % of the base.
  - The tiers pass.
    - Schema tier (`pytest --schema tests/corpus/test_schema_data.py`): 34 passed, 2 skipped (no pinned count for 21.4R0); the one warning is the pre-existing DEV-V5 `FutureWarning`.
    - JVD tier (`pytest --jvd tests/corpus/test_jvd_corpus.py`, the field-warning budget included): 8 passed.
    - Unit, contract, tooling and corpus (device law included): 6,989 passed, 45 skipped, 22 xfailed (one new strict xfail, the ARCH-C10 carry-forward).
    - `known-differences.json` unchanged: the device law passes with no record change.
- 2026-10-11, phase 5 complete. Full check at 0683f96: every check passed except `fields`, which named three bullets of this file that read as unanswered `label:` lines. They were reworded at c47147a (document only), and `check --set fast` then passed. Application tests in the full check: 6,989 passed, 45 skipped, 22 xfailed; the one warning is the pre-existing DEV-V5 `FutureWarning`. `griffe` reports the display API changes (the four helpers' `key` parameter, the five exported tables, `UNIVERSAL_STATEMENTS`'s value), which are not on a named surface. Resume point: STOP-R, a fresh Reviewer on the head against the merge base dd7c8c4.
