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

## Evidence

Pending implementation.

## Specification challenges

- SC1 Artifact: `.openspec.yaml` "every new output loads, put back under its path, as the absolute output does". Counterexample: a flag, a null or `system.@` writes nothing relative in structured. Proposed correction: narrow the claim, state annotation selections. Decision: adopted; the tag on the selected statement itself is a bare command in set and a noted drop in structured (base wrote `inactive;`), pinned by `test_an_annotation_selection_in_set_and_structured`.
- SC2 Artifact: the word rule. Counterexample: TC8. Decision: adopted.
- SC3 Artifact: the delta's "`groups` holding its entries" for `yaml`. Counterexample: yaml holds `groups: {group: [...]}`. Decision: adopted; yaml writes the IR's value.
- SC4 Artifact: the dotted rule. Counterexample (theoretical, none in the schema): a dotted key beside a shorter key. Decision: stated as "the shortest join with which the rest of the path resolves"; the resolver stays in `convert`, the display filters are untouched; pinned by `test_the_exact_key_wins_over_a_dotted_one`.
- SC5 Artifact: the not-a-break call. Assessment: sound; the structured leaf and the `groups` list changes are now named in `why`. Decision: adopted.

## Pending owner decisions

- The break call (patch) for the changed relative outputs; recorded default patch.
- C8 of relative-null-flags (device question), not acted on.
