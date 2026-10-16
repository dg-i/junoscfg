## Findings

Independent Test/Challenge (fresh agent, Opus, no Builder reasoning, high risk floor) on a
detached snapshot of tests commit `5c513a9` against base `2d4904b`; probes, a candidate
implementation and mutants under `private_test_data/makeover-work/own-crash-fixes/tc/`.
Every red test failed at base for its intended reason (120 failed, 1,232 passed,
`tc/red-full.txt`). Resolutions are in the commit after `9b0c903` (red run of the final tests
against base: `red-run-2.txt`, 183 failed for their defects; guards pass at base):

1. TC1 binding: `TestPathFiltering::test_a_relative_yaml_new_selection_is_measured_as_written`
   read JSON past 64 levels. Fixed: the IR is handed to `from_dict(..., below=path)` as the
   pipeline hands it (no reader gives such an IR any longer, XML included, see SC2).
2. TC2 binding: the relative guard pinned base output the approved relative requirement calls
   wrong. Fixed with SC1 (below): the guard became
   `test_a_relative_leaf_selection_writes_its_tags_as_a_container_does`.
3. TC3 binding: a validator refusing YAML scalar values survived. Fixed:
   `TestYamlValidation::test_a_yaml_scalar_value_keeps_its_verdict` (a date, an unquoted `on`,
   `010` stay valid).
4. TC4 binding: the relative guard covered one scalar leaf by bytes. Fixed: parametrized over
   the leaf, the leaf-list and a flag, by meaning (set put back under its path, loaded values).
5. TC5 binding: list-level sibling annotations of the device corpus untested. Fixed:
   `tests/corpus/test_device_renderings.py::TestAnAbsoluteSelectionKeepsItsTags` (every tagged
   path to depth 5 of every capture: `groups`, `access.radius-server`, `routing-options.router-id`
   comments, the `l3vpn` flag; fails at base), and the requirement names flags and a list's comment.
6. TC6 advisory: flag and dotted key. Fixed: `system.no-redirects` in every leaf test and
   `test_a_dotted_flag_keeps_its_tags` (`system.services.netconf.version-1.1`).
7. TC7 binding: the `yaml` writer's key quoting was unpinned. Fixed:
   `TestTheYamlWriterDumpsTheIr::test_every_key_it_writes_reads_back` (keys YAML reads as numbers,
   dates, booleans, null). Observed: a key holding NEL, LINE or PARAGRAPH SEPARATOR reads back
   with a space; the `yaml` writer stays as it was (owner instruction 2026-10-15), so those keys
   are outside this law (pending owner decision, reported).
8. TC8 advisory: doors. Fixed: `test_an_anonymized_leaf_selection_keeps_its_tags`,
   `TestFilterDictByPath::test_the_text_filters_keep_a_selected_leafs_annotation`, detected JSON
   in `test_json_past_64_levels_exits_two`, `to_dict` in `TestJsonReader`.
9. TC9 advisory: spec trace and a misleading name. Fixed: every new test is on a `Tests:` line;
   `test_a_key_reads_as_yaml_new_reads_it` renamed `test_both_yaml_readers_refuse_a_key_alike`.
10. TC10 advisory: the first red run listed pre-rename ids. Superseded by `tc/red-full.txt`
    (from `5c513a9`) and `red-run-2.txt` (final tests against base).
11. SC2 (Test/Challenge, accepted by the owner's instruction "check whether other input formats
    hit the same RecursionError at depth and fix them under the same rule if so"): XML repeating
    its element at each level doubles the IR depth; from about 164 XML levels `-e yaml` raised
    `RecursionError` (`tc/probes/xml_list_depth.red.txt`). Fixed: the XML reader calls
    `find_non_json_value` ("an XML value at ... is nested deeper than 64 levels");
    `TestXmlReader`.
12. SC3 (Test/Challenge): JSON validation judged a leaf holding 1,600 nested values valid and
    `convert -v -i json` printed "Validation: OK" before crashing. Fixed as yaml and yaml-new
    validation do: `validate_json` reports the depth (`TestJsonValidationDepth`,
    `test_json_past_64_levels_exits_one`). Builder ruling within the change's outcome (no
    traceback, no wrong verdict at the JSON door); reported to the owner.
13. SC4 (Test/Challenge): a `yaml` date value drops its statement in set and structured output
    and crashes `-e json`. Already in `docs/BACKLOG.md` as YAML-DATE-001; outside this change.

Fresh isolated Reviewer: pending, dispatched by the coordinator after the full check.

## Specification challenges

### SC1: a leaf selected relative now writes its tags as a selected container's

- Artifact: the coordinator brief (owner request 2026-10-16: "Relative selections are out of
  scope: the archived change deliberately drops a tag on the selected statement itself when
  relative") and this change's first delta wording ("a relative selection ... unchanged by
  this one"), against the approved requirement `conversion/path-filtering` "A relative
  selection is written as absolute output writes it, without its path": "a tag on the
  selected statement itself is a bare command in set output (`deactivate`) and, in
  structured output, dropped with a note".
- Counterexample (executed): `set system host-name r1`, `deactivate system host-name`,
  `protect system host-name`, `--path system.host-name --relative -e set`. Base writes
  `set r1` (the tags silently dropped, as for the absolute selection); with the fix, which
  hands every writer the leaf's annotation, it writes `set r1`, `deactivate`, `protect`,
  as `--path system.syslog --relative` of a deactivated syslog already writes `deactivate`;
  structured writes `r1;` with the existing note "2 tag(s) of the selected statement itself
  dropped"; json, yaml and yaml-new write the value alone, unchanged. Device corpus
  (`probe_selections.py`, 2,875 relative selections): 2 relative outputs change, both set,
  `routing-options.forwarding-table.chained-composite-next-hop.ingress.l3vpn` (a deactivated
  flag) from `set` to `set`, `deactivate`.
- Violated invariant: base violates the approved relative requirement for leaves (a tag on
  the selected statement itself was dropped without the bare command or the note); the brief
  asks for relative output to stay as it is.
- User impact: a relative leaf selection loaded under `edit system host-name` was active at
  base; with the fix it is deactivated, as the configuration says. A script comparing the
  relative text of a tagged leaf sees new lines.
- Proposed correction: accept, and record the relative leaf behaviour in the path-filtering
  delta (done, scenario "A tagged leaf selected relative"). The alternative keeps base: the
  pipeline strips the selected key's annotation for a relative selection (about three lines
  in `junoscfg.convert.pipeline`), keeping an output the approved relative requirement calls
  wrong.
- Decision: Pending owner decision. Interim action, fixed by the approved relative
  requirement and needing no code of its own: the fix applies to relative selections too;
  pinned by `TestPathFiltering::test_a_relative_leaf_selection_writes_its_tags_as_a_container_does`.
