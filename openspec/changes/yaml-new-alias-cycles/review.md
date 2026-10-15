## Findings

Independent Test/Challenge (fresh agent, no Builder reasoning, high risk floor) on tests
commit `66041f444938be3e164a879ca28322b154a898f2` against base `87e14cd`. It built a reference
implementation of design.md with mutants (`private_test_data/makeover-work/yaml-new-alias-cycles/tc/refimpl.py`)
and attack probes in the same folder. Verdict: changes required. Resolutions, all in the
tests and records commit after this one:

1. TC1 binding (test defect): the 2^200 reader row's path regex could not hold. Fixed: exact
   pins everywhere (`lol1.2`, `acme1.2`, the writer's `...lol.0x12.1`, `acme2.0` and
   `s1.0x300` for the depth bound) in kernel, reader, writer, validator, CLI and audit rows.
2. TC2 binding (test defect): the `yaml-migration` CLI row was unsatisfiable: the legacy
   reader writes every place out, so no CLI path hands the yaml-new writer a shared IR.
   Fixed: row dropped; the writer rows say the writer bound protects library callers.
3. TC3 binding (trust boundary): an alias chain (17 KB, inside the 2x size bound) nests the
   written-out document 1,200 deep; the designed recursive walk, the copy and the dumper
   raise `RecursionError` where the base refused cleanly. Fixed by a second bound (SC-A):
   an alias may not nest the document deeper than its parsed depth; the counting pass is
   iterative. Rows: kernel, reader, validator, CLI convert (exit 2) and `-v` (exit 1).
4. TC4 binding: counting mutants survived (2P+1; containers only; scalars deduplicated by
   id). Fixed: `test_one_value_past_twice_is_refused`, `test_scalars_count_toward_the_bound`,
   `test_an_alias_free_document_of_repeated_scalars_passes`.
5. TC5 binding: partial unsharing was not caught although anonymizing and `yaml` output
   differ on a shared IR. Fixed: `test_a_shared_block_converts_as_written_out` (every writer,
   plain and anonymized, shared `contents` and shared `prefix-list-item`) and
   `test_the_ir_of_a_shared_block_shares_nothing` (no container twice anywhere).
6. TC6 (pre-existing): scalar aliases and chained merge keys amplify inside PyYAML before
   the check (18 KB to 20 MB of output; 70 KB to 2,001,000 merged pairs). Not introduced
   here. Records corrected: the bound is linear in the loaded object, not the text; SC-B.
7. TC7: nested anchors each aliased once can be refused (`contents` reached three times).
   Records state the count is per written-out value; row
   `test_a_block_reached_three_times_through_nested_anchors_is_refused` pins it; SC-C.
8. TC8 records: (a) merge keys with a container value were refused at base and are now
   expanded (row `a-merge-key`; proposal corrected); (b) `from_dict(ir, "yaml-new")` of a
   caller's IR sharing a block past the bound is now refused where the base wrote it
   (secondary door, not a named surface; `.openspec.yaml` says so); (c) "outermost alias"
   and (d) "never the offending value or key" in the spec; (e) noted in design.md.
9. TC9: no pytest-timeout. Fixed: `tests/support/aliases.within` (POSIX timer) guards every
   bomb row, so an unbounded mutant fails instead of hanging; writer rows 2^16, 2^64, 2^200;
   the cycle row carries `host-name: acme-r1` and asserts it is not quoted.
10. TC10: doors without alias rows. Fixed: `audit -i yaml-new`, `validate_config`, CLI
    convert of a shared block and of a cycle.

Builder consequences found while implementing, recorded under the challenges they follow:

11. The depth bound refuses the approved writer test's IR
    (`test_a_shared_object_is_written_out_each_time`: an object shared at depth 1 and 2 in a
    selection nowhere deeper). Its assertion (no anchor; equal to JSON output) is kept; its
    IR now shares at one depth. A caller's IR on the secondary door `from_dict` sharing an
    object deeper than anything written is refused (SC-A; `.openspec.yaml`).
