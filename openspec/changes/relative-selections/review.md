## Findings

Independent Test/Challenge (fresh agent, Opus, no Builder reasoning, high risk floor) on tests
commit `1370b2c` against base `d3ed627`; reference implementation and 19 mutants under
`private_test_data/makeover-work/relative-selections/tc/`. Every new test failed at base for
the right reason; 9 mutants survived. Verdict: changes required. Resolutions, all in the
tests and records commit after this one (64 tests fail at base, all pass on the
implementation):

1. TC1 binding: coercion pinned for a mapping only. Fixed: `test_a_relative_selection_keeps_its_schema_context` over a mapping, a list and a leaf (`host-name: [r1]`), json and yaml-new.
2. TC2 binding: the `groups` wrapper unpinned. Fixed: `test_a_selected_groups_is_the_list_of_groups` (json, yaml-new) and `groups.group` rows of `test_a_list_name_the_schema_hides_is_not_written` (set, structured), literal outputs.
3. TC3 binding: the corpus law too weak. Fixed: every relative set line must be its absolute line less the path's words (each key consumed when it is the next word); relative structured, put back under those words, must read as the absolute text.
4. TC4 binding: dotted keys pinned only as the last step. Fixed: mid-path row `routing-options.dynamic-tunnels.forwarding-rib.inet.0.inet-import`.
5. TC5 binding: purity under `below=` unpinned. Fixed: `TestNoWriterChangesTheIrItIsGiven::test_a_selection_below_its_path_is_left_unchanged` (five writers, four selections).
6. TC6 binding: `from_dict(wrap=False)` output unpinned. Fixed: `test_a_bare_value_keeps_its_meaning`.
7. TC7 binding: anonymized data could not tell old from new. Fixed: coercion and annotation rows, and `test_an_anonymized_list_selection_in_set`.
8. TC8 binding: the `junoscfg:unplaced` key writes no word. Fixed: spec names it; `test_the_kept_statements_key_writes_its_statements` pins base output.
9. TC9 advisory: masked red results. Fixed: the tests are split or parametrized per defect.
10. TC10 advisory: hidden list names only in the corpus. Fixed: unit rows `interfaces`, `interfaces.interface`, `routing-options.dynamic-tunnels.dynamic-tunnel`, `groups.group`.
11. TC11 advisory: law depth 3, missing-key paths through lists or leaves. Fixed: depth 4 (the depth-5 probe is recorded as evidence), `test_a_path_through_a_list_or_a_leaf_selects_nothing`.

Fresh isolated Reviewer (separate agent, Opus, no Builder reasoning) on records head `caebec4`,
code head `ab46c51`, base `d3ed627`; probes under
`private_test_data/makeover-work/relative-selections/review/`. Verdict: **Changes required**,
two binding findings. It found the rule correct at every writer, absolute output
byte-identical (0 of 96; 2,955 absolute outputs differing only in the 10 dotted selections
that were empty), `from_dict(wrap=False)` identical at base and head, the widening to set and
structured justified, and the not-a-break call sound but for R1. Resolutions in the follow-up
commits (tests first, `test: pin relative yaml-new depth, ...`):

12. R1 binding: relative yaml-new counted the 64-level ceiling on the absolute document, so
    a selection base wrote was refused. Fixed: the writer measures a relative selection from
    its own root, as written; `test_a_relative_yaml_new_selection_is_measured_as_written`
    (fails on `ab46c51`).
13. R2 binding: `Below`'s delete, activate and replace paths were unpinned (a raw delete
    line with the wrong path survived). Fixed: `test_every_tag_below_a_selection_is_written_below_it`
    (set and structured, all five tags); mutants delete-raw, activate-raw, replace-raw,
    protect-raw and deactivate-raw each fail it.
14. R3 advisory: the depth-5 probe restarted the depth at every level (1,640). Fixed: only the
    entry call goes to depth 5: 575 selections, 0 problems (law5-head.txt); the mutation count
    is now 16 of 16 (mutations.txt).
15. R4 advisory: `removes` and two docstrings described the old mechanism. Fixed: `removes`
    names the pipeline's use of the bare spelling; `junos_json_object` and `pipeline_result`
    docstrings updated.
16. R5 advisory: anonymized rows held preserved addresses. Fixed: 203.0.114.x in every row, and
    the test asserts no such address survives.
17. R6 advisory: display's `filter_*_by_path` text filters keep schema-less matching (a declared
    non-goal). Fixed in the records: display contract and conversion guide say so; moving the
    resolver into display stays an owner choice (reported).
18. R7 advisory: `path_words` branches with no visible effect. Fixed: the annotation and
    kept-statements exemptions are removed (`Below` passes over a word no statement names;
    the spec says so); the transparent-list-key branch is pinned by an entry named
    `dynamic-tunnel` (`test_an_entry_named_like_a_hidden_list_keeps_its_name`).

The Reviewer's out-of-scope note (absolute `--path system.host-name` drops the leaf's
`@host-name` tag, base and head alike) is reported as a pending owner decision.

## Evidence

- Follow-up canonical full checkpoint at `f677934` (after R1 to R7): every check passed, 166 s;
  13,496 passed, 22 xfailed, 37 skipped; coverage 93.17 %; schema-25.2 tiers exit 0. Absolute
  output rerun: 0 of 96, 0 of 2,435.
- Canonical full checkpoint at `ab46c51`: every check passed, 350 s; 13,492 passed, 22 xfailed,
  37 skipped; coverage 93.11 %; schema-25.2 tiers exit 0.
- Absolute output unchanged: device corpus 0 of 96, catalogue 0 of 2,435 (base: the
  yaml-depth-ceiling head records, same runtime as `d3ed627`).
- Corpus law at depth 5: every capture passes (law5-head.txt). Sixteen mutations each fail the
  tests (mutations.txt).

## Specification challenges

- SC1 Artifact: `.openspec.yaml` "every new output loads, put back under its path, as the absolute output does". Counterexample: a flag, a null or `system.@` writes nothing relative in structured. Proposed correction: narrow the claim, state annotation selections. Decision: adopted; the tag on the selected statement itself is a bare command in set and a noted drop in structured (base wrote `inactive;`), pinned by `test_an_annotation_selection_in_set_and_structured`.
- SC2 Artifact: the word rule. Counterexample: TC8. Decision: adopted.
- SC3 Artifact: the delta's "`groups` holding its entries" for `yaml`. Counterexample: yaml holds `groups: {group: [...]}`. Decision: adopted; yaml writes the IR's value.
- SC4 Artifact: the dotted rule. Counterexample (theoretical, none in the schema): a dotted key beside a shorter key. Decision: stated as "the shortest join with which the rest of the path resolves"; the resolver stays in `convert`, the display filters are untouched; pinned by `test_the_exact_key_wins_over_a_dotted_one`.
- SC5 Artifact: the not-a-break call. Assessment: sound; the structured leaf and the `groups` list changes are now named in `why`. Decision: adopted.

## Pending owner decisions

- Absolute `--path` to a leaf drops the leaf's own tag (`deactivate system host-name`),
  pre-existing, found by the Reviewer; recommended default: a follow-up fix rebuilding the
  `@leaf` sibling along the path.
- Whether display's text filters (`filter_*_by_path`) should share conversion's path rule
  and dotted-key resolver; recommended default: leave them (they serve text), as recorded.

- The break call (patch) for the changed relative outputs; recorded default patch.
- C8 of relative-null-flags (device question), not acted on.
