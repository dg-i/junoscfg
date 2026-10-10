<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner prompt `private_test_data/deactivate-fix-prompt.md`, change B, narrowed by the owner on 2026-10-10 ("go ahead with B narrowed") to what changes meaning; `ARCHITECTURE.md` §1: equivalent output, not the device's layout (C3).
- Stacked on change A; focused tests and the fast set while building; one full check per change head, Test/Challenge and one fresh Reviewer for A and B together at the end (owner answer 3).
- `SetConverter` and `ConfigStore` sit on the secondary `junoscfg.display` door (decision 2026-10-09-scope-compatibility-to-production-consumer); `to_set()` output is kept and its limit written into `display/CONTRACT.md`.

## Requirements

- `specs/conversion/meta-tags/spec.md` (ADDED to change A's capability): a curly tag marks the node its statement starts; structured output puts a tag first; a tag on an unkeyed `homogeneous` container is reported; XML keeps `protect`.
- `specs/conversion/raw-set-input/spec.md` (MODIFIED): the bracket requirement names any command instead of the internal `replace` form; behaviour and tests unchanged.
- Contradicted requirement: none. `conversion/entry-keys` "a statement the reader cannot complete is kept whole" stands: a tag on a kept-whole statement marks the kept key.

## Evidence

- Device: `deactivate.txt` (one-line inactive route with `apply-groups`; XML/JSON tag on the entry), `deactivate2.txt` (leaf), `deactivate3.txt` (`inactive: family inet {` = `<inet inactive>`), `deactivate4.txt` and `deactivate6.txt` (`deactivate`/`protect … family` rejected; `protect: route … next-hop …;` = `<route protect>`; keyed `homogeneous` container accepts tags, out of scope).
- Device re-export `private_test_data/anon/` and the scratchpad oracle: baseline set output differs from the device in 8–10 lines, two classes out of scope; curly layout differences load equivalently (`output.txt`).
- XSD 25.2R2 dump: unkeyed non-list `homogeneous` containers are `family` (145) and `tunnel encapsulation` (8); keyed ones and 1,716 lists are not in the rule.
- Owning code: `SetConverter._process`/`_transform_line`, `set_input._merge_tokens`/`set_to_dict`, `structured_input.structured_to_dict`, `ConfigStore.__str__`/`_prefixed`/`COMPOUND_KEYWORDS`, `DictWalker._process_hash`/`_emit_oneliner`, `StructuredWalkOutput`, `FieldValidator._walk`, `to_yaml._get_inactive_attrs`, `artifact_builder._BOOL_FLAG_KEYS`.

## Non-goals

As `proposal.md`.

## Acceptance criteria

- Every test id in the delta fails before the change and passes after it; the existing suite stays green.
- Oracle: set output against the device re-export loses the defect-1 lines (`deactivate … apply-groups …` becomes `deactivate … route …`) and gains no new difference; structured output reread gives the IR it was written from.
- High risk floor: independent Test/Challenge and a fresh Reviewer at least as capable as the Builder, at the end with A's.

## Performance expectations

None measurable: the curly reader drops one text round trip (curly → set text → tokens) for one structured pass over the same statements; `--regen-schema` adds one flag key per `homogeneous` node to the structure tree.

## Outstanding decisions

None blocking. `tunnel encapsulation` is the rule's one member without device evidence (`private_test_data/deactivate7.in`, first block); it is a merge condition: if the device accepts a tag there, the rule narrows to what the device refuses.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high (cross-domain: schema-pipeline, conversion, validation, kernel; regenerated artifacts)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer; Finalizer
- Resume point: phase 5 pre-review full checkpoint, run with change A's at the end (owner answer 3); last valid evidence: whole suite 1,959 passed / 45 skipped / 1 xfailed and `agent-ready check --set fast` green at ea224cd

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established on `change/meta-tag-placement` after 515b180.
- 2026-10-10, phase 5: one `--regen-schema`. The structure tree gains `h`; the set grammar is identical once its variant-name hashes are masked (9,779 lines either way, no difference): `grammar_generator` hashes each node's sorted flags into variant names, and `homogeneous` is now among them, so set validation is unchanged. Three `tests/test_config_store.py` tests pushed a path named `family` and expected merging from the name; they now call `mark_merged`, the declared replacement for `COMPOUND_KEYWORDS`, with their assertions unchanged, and three tests are added beside them. My own `TestHomogeneousFlag` test indexed the tree under `configuration`, whose root it is; the path is corrected, the assertion unchanged. Device oracle (`private_test_data/anon/`): structured input now gives the IR set input gives (562 differing lines against device JSON for both, down from 588), set output from structured input equals set output from set input, no new difference in any direction; structured output read back keeps the IR for set and structured sources. JSON and XML sources do not round-trip through structured output on master either: JSON input keeps numbers, XML input keeps 230 single leaf-list values scalar (follow-ups). No acceptance criterion changed.