12. Two of the Builder's own kernel rows contradicted the design: `{"a": S, "b": [S]}` is the
    depth edge (now pinned by `test_a_block_aliased_deeper_than_anything_written_is_refused`,
    the passing row gains a deeper sibling), and the 2^64 writer path has 59 list steps, not
    60 (the 2^16 path, 12, matches the Test/Challenge reference).
13. Mutating the object stage's `unshared` back to `deepcopy` survived every test, although
    at base the JSON writer coerced a shared login user's `class` in an unknown context too
    (executed). Fixed: `test_a_shared_object_is_spelled_in_each_of_its_contexts` (json and
    yaml-new); it fails at base and under that mutation.

Fresh isolated Reviewer (separate agent, Opus, no Builder reasoning) on records head
`1d9db9e`, code head `4d30eec`, base `87e14cd`; probes under
`private_test_data/makeover-work/yaml-new-alias-cycles/review/`. Verdict: **Changes
required**, one binding finding. It found the ruling implemented at every door, no
denial-of-service against base (bombs and chains refused in about 0.2 s at each door;
recursion thresholds for deep alias-free text identical at base and head), nothing leaked by
anonymized runs, the non-break call sound, and both backlog entries reproducible.
Resolutions in the follow-up commit:

14. R1 binding: the size budget could run out on a value met for the first time after the
    copies, so the refusal named a non-alias (`configuration.system`, or a host's `name`
    scalar; 16 of 20,000 random shared documents). Fixed as proposed: only visits inside a
    copy spend a budget of the parsed size (the same accept set: the rest of the walk visits
    exactly that many) and meet the depth ceiling. Row
    `test_the_refusal_names_an_alias_when_the_copies_end_early` (`configuration.f`, eleven
    hosts at `...host.7.contents`) fails on the old walk; every earlier pinned path is
    unchanged.
15. R2: SC-C's counterexample was refused by the depth bound, not the count. Fixed: the test
    pins a size refusal of one-alias-per-anchor (`configuration.j`) and `NESTED_ONCE` with its
    depth reason; SC-C restated; design.md Risks corrected.
16. R3: ARCHITECTURE.md said "twice the parsed size or depth" and the kernel docstring left
    out the depth bound. Fixed in both.
17. R4: the changelog said the change only loosens; on `from_dict` with yaml-new it refuses
    a caller's IR past the bounds. Fixed in the fragment; added to SC-A (an in-memory IR has
    no text, so "deeper than written" is arbitrary there).
18. R5: SC-2 and SC-A understated user impact. Fixed with the Reviewer's concrete examples.
19. R6: the device figure does not cover yaml-new. Fixed: its scope stated here and in
    tasks.md 2.3.

Correction review on `e0b5e20` (same Reviewer, read-only; code `b30dcd2`): R1 to R6
resolved. R1 re-measured over 20,000 random shared documents: no size refusal names a
non-alias (16 before); verdicts and paths equal the proposed variant, and the accept set is
unchanged against `4d30eec`. Verdict: **Merge**. Its two cosmetic notes: the changelog
fragment's long line is rewrapped (records only); the test helper's placement between two
constants is accepted as is, since moving it would only reorder test code.

## Evidence

- Follow-up canonical full checkpoint at `b30dcd2` (after R1 to R6): every check passed,
  167 s; 13,382 passed, 22 xfailed, 37 skipped; coverage 93.15 %; schema-25.2 tiers exit 0.

- Canonical full checkpoint at `8fecbdd` (code head `4d30eec`): every check passed, 349 s;
  13,380 passed, 22 xfailed, 37 skipped; coverage 93.15 %; schema-25.2 tiers exit 0.
- Device corpus base `87e14cd` vs head: 0 of 96 conversions differ. The tool writes set,
  structured, json and yaml, so this covers the JSON object stage's copy, not yaml-new; the
  Reviewer's probe adds yaml-new over 24 renderings (no shared container in the reader's IR,
  output equal to JSON output).
- Door probe (doors-base.txt, doors-head.txt): shared block now read at every yaml-new door;
  cycle refused as `cycle`; bombs refused at `l1.2` in about 1 ms; legacy `yaml` unchanged.
- Mutations (no size bound, 2P+1, no depth bound, global seen-set, containers only,
  innermost path, reader sharing, object-stage deepcopy): each fails the focused tests.

