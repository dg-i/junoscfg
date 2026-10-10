## Specification challenges

Raised by the independent Test/Challenge role (`test-challenge.md`, 2026-10-10,
fresh context-isolated agent, worktree at 0c9e24d). Interim actions are the
Builder's safe, reversible steps under the frozen rule (a tag marks the node its
statement starts) and the one-IR rule; the owner decides each.

### S1 — Where an entry starts when its list keyword opens a block

- **Artifact**: requirement "A tag on a curly statement marks the node the statement starts"; `set_input._merge_tokens`, list path.
- **Counterexample**: executed: `source-prefix-list { inactive: PL1; PL2; }` raised "a tag inside a key or value" (CLI exit 2; change A's head exits 0). Tagging every level of the device re-export one at a time raised on 122 of them.
- **User impact**: valid device-layout curly refused once one such entry is tagged.
- **Proposed correction**: the level that starts at an entry's key marks the entry.
- **Decision**: Pending owner decision. Interim action taken: every level start is recorded; a tag on an entry's own line marks the entry, and a tag on a list keyword alone on its line marks the whole list (`deactivate … source-prefix-list`, as `inactive: routing-instance {` is `deactivate … routing-instance` in `deactivate6.txt`). The probe now raises on 0 of 3,422 statements. Scenario "Entry inside its list's block" and `test_a_tag_on_a_bare_list_keyword_marks_the_list` added; the challenger's four shapes pass.

### S2 — Round trip of a tagged leaf-list

- **Artifact**: requirement "Structured output puts a tag at the head of its node's line".
- **Counterexample**: executed: two-value `members`, static `next-hop`, `vlan members` with a tag → `members [ … ];` without it (pre-existing on master; reachable from change A's XML IR).
- **User impact**: curly output re-activates a deactivated leaf-list on load, silently.
- **Proposed correction**: the writer keeps the tag (`inactive: members [ … ];`, `deactivate6.txt`).
- **Decision**: Pending owner decision. Interim action taken: `DictWalker` emits the leaf-list's tag after its bracket line; requirement text and test ids extended.

### S3 — A tag on a `family` block widened to every family inside

- **Artifact**: "the child that follows it in the same statement" and "reported from any input".
- **Counterexample**: executed: `inactive: family { inet {…} inet6; }` tagged both families, no diagnostic.
- **User impact**: more deactivated than written, silently; other inputs report it.
- **Proposed correction**: pass the tag only within one level.
- **Decision**: Pending owner decision. Interim action taken: as proposed; a lone `family` level keeps the tag and field validation reports it; structured input added to the "every input" test.

### S4 — Widening onto a node the statement does not start

- **Artifact**: `_tags_from` in the `apply-macro` and `apply-groups` paths; the leaf rule.
- **Counterexample**: executed: `apply-macro M1 { k1 v1; inactive: k2 v2; }` tagged `M1`; `members 64496:1; inactive: members 64496:2;` tagged both values.
- **User impact**: active configuration deactivated silently; XML refuses the leaf-list shape.
- **Proposed correction**: keep whole and report, or refuse as XML does.
- **Decision**: Pending owner decision. Interim action taken: a tagged `apply-macro` data line is kept whole and reported (UNPLACED), as in change A; uneven tags across one leaf's values in curly input raise `ValueError`, as XML input does. No device artefact for `apply-macro` data tags yet (`deactivate system apply-macro M1 k2`).

### Low findings

- JSON `"@family"` beside `family` was reported UNPLACED but dropped from set output; set output now repeats it (`test_set_output_repeats_a_sibling_family_tag_from_json`).
- `test_a_tagged_child_is_not_joined` asserted the `then {` layout; it now asserts the IR, keeping the "no tag mid-line" check.
- A rebase onto change A's fixes left one call to the renamed `_get_inactive_attrs` in `display/to_yaml.py`; corrected before any run.

## Phase-6 review (fresh session, 2026-10-10)

Fresh context-isolated Reviewer, worktree at 7eebb2c (base 458e9b3, change A's head). Read the change folder, `ARCHITECTURE.md` §1 and §8, `AGENTS.md`, `display/` and `convert/` `CONTRACT.md`, decision 2026-10-09, the tests and the diff. Device captures and `private_test_data/anon/` were read in memory, counts only, no value copied. Probes use test-data values only. No product code, spec or test edited: one temporary checkout of A's `src/` for a mutation run was restored, and the tree is clean.

### Verdict

**Mergeable after fixes.** The curly reader now places tags as the device does on its own configuration:

- All 16,541 block-opener taggings of the re-export agree with set `deactivate <path>`.
- None of 19,997 level taggings raises.
- The grammar is unchanged up to variant renaming.
- The oracle figures hold.

Two regressions against change A should be fixed first (F2, F3). F1 sits inside this change's own round-trip requirement, and the owner decides it.

### Findings

1. **High, pre-existing but inside this requirement: a tag on a whole list is written on its first entry only.**
   Requirement: "Structured output puts a tag at the head of its node's line … reading the output back gives the same IR". The interim scenario "Entry inside its list's block" (`inactive: source-prefix-list {` tags the whole list) makes `@<list>` a shape of this capability.
   Artifact: `ConfigStore._set`/`_inverse_match` matches `… name-server` to the first `name-server <key>` line.
   Evidence: `printf 'set system name-server 192.168.0.1\nset system name-server 192.168.0.2\ndeactivate system name-server\n' | uv run --locked junoscfg convert -i set -e structured` gives `inactive: name-server 192.168.0.1;` and an untagged `name-server 192.168.0.2;`. Read back, the list is active and one entry is inactive. The same happens to `routing-options static route`, `interfaces … unit`, and `source-prefix-list` read from B's own curly (`inactive: source-prefix-list { PL1; PL2; }` → `inactive: source-prefix-list PL1;`). Set output keeps it.
   Proposed correction: write a tagged list as `inactive: <keyword> { <entries> }`, and add the shape to `SHAPES` in `test_round_trips_keep_the_ir`. Ask for the device artefact first (lab, `rollback` after): `deactivate system name-server`, then `show system name-server`, `| display xml`, `| display json`. If the device rejects it, refuse the shape on every input instead.
2. **Medium, regression against A: any non-empty `@` on `family` counts as a tag.**
   Artifact: `convert/field_validator.py` hunk `+if passes_tag_to_child(child_schema) and (value.get("@") or obj.get(f"@{key}"))`. Device JSON carries `junos:` attributes in `@`; the oracle strips them, and `display inheritance` writes `junos:group`.
   Evidence: `printf '{"configuration":{"interfaces":{"interface":[{"name":"xe-0/0/0","unit":[{"name":"0","family":{"@":{"junos:group":"G1"},"inet":{}}}]}]}}}' | uv run --locked junoscfg convert -i json -e set --strict` fails with "a tag on 'family' … could not be placed", exit 1. A exits 0. `convert_config(..., strict=True)` raises `FieldValidationError`, and the non-strict path warns falsely.
   Proposed correction: ask the question `DictWalker._read_attrs` already answers (inactive, protect, operation, active), and add the `junos:group` case as a negative test.
3. **Medium, regression against A: a per-value tag on `apply-groups` in curly is widened.**
   Requirement: "A tag that would mark only some values of a leaf … is not widened". Artifact: `set_input._merge_tokens` apply-groups branch, `+_mark(current, here, token)`, which has no evenness check, unlike the leaf branch.
   Evidence: `printf 'system {\n    apply-groups G1;\n    inactive: apply-groups G2;\n}\n' | uv run --locked junoscfg convert -i structured -e set` gives `deactivate system apply-groups`, which deactivates G1 as well, silently. A kept it whole and reported it UNPLACED. This is not device layout (the device writes `apply-groups [ … ];`).
   Proposed correction: apply the leaf branch's uneven-tag `ValueError` to `apply-groups` and `apply-groups-except`, and add a test.
4. **Medium: the `family`-only scope of the refusal is not what the code does.**
   The freeze delta log says "until it returns, the tag refusal covers `family` only", but `passes_tag_to_child` is generic. It also fires on `tunnel encapsulation`, for which there is no device evidence (`deactivate7.in` is outstanding).
   Evidence: `printf 'set interfaces fti0 unit 0 tunnel encapsulation gre\ndeactivate interfaces fti0 unit 0 tunnel encapsulation\n' | uv run --locked junoscfg convert -i set -e structured` gives UNPLACED, and the tag is dropped with a note. It is loud.
   Proposed correction: either restrict the predicate to `family` until the artefact arrives, or correct the freeze and keep this as the recorded merge condition.
5. **Low–Medium: `validate_config` and `convert_config` give two answers for the same curly input.**
   `validate/structured_validator.py` still validates through schema-free `SetConverter.to_set()`.
   Evidence: `validate_config('policy-options {\n community C1 {\n members 64496:1;\n inactive: members 64496:2;\n }\n}\n', format="structured").valid` is `True`, while `convert_config` raises `ValueError` on it. `inactive: family { inet; }` is also valid there and UNPLACED in conversion.
   Proposed correction: record the gap in `display/CONTRACT.md` beside the `to_set()` limit, or validate structured input through `statements()`.
6. **Low: a tag written both inline and as a sibling is emitted twice.** JSON with both `"family": {"@": {inactive}}` and a sibling `"@family"` gives two identical `deactivate … family` lines. The cause is the trailing `@key` loop, which now admits dict-valued keys (`+not isinstance(held, bool | dict)`). Harmless on load. Proposed correction: skip the sibling when the dict carries the same inline `@`.
7. **Low: `passes_tag_to_child` also accepts leaves.** It is true for the 28 `homogeneous` *leaves* named `name` in the tree (`static-subscribers … interface name`). The docstring says "a container without a key". No caller reaches a leaf today. Proposed correction: also require `"c" in schema_node`.
8. **Low: `_holds_a_tag(remaining)` counts more than tags.** `remaining` includes the entry's own `@`, and any non-empty `@` counts, `junos:*` included. A tagged one-line entry is therefore written as a block, while the comment says "no node after the first". This is layout only (§1). Proposed correction: fix the comment, or test only tag keys after the first node.
9. **Low: tests that assert layout, and the release level of the removals.**
   `tests/test_config_store.py::test_merging_comes_from_the_mark_not_the_name` asserts `"family {"`, which is layout. That conflicts with the new `ARCHITECTURE.md` §1 sentence "a test asserts what a configuration means". The other ConfigStore layout tests assert where a tag leads a line, which carries meaning.
   Removing `SetConverter(emit_replace=)` and `ConfigStore.COMPOUND_KEYWORDS` from the secondary `junoscfg.display` door in a patch: the decision says "a minor release may" change such an API. Not re-litigated (C7); noted for the owner's patch-or-minor decision.
10. **Carried from change A's F2 (High, pre-existing): the writers drop an enum-spelled flag's tag.** `deactivate interfaces xe-0/0/0 disable` is lost by set and structured output. This breaks "Round trips" for a tagged leaf shape not in `SHAPES`. See `openspec/changes/xml-inactive-leaf/review.md`.

### Prompts

- **Trust-boundary input.**
  - Curly text from users or tools. The new `ValueError`s ("a tag inside a key or value", uneven leaf tags) echo the statement text and exit 2.
  - No new parsing outside the existing lexer.
  - None of the 19,997 single-level taggings of the device re-export raises.
  - `junos:*` attributes in JSON now reach a validation decision (F2).
- **Valid input that breaks an assumption.**
  - The assumption "a non-empty `@` is a tag" breaks on `"@": {"junos:group": "G1"}` (F2).
  - The assumption "`apply-groups` is not a leaf" breaks on `apply-groups G1; inactive: apply-groups G2;` (F3).
  - ConfigStore's assumption that a list's tag is the first matching line breaks on `deactivate system name-server` (F1).
- **Blind spot shared by implementation and tests.**
  - Round trips cover only entry and container tags. No test writes a tag on a whole list, on an enum-spelled flag (`disable`), or on a `family` carrying non-tag attributes.
  - Both the reader and its tests read the structure tree by name, so a node reached through a spelling alias falls through both.
- **Second answer to a question the codebase already answers.**
  - Tag placement: `_merge_tokens` (curly) now differs from `_apply_meta` (set) by design for one-line entries. Set input still widens `deactivate … members <value>` (C2), which curly and XML refuse, so one per-value tag has three outcomes.
  - "Which tags does this `@` hold": answered by `DictWalker._read_attrs`, and differently by `FieldValidator` and `_holds_a_tag` (F2, F8).
  - `SetConverter.to_set()` (validation) and `statements()` (conversion) disagree (F5).
  - `ConfigStore` merging now comes only from the walker's `mark_merged`; there is no direct ConfigStore caller left in `src/`, so this is fine.
- **Stated figures and non-goals.** All figures that could be rerun hold; see below. Non-goals are respected: layout differences are left alone, C8 keyed `homogeneous` containers are unchanged (`… routing-instance R1 R1` is the same on A and B), and `to_set()` output is unchanged.

### Figures rerun

- Focused tests (`test_meta_tags*.py`, `test_xml_inactive_leaf_challenge.py`, `test_to_yaml.py`, `test_characterization.py`, `test_cli.py`, `test_config_store.py`, `test_artifact_builder.py`, `test_set_input.py`): 469 passed.
- B's tests on A's `src/`: 48 failed and 45 passed. Of the 25 spec-cited ids, 8 pass on A:
  - the 3 unchanged bracket tests (MODIFIED `raw-set-input`, wording only);
  - `test_set_input_still_marks_the_last_node` and `test_set_output_repeats_it`;
  - 3 guards for regressions the interim fixes closed: entry in list block, apply-macro data, bare list keyword.
- Grammar:
  - `junos-set.lark` has 9,778 newline-terminated lines at both heads (the freeze says 9,779).
  - The sorted text with masked hashes is identical.
  - Partition refinement over rule bodies shows the two grammars isomorphic under variant renaming, `start` included, so set validation is unchanged.
- Structure tree: the only change is 4,132 added `h: true`. That is 3,432 lists, 672 containers and 28 leaves, exactly twice the freeze's XSD counts of 1,716, 336 and 14. `passes_tag_to_child` holds for 290 `family`, 16 `encapsulation` and 28 `name` leaf nodes, against 145 and 8 in the freeze. `junos-schema-meta.json` changes only `generated_at`.
- Device oracle on the re-export:
  - IR of curly vs device JSON goes from 588 lines (A) to 562 (B), equal to set input.
  - The curly IR equals the set IR.
  - Set output from curly equals set output from set (4 extra and 8 missing vs the device, the out-of-scope classes).
  - Curly → structured → IR and set → structured → IR are unchanged.
  - XML and JSON round trips are equal once numbers and one-value lists are normalised (the recorded follow-ups).
  - Every input format gives the same tag count.
- Level-tagging probe: none of 19,997 single-level taggings of the 3,422 statements raises. All 16,541 block-opener taggings give the IR of set `deactivate <path to that level>`.
- The 1,433 one-line statements that differ from `deactivate <whole statement>` are all the designed start-node rule: entries, `then`, `from`, `community`.

### Not checked

- The full suite and `agent-ready check --set full` on 7eebb2c: still running separately when this was written. Would catch: regressions outside the focused files and gates (lane, specs, interfaces).
- `--regen-schema` reproducibility. Would catch: committed artifacts that differ from what the generator produces.
- The `--schema` tier over every XSD dump, and the 25.2 XSD counts themselves: the tree was checked, not the XSD. Would catch: `homogeneous` on nodes the shipped tree lacks.
- The device's acceptance of a tag on a whole list (`deactivate system name-server`) and on `tunnel encapsulation` (F1, F4). Would catch: which side of each finding the device is on.
- The anonymize and audit pipelines with tagged curly input, and the ansible collection's 33 tests. Would catch: consumer reliance on the old placement.

### Builder response (2026-10-10)

- Finding 1 (High, a tag on a whole list written on its first entry; pre-existing on master, inside this change's round-trip requirement): corrected. Structured output writes such a list as its keyword's tagged block with the entries inside and never collapses it (`keep_block`), the layout the device uses for `inactive: routing-instance { R1 {…} }` (`deactivate6.txt`) and that this change's reader reads as a list-level tag. Round trips for `name-server`, static `route`, a one-entry list and the one-line `route-filter` list hold (`TestAListTaggedAsAWhole`, failing before the correction). Open for the owner: whether the device accepts that layout for a list it does not print as a block (`deactivate routing-options static route`); set output is unaffected either way.
- Finding 2 (Medium, metadata counted as a tag on `family`): corrected; one kernel answer, `junoscfg.display.holds_tag`, for the validator and the writer (`test_metadata_on_family_is_not_a_tag`).
- Finding 3 (Medium, uneven `apply-groups` tags widened in curly input): corrected; refused as uneven leaf tags are (`test_uneven_tags_on_apply_groups_are_refused`).
- Finding 4 (Medium, `encapsulation` covered without evidence): the freeze now says what the code does; the device answer is a merge condition.
- Finding 5 (Low–Medium, `validate_config(format="structured")` through `to_set()`): carried forward as follow-up 10 in `private_test_data/meta-tag-follow-ups.md`.
- Low: a tag written both inline and beside `family` is repeated once (`test_a_family_tag_written_twice_is_repeated_once`); `passes_tag_to_child` now requires a container (`c`, not `l`); the `_holds_a_tag` docstring states what it checks; the `ConfigStore` test asserts the tag position, not the whole text. The patch-versus-minor question stays with change A's C7.
- The corrections return to the same Reviewer before merge.

### Re-review (2026-10-10)

Same Reviewer. I reviewed only the corrections: `git diff 445aca8..733574d`, which is the rebase of 7eebb2c onto A's 164ae86 plus `meta-tag-placement: phase-6 corrections`. I edited nothing; the mutation run was restored afterwards and the tree is clean apart from this section.

**Verdict: mergeable after fixes.** Findings F1, F2, F3, F6, F7 and F8 are fixed, each with a test that fails without it. F4 and F5 are recorded (freeze and follow-up). One High remains: R1, which B's reader makes worse than on A.

- **The new tests fail without the correction.** With 445aca8's `src/` swapped in, all 7 new tests fail: `TestAListTaggedAsAWhole` (4 shapes) and `TestOnlyTagsCountAsTags` (3). At 733574d the focused files (`test_meta_tags*`, `test_xml_inactive_leaf_challenge`, `test_to_yaml`, `test_characterization`, `test_cli`, `test_config_store`, `test_artifact_builder`, `test_set_input`, `test_convert_*`, `test_set_converter`) give 608 passed.
- **The whole-list block layout (`keep_block` with `split_key_name`) holds.** Round trips through structured output and through set are equal for:
  - `name-server`, static `route` and `unit`
  - multi-key `route-filter`, written as `inactive: route-filter { 198.51.100.0/24 exact; … }`
  - a whole `community` list and a whole `term` list
  - a whole list plus a protected entry inside it
  - a whole list inside `groups`
  - an inner `next-hop` tag inside a whole-tagged `route` list.

  The oneliner is now suppressed for every `split_key_name` entry, transparent-child entries included. That changes layout only (§1). The interface entry path is untouched.
- **`holds_tag` holds.** `junos:group` on `family` no longer warns, and `--strict` exits 0. A real tag on `family` is still reported. A `family` tag written both inline and as a sibling is emitted once.
- **The `apply-groups` evenness check holds.** An even `inactive: apply-groups [ G1 G2 ];` still reads; an uneven pair raises `ValueError`.
- **`passes_tag_to_child` now requires `c` and no `l`**, so the 28 `name` leaves are out. The family and encapsulation behaviour is unchanged, and the set grammar is unaffected (the predicate is runtime only).
- **The level probe and oracle still hold, with one caveat.** The owner replaced `anon/` at 15:39:
  - None of 20,048 level taggings of the 3,424 statements raises.
  - All 16,624 block-opener taggings equal set `deactivate <path>`.
  - The curly IR equals the set IR (570 lines against device JSON for both), and set output from curly equals set output from set.
  - Structured round trips hold for set and curly sources.
  - Caveat: the new export carries **no tags in any format**, so it no longer exercises tag placement. The tag-placement figures in the evidence freeze rest on the earlier export.

**R1. High (introduced by B's reader on top of change A's R1): `deactivate protocols lldp disable` becomes a deactivated `lldp` after a structured round trip.**
- Requirements: "Structured output puts a tag at the head of its node's line … SHALL NOT join onto one line a node after the first that carries a tag", and "Round trips".
- Artifact: the `has_nk_leaf` / `emit_positional` branch in `dict_walker.py`, which writes the flag merged into the parent's line. With the tag now emitted (change A's correction), it becomes `inactive: lldp disable;`, and B's reader correctly gives that tag to `lldp`, the node the statement starts.
- Evidence: `printf 'set protocols lldp disable\ndeactivate protocols lldp disable\n' | uv run --locked junoscfg convert -i set -e structured | uv run --locked junoscfg convert -i structured -e json` gives `"lldp": {"@": {"inactive": true}, "disable": [null]}`. The whole of LLDP is deactivated, silently.
- With a sibling (`set protocols lldp interface all`), the tag is dropped instead, also silently.
- Set output is correct.
- Proposed correction: as in change A's R1. Do not merge a tagged value-spelled flag into its parent's line; write `lldp { inactive: disable; … }`. Add both shapes to `SHAPES`.

### Builder response to the re-review (2026-10-10)

- R1 (High, a tagged statement-name flag under a container: dropped beside a sibling, read back as the container's tag alone): corrected in change A's writer (a tagged flag is a line of its own) together with this change's rule that no line joins past a tagged node. `TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_flag_under_a_container_keeps_its_tag` covers both lldp shapes; change A's strict xfail for the shape alone is promoted here and passes.
- The replaced `anon/` export carries no tags, as the re-review notes: the tag figures in the freeze rest on the earlier export and on the level probe, which tags every level itself.
