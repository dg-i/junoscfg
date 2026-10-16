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

Fresh isolated Reviewer (separate agent dispatched by the coordinator, no Builder reasoning)
on `git diff 4dc114e...8846937` (code head `ec1de93`), probes p1 to p8 against archive
snapshots of base and head (kept beside the verdict in the coordinator's scratchpad,
`review-ocf/`). Verdict: **Merge after fixes**. The code is sound: each defect is fixed at
the owning layer with one rule, no wrong answer or regression found, 175 of 316 selected head
tests fail at base for their defect and all pass at head. Resolutions in the commit after
`8846937` (records and one test file; no runtime file changed, so the full check stands):

14. B1 binding (records): the declared-break record understated the surface changes. Fixed:
    `.openspec.yaml` `removes` and consumer/cli `why`/`migration`, the proposal's Completion
    and the changelog fragment now state (a) `yaml` validation reports a cycle, depth past 64
    and a non-string key, including where base judged the document valid (a cycle,
    `host-name` holding 70 or 300 nested lists, `host-name: {1: x}`); (b) JSON and XML past
    64 levels are refused including the range base still converted (JSON 65 to about 448
    levels, plain XML to 250, repeated-element XML to 163); (c) JSON is refused wherever a
    value passes 64 levels, outside `configuration` too, and `-v -i json` goes from OK and
    exit 0 to exit 1; (d) a relative leaf, leaf-list or flag selection writes bare commands in
    set and the note in structured. Justification for each: no Junos configuration nests past
    about 28 levels counting groups or holds such keys or cycles; (d) is the approved
    path-filtering requirement. Not a break, patch.
15. A4 advisory: message-door rows added to `tests/contract/test_every_message.py`:
    `read-xml-deep`, `cli-read-xml-deep`, `cli-validate-only-json-deep`,
    `cli-validate-only-yaml-key` (withheld under `--anonymize-ips`, kind and path otherwise).
16. A5 advisory: the main spec's "a key that is not a string named by its kind" is replaced
    when the MODIFIED delta is applied at finalization.
17. A6 advisory: `NonJsonValue.read_refusal` became a method; `junoscfg.input` is not the
    `consumer` surface; callers and `docs/api/input.md` updated. No action.
18. A1, A2, A3: pending owner decisions, below.

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
- Decision: Pending owner decision. The fresh Reviewer judged that the new behaviour fulfils
  the approved requirement: the archived relative-selections record states the invariant
  ("relative set and structured, put back under the path's words, read as the absolute
  output; set writes a bare command, structured notes the drop"), and keeping base output
  would break it once absolute output carries the tags. Interim action, kept: the fix applies
  to relative selections too; pinned by
  `TestPathFiltering::test_a_relative_leaf_selection_writes_its_tags_as_a_container_does`.
  Note for the owner: a bare `deactivate` at a leaf's edit level is not device-evidenced
  (nor for a container; the approved relative design).

## Pending owner decisions

Recorded, not backlogged (no backlog entry without the owner):

- SC1 (above): relative leaf, leaf-list and flag tags; interim the new behaviour.
- A1 (Reviewer, executed): relative json, yaml and yaml-new selections of a tagged leaf write
  the value alone and drop the tags without a note; relative structured does not note an
  `active` tag or a comment. Pre-existing at base, as the approved requirement says ("value
  alone"); the output loads the leaf active. Raise with SC1.
- A2 (Reviewer, executed): per-value leaf-list tags (`"@domain-search": [null, {"inactive":
  true}]`, JSON input) are dropped by the set and structured writers, for `--path system` and
  at base too; json, yaml and yaml-new keep them. Not covered by `docs/BACKLOG.md`
  MAKEOVER-14, which owns metadata on absent targets (NTP, hostname, securid-server) and
  states the scalar/leaf-list target widening fixed; the set reader refuses per-value tags
  (change reject-leaf-list-meta-values), the writers' drop of them from JSON or YAML is not
  listed anywhere.
- A3 (Reviewer, executed): leaf values are unconstrained in the JSON and YAML validation
  schemas (`host-name: {1: x}` or 1,600 nested lists validate); why SC3 and B1 (a) exist.
- C3 (preflight): an ancestor's tag on an absolute path (`deactivate system`, `--path
  system.host-name`) is dropped; needs a device artefact.
- SC3 (Test/Challenge): JSON validation now reports depth; Builder ruling, owner to confirm.
- TC7 observation: the `yaml` writer writes a key holding NEL, LINE or PARAGRAPH SEPARATOR so
  that it reads back with a space (the writer stays as it was, owner instruction 2026-10-15).
- SC4 (Test/Challenge): a `yaml` date value; already `docs/BACKLOG.md` YAML-DATE-001.