## Specification challenges

### SC-2 The size bound (interim, set by the Builder under the owner's instruction)

- Artifact: specs/conversion/junos-json-yaml, "A block shared through an alias is written
  out, a cycle and an alias bomb are refused"; design.md decision 2; decision record.
- Counterexample: the owner's ruling names no limit, but pure expansion is exponential
  (billion laughs, 10^9 values from 9 lines; executed).
- User impact: without a bound any yaml-new door can be made to hang; with it, a small file
  reusing one block many times is refused (`a: &x {k: v}` with three more aliases; four
  syslog hosts sharing one two-entry `contents`, Reviewer probe p3_idiom.py).
- Proposed correction: written out, at most twice the parsed values. Grounded in the
  property the earlier rule had (linear in the loaded document) and in the ruling's
  "reached twice". Alternatives for the owner: a larger factor, or a fixed allowance added
  to it (go-yaml style); either is additive.
- Decision: Pending owner decision. Interim action: the factor two is implemented.

### SC-A The depth bound (raised by Test/Challenge TC3)

- Artifact: the same requirement; design.md decisions 2 and 5.
- Counterexample (executed): `alias_chain_yaml()`, 17 KB, inside the size bound, nests 1,200
  deep written out; a recursive walk, copy or dump raises `RecursionError` (exit 1 with a
  traceback) where the base refused it (exit 2).
- User impact: an untrusted file crashes every yaml-new door instead of being refused.
- Proposed correction: an alias may not nest the written-out document deeper than the parsed
  document's deepest value (aliases as leaves): no number, and no stage meets a depth an
  alias-free document of the same text could not have. It also refuses a block defined
  shallow (a sibling of `configuration`, say) and aliased deeper than anything else in the
  file: the common YAML idiom of anchors in a top-level block (`x-contents: &c [...]`, then
  `contents: *c` under `configuration`) is refused, while the same text converts with
  `-i yaml`, and an unrelated deeper sibling makes it pass (Reviewer probes p3, p8). For a
  caller's in-memory IR on `from_dict` there is no text, so "deeper than written" is
  arbitrary there (an object shared one level deeper is refused). Alternatives for the
  owner: a fixed ceiling (such as 64 levels, beyond any Junos hierarchy) or a depth
  allowance added to the parsed depth, with the walk kept within it.
- Decision: Pending owner decision. Interim action: the parsed-depth rule is implemented.

### SC-B Amplification inside PyYAML (pre-existing)

- Artifact: decision record and design.md, "linear".
- Counterexample (executed by Test/Challenge): one 18 KB string aliased many times writes
  20 MB (x1,109), 5.6 s; a 70 KB merge-key chain loads 2,001,000 pairs. Base and head alike.
- User impact: an untrusted yaml-new file can still cost quadratic time and memory.
- Proposed correction: the claim now says linear in the loaded object; a stronger rule counts
  `yaml.compose` nodes, weighting strings by length, which changes what a value is.
- Decision: Pending owner decision. Interim action: none beyond the corrected claim.

### SC-C What "reached twice" means

- Artifact: the requirement's "every document that reaches each value at most twice" against
  the ruling's "a mapping or list reached twice through an alias is expanded".
- Counterexample (executed): `configuration: {h: &h {name: a, contents: &c [x, y, z]}, i: *h,
  j: *c}`, each anchor aliased once, `contents` reached three times written out: refused by
  the size count at `configuration.j` (`NESTED_ONCE` is refused by the depth bound, SC-A).
- User impact: nested sharing in a small file can be refused.
- Proposed correction: the count is per written-out value (stated in spec and decision
  record); the owner may prefer a per-alias reading, which needs a different bound.
- Decision: Pending owner decision. Interim action: per written-out value, pinned by a test.

## Pending owner decisions

- SC-2, SC-A, SC-B, SC-C above.
- C5 (instruction-integrity): legacy `yaml` input recurses on a cycle (`_strip_meta_keys`)
  and expands an alias bomb through every writer. Recommended default: a backlog entry, and
  the same kernel check on the `yaml` reader in a follow-up change.
- C8 (device question, open, not acted on).
