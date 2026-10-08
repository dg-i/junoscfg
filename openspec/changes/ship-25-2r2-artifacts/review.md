# Review

Fresh agent session, read-only, against commit `6445bb8` before it was
amended and tagged `v0.8.0`. The reviewer rebuilt the artifacts from the same
dump and re-measured the three devices against both sets on its own.

## Confirmed exact

Four of five artifacts byte-identical to an independent rebuild. Three real
devices: old code with old artifacts 21 rejected, committed code with new
artifacts 1, the one being `chassis dump-on-panic`; committed code with the
old artifacts 167, which is the bridge's own weight. Across 20 `apply-*`
forms exactly three old-accept, new-reject losses, all under the two clauses
the declared break names. The four new tests claim what the grammar does.
Contracts respected: corrections went through the generator, nothing lazy
became eager.

## Findings

1. **`docs/guide/validation.md` said 106 of 116 corpus lines accepted.** It
   is 102 after the four the bridge hid. **Applied.**
2. **A comment in `schema_generator.py` said the shipped tree carries no
   `apply-*` node.** It does now. **Applied**: past tense.
3. **`junos-schema-meta.json.gz` never reproduces**: `generated_at` is wall
   clock, so a regenerate-and-diff check must exclude that key. **Accepted**
   as-is and recorded; the `schema info` example in `docs/guide/cli.md`
   showed a 2026-02 timestamp beside the new version, **applied**.
4. **Four comments still called 24.4R0 "the bundled" set**, in
   `grammar_generator.py`, `artifact_builder.py`, `test_grammar_generator.py`
   and `schema_data.py`; the `artifact_builder` one also described a
   rebuild-drift caveat that no longer holds on 25.2R2. **Applied**.
5. **The deactivate path was unpinned** though the bridge ran on it. No
   regression measured. **Applied**: one test.
6. **`set protocols bgp group G apply-groups` with no value is accepted**:
   after a list entry name a bare token is taken as a value. The grammar's
   general looseness, finding 3 of the private assessment, not this change.
   **Accepted**, recorded here.
7. **Declared break accurate and complete**; wording widened to every
   `apply-*` bracket form and to a quoted trailing value. **Applied**.
8. **The proposal gave one denominator for both sets**; 6,998 set lines under
   the old artifacts, 7,002 under the new, since `hop-limit` stops fusing.
   **Applied**.
9. **Pre-existing, out of scope**: `SetValidator` rejects `delete` lines the
   converter may emit, and rejects `deactivate system host-name`, which
   junoscfg itself emits, on both artifact sets. **Recorded** as known
   defects for a later change.

## Already provided

Nothing the toolbox or the standard library covers was rewritten.

## Specification challenges

None.

## Verdict

The core claim holds and the bridge removal is safe; ship. Findings 1, 2, 4,
5, 7 and 8 applied in the amended commit; 3, 6 and 9 recorded.

## Owner acceptance

Pending. The findings and their resolutions are recorded above for the owner
to accept or reopen.
