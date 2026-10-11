<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): IDs ARCH-C05, NEW-R5, ANON-P1 (=NEW-C13), ANON-P2 (incl. NEW-C11), NEW-A-N1/N2/N3/N6, NEW-A-S2, the change-4 carry-forwards (`anonymize/walker.py` and `audit/walker.py` adopt `schema_child`; the stale docstring of `rules/group.py`; nested `apply-macro` values), and NEW-R8 found here (C9). Assurance `balanced`; fast-forward into local `master`, archive, tag, never push.
- C3 one change. C4 the walk decides at both doors; the pipeline's blanket refusal goes. C5 the record follows owner rule 5 too (specification challenge S1, interim action recorded). C6 the IP rule's type families, the name table retired. C7 lists under a container are walked, not remodelled. C8/C12 no original value in a warning or an `UNPLACED` message of an anonymized run. C10 a declared break on `consumer` and `cli`, minor 0.19.0. C11 pattern plus warning, not refusal. C13 secrets and names in unplaced content are left as written, as the warning says.

## Requirements

- `specs/anonymization/placed-values/spec.md`, a new capability: ADDED "The walker reaches every value the schema places", "The IP rule answers by the leaf's type", "A group reference goes to the group rule once", "Content the walk cannot place is named, its addresses replaced".
- `specs/anonymization/keyed-entries/spec.md`: MODIFIED "No value anonymized before escapes". Contradicted, quoted: "the anonymized output of `name`-keyed lists SHALL be byte-identical; phase 5 SHALL stop and report any value whose treatment moves otherwise". The owner's task allows the pin to change by added entries, each explained, never a dropped one; the requirement says so now.
- `specs/conversion/entry-keys/spec.md`: MODIFIED "A statement the reader cannot complete is kept whole". Contradicted, quoted: "`junoscfg.anonymize.anonymize()` SHALL refuse an IR whose record holds a statement (any other key its walk cannot place is NEW-R5, change 5), and the conversion's refusal SHALL withhold the statement's text"; scenario "strict conversion raises and anonymization refuses". C4, C5.
- `specs/validation/keyed-entries/spec.md`: MODIFIED "An entry without a key field is unplaced" (quoted: "so `--strict` and anonymization refuse it"); ADDED "Field validation walks a transparent container's other children" (NEW-A-S2).
- `specs/schema-pipeline/universal-statements/spec.md`: MODIFIED "One helper resolves a universal statement at every level": scenario "Not inside a universal statement" (quoted: "an anonymized run refuses without the address passing") and the name exception narrowed from "the anonymize and audit walkers" to the group rule and the audit walker.
- Unchanged and binding: `conversion/writers` (a writer leaves its IR unchanged), `conversion/diagnostics` (the caller renders diagnostics; library code writes nothing), `conversion/structured-input` (an anonymized run withholds an input path).

## Evidence

- Observed on `3a0607f`: synthetic reproductions in `private_test_data/makeover-work/anonymize-every-placed-value/repro.py`, output `repro-base.out`; the findings follow.
  - `anonymize()` returns an unknown leaf `203.0.114.9`, a 0.16.1 joined key `bogus 203.0.114.9 G-SECRET` and a scalar on a container verbatim with no word; it raises on a record. The pipeline refuses all of them from set, JSON and XML (`FieldValidationError`, "cannot anonymize").
  - Groups with sensitive words: root `apply-groups` names `group_0490…`, the group is `group_4889…` (ANON-P1).
  - `set system apply-macro M2 peer 203.0.114.8` keeps the address; `interface-range IR1 description "access range"` beside an interface keeps its description; `interface-range ... member-range` alone is refused (NEW-A-S2 through the pipeline's refusal).
  - Strict raises on `set interfaces interface-range R1 member-range xe-0/0/0 to xe-0/0/3` and `set interfaces traceoptions file f1`; JSON `bogus-key` beside `interface` and `bogus-trace` under `traceoptions` report nothing.
  - `tacplus-server` and its `source-address` (`hostname`), BGP `cluster` and `from area` (`areaid`), `ipv6-router-id` (`string`) keep their addresses; `syslog host` is replaced through the name table; `from interface ge-0/0/0.0` crashes with `ValueError` (NEW-R8).
- Device example (`examples/junoscfg-oracle.json` = `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz`, vMX 23.2R2-S7.5): `MISSED` holds `203.0.114.49`, `10.255.0.1` (tacplus, `hostname`), `10.0.0.1` (port-mirroring `routing-instance`, a one-entry JSON list under a container that is no list), `access range`, `access ports` (`interface-range`, a sibling of the transparent child). Base pin mapping: `pin-base.json` (SHA `b8c3da05…`, 9 rules, 92 entries).
- Type measurement: `parents.py` (the name table against the tree) and `untyped_ips.py`/`untyped_ips.out` (every device capture and 1,528 JVD files: address-shaped values on leaves of no address or host type sit only on `areaid`, `syslog host`, `ipv6-router-id` and the untyped `security ike gateway address`; no four-part OID).
- `rules/group.py` docstring (stale since 0.18.0: "only the grammar and JSON-schema generators read that flag"); `audit/walker.py` resolves children by `children.get` (change-4 carry-forward).

## Non-goals

As `proposal.md`: NEW-R1, NEW-R3, NEW-R4 (change 5b); ANON-P3 `<*>` (change 6, strict xfail kept); ANON-P5, NEW-A-N4/N5/N7 (change 7); ANON-P4 (change 8, strict xfail kept); OPEN-21 (change 11). Observed and left: `apply-groups "${node}"` (a chassis-cluster expansion) is replaced like any group name, as the retired second pass did.

## Acceptance criteria

- Every test id the delta names exists; the new and changed ones fail on the merge base `3a0607f` and pass after the change, except guards named in the delta log. `agent-ready reconcile` passes.
- The strict xfails `_APPLY_GROUPS_DEFECT` (3 nodes) and `test_what_a_rule_misses_today_is_replaced` (2) are gone because their causes are fixed; `MISSED` is gone. ANON-P3 and ANON-P4 xfails stay.
- Anonymization proofs: over every device capture and the examples, with every rule alone and all together (`private_test_data/makeover-work/anonymize-every-placed-value/combos.py`): no address of the capture survives unless the address anonymizer maps it to itself; syntax values (enum values, keywords, key choices) are unchanged; every `apply-groups` names a group the output defines; revert restores the canonical IR. A committed law, `tests/corpus/test_device_anonymization.py`, holds the every-rule case.
- The pin `test_name_keyed_output_is_unchanged` changes only by added entries, each listed and explained in this file; none dropped or altered (`pin-base.json` against the head's).
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

The walker now walks subtrees it skipped (transparent siblings, universal statements, lists under containers) and asks `schema_child` on a miss: one dict lookup. Timed per the developer guide on the largest capture and a synthetic list of tens of thousands of entries, base and head, recorded in the delta log; a record, never a gate.

## Outstanding decisions

None, because C1–C13 are resolved by precedence, the owner's answers and repository rules. Specification challenge S1 (the record's refusal) goes to the owner with its interim action, as intake answer 3 directs.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high (red zone `anonymize`, trust boundary, cross-domain, declared break on `consumer` and `cli`)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer at least as capable as the Builder; Finalizer duties run by the Builder under the owner's brief
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `ac025a9` and the delta. Approved under the owner's unattended-run instruction of 2026-10-11.
