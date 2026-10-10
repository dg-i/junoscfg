## Specification challenges

Raised by the independent Test/Challenge role (`test-challenge.md`, 2026-10-10,
fresh context-isolated agent, worktree at 7a60907). Interim actions are the
Builder's safe, reversible steps under existing architecture (`ARCHITECTURE.md`
one-IR rule); the owner decides each.

### S1 — "Presence flag" was decided without the schema

- **Artifact**: requirement "An inactive leaf from XML reaches the IR set and structured input give"; `display/to_yaml.py::_xml_children_to_dict`.
- **Counterexample**: executed: `<protocols><lldp inactive="inactive"/></protocols>` gave `[null]` + `@lldp`; set and structured input and master's XML input give `{"lldp": {"@": {"inactive": true}}}`.
- **User impact**: JSON/YAML output from XML differed from the same configuration read as set; set and curly output kept the meaning.
- **Proposed correction**: decide leaf versus empty container from the structure tree (`l`/`p`); add a scenario.
- **Decision**: Pending owner decision. Interim action taken (one-IR rule): `_holds_a_value` asks the tree; an untagged empty element stays `[null]` as on master; scenario "Empty tagged container" and `tests/test_xml_inactive_leaf_challenge.py::test_an_empty_inactive_container_matches_set_input` added; the challenger's strict xfail is promoted.

### S2 — The JSON scenario cited the device JSON but used a string

- **Artifact**: scenario "Single inactive leaf".
- **Counterexample**: `deactivate6.txt` writes `"vlan-id" : 751`; JSON input keeps the number, so the four IRs differ by type, while set output agrees (`test_device_json_with_a_number_value_writes_the_same_set_lines_as_xml`).
- **User impact**: none on set or curly output; the scenario claimed more than the device's JSON reaches.
- **Proposed correction**: say so in the scenario; JSON input's numbers are follow-up 6 in `private_test_data/meta-tag-follow-ups.md`.
- **Decision**: Pending owner decision. Interim action taken: scenario wording only.

### S3 — The whole-leaf-list requirement stopped at the IR

- **Artifact**: requirement "An inactive leaf-list is inactive as a whole".
- **Counterexample**: executed: structured output writes `members [ … ];` without the tag, from XML (this change's IR) as from set input (pre-existing writer gap).
- **User impact**: XML or set → structured output silently re-activates a deactivated leaf-list on load.
- **Proposed correction**: the curly writer keeps the tag; that writer is change B's scope.
- **Decision**: Pending owner decision. Interim action: fixed in change B (`meta-tag-placement`); here the challenger's test stays a strict xfail naming B.

### Low findings without a spec change

- The refusal message for uneven tags said "inactive" for uneven `protect`; it now says "tags".
- A comment node inside a leaf element raises an lxml `ValueError`; no device writes it; carried forward as not checked against master.

## Phase-6 review (fresh session, 2026-10-10)

Fresh context-isolated Reviewer, worktree at 458e9b3 (base 6635b11). Read the
change folder, `ARCHITECTURE.md` §1 and §8, `AGENTS.md`, `display/CONTRACT.md`,
decision 2026-10-09, the tests and the diff; device captures read, no value
copied. Probes use test-data values only. No product code, spec or test edited
(two temporary checkouts of base files for mutation runs were restored; tree clean).

### Verdict

**Mergeable after fixes.** The vlan-id defect is fixed at the owning layer, and the
five acceptance tests fail without the fix. The interim S1 fix
(`_holds_a_value`) left requirement 1 unmet for presence flags spelled through
`statement_name_spellings`, the most common one being `interface … disable`. The
correction for that depends on a writer defect that was already on master (F2).

### Findings

1. **High: the requirement "An inactive leaf from XML reaches the IR set and structured input give" is unmet for enum-spelled presence flags.**
   Artifact: `src/junoscfg/display/to_yaml.py` `_holds_a_value` (diff hunk `+def _holds_a_value`), which asks `_schema_of`, a lookup by local name. `disable` is no key in the tree. It is the `enable-disable` nokeyword leaf, a shape that holds for 4,238 nodes (`constants.py` docstring), and the set reader resolves it through `statement_name_spellings`.
   Evidence:
   `printf '<configuration><interfaces><interface><name>xe-0/0/0</name><disable inactive="inactive"/></interface></interfaces></configuration>' | uv run --locked junoscfg convert -i xml -e structured` prints nothing, so the interface vanishes.
   `-e set` prints `deactivate interfaces xe-0/0/0 disable` with no `set` line, and `-e json` gives `"disable": {"@": …}`. Set input of the same statement gives `"disable": [null], "@disable": {"inactive": true}`.
   The pre-challenge head 7a60907 matched set input, so the interim fix brought master's shape back. The same happens to `protocols lldp disable` and to a `groups` wildcard interface.
   Proposed correction: treat a tagged empty element as a container only where the tree says it is one (`c`, not `l`/`p`), and resolve the name as the set reader does. Add `<disable inactive="inactive"/>` to the acceptance tests. **Land this only together with F2.** Otherwise XML → set writes `set interfaces xe-0/0/0 disable` without the `deactivate`, which disables the interface; this was verified on 7a60907.
2. **High, pre-existing on master and outside this diff: the writers drop the tag of an enum-spelled flag.**
   Artifact: `convert/output/dict_walker.py` (B head lines 288–302). The `child_schema is None and value == [None]` / `has_nk_leaf` branch emits the `set` line and `continue`s without `_emit_attrs`, and the trailing `@key` loop skips list-valued keys.
   Evidence: `printf 'set interfaces xe-0/0/0 disable\ndeactivate interfaces xe-0/0/0 disable\n' | uv run --locked junoscfg convert -i set -e set` prints only `set interfaces xe-0/0/0 disable`. Device-shaped JSON (`"disable": [null], "@disable": {"inactive": true}`) does the same. Structured output loses `inactive:` too.
   The effect is that a deactivated `disable`, an interface the operator kept enabled, loads as disabled, silently.
   This breaks the capability Purpose this change adds ("every writer renders the tag where the device would accept it").
   Proposed correction: emit the leaf attributes in that branch, and add a set → set and set → structured test. Owner: in A, in B, or as a blocking follow-up.
3. **Low: one test cited as acceptance is a guard.** `tests/test_xml_inactive_leaf_challenge.py::test_an_empty_inactive_container_matches_set_input` passes on base 6635b11. It guards the interim fix, and the spec lists it beside tests that fail before the fix. Proposed correction: none needed, or label it a guard.
4. **Low, pre-existing: a comment node inside or beside a leaf raises lxml's `ValueError: Invalid input tag of type <cython…>`**, on master too. Example: `<host-name>router1<!-- c --></host-name>`, or a comment sibling under `<system>`. No device writes XML comments (annotations are `junos:comment`). Proposed correction: follow-up, `_filtered_children` skips non-elements.

### Prompts

- **Trust-boundary input.**
  - XML from a file or stdin. The new uneven-tag `ValueError` names only the element and exits 2 on the CLI (guard tests).
  - `inactive="yes"` is ignored silently (not device output).
  - The lxml parse is unchanged (pre-existing `S320` waiver).
  - Nothing new reaches a shell or a path.
- **Valid input that breaks an assumption.** The assumption is that a childless element's local name finds its tree node. `<disable inactive="inactive"/>` breaks it (F1).
  A second case: a tagged empty element outside the shipped tree, such as a statement a newer release adds. It becomes `{"@": …}` while untagged it is `[null]`, so one statement gets two shapes depending on the tag (not device-evidenced; low).
- **Blind spot shared by implementation and tests.**
  - Every test compares junoscfg's own readers against each other, on names that are tree keys.
  - No test uses a statement reached through `statement_name_spellings`.
  - No test sends an inactive presence flag through set or structured *output* (F1, F2).
- **Second answer to a question the codebase already answers.** "Is this element a leaf?" is answered by `_holds_a_value` → `_schema_of` (local name), while the set reader answers it with `statement_children` / `statement_name_spellings`. The two disagree on 4,238 nodes. One answer should serve both readers (`ARCHITECTURE.md` §1 point 2).
- **Stated figures and non-goals.**
  - Five acceptance ids fail on base: confirmed, plus eight challenge tests.
  - The "245 passed" focused-test figure: a different selection, not rerun. The focused files here give 189 passed and 1 xfailed.
  - Non-goals hold: there is no per-value marker, and set input's `deactivate … members <value>` is untouched (C2, change B's follow-up).

### Figures rerun

- `uv run --locked pytest tests/test_xml_inactive_leaf_challenge.py tests/test_to_yaml.py tests/test_characterization.py tests/test_cli.py -q`: 189 passed, 1 xfailed (the xfail is B's writer gap, closed on B).
- With base `to_yaml.py` swapped in, the five spec ids plus eight challenge tests fail. Three pass: the empty-container guard's two cases and `test_an_empty_inactive_container_keeps_its_meaning_in_set_output`, all guards of master behaviour.
- Device oracle (`private_test_data/anon`, counts only): XML IR vs device JSON 3,116 differing lines on A and on B. This is the known number and one-value-list follow-up; the XML → structured → IR round trip is equal once those are normalised.
- The JSON-number follow-up (S2): set output from device-shaped JSON equals XML's (guard test passes).

### Not checked

- The full suite and `agent-ready check --set full` on 458e9b3: run separately. The log in the session scratchpad reports 1,935 passed, 45 skipped, 2 xfailed, "every check passed". Would catch: regressions outside the focused files.
- `validate_config` for XML: the worktree has no XSD (`SchemaLoadError`). Would catch: XML validation accepting what conversion refuses.
- Device XML of `deactivate interfaces … disable` is not captured. F1 rests on the attribute pattern of `deactivate2.txt` and on set input. Would catch: the device writing a different XML shape.
- The anonymize and audit pipelines with tagged XML. Would catch: a consumer of the old nested shape.

### Builder response (2026-10-10)

- Finding 1 (High, `_holds_a_value` and enum-spelled flags): fixed. An empty tagged element is a container only where the tree names a container (`c`, not `l`/`p`); `<disable inactive=…/>` is the flag set input gives. Scenario "Tagged flag spelled by its value".
- Finding 2 (High, writers drop the tag on such flags; pre-existing on master): fixed with it, as the review asks: `DictWalker`'s statement-name branch emits the flag's tag. Executed before/after: `set interfaces xe-0/0/0 disable` + `deactivate … disable` round-trips through set and structured output. Test `TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_disable_flag_keeps_its_tag` fails without the fix (product code stashed) and passes with it. `convert/output/dict_walker.py` is a context expansion for this change, taken because the review ties the two findings together.
- Finding 3 (Low): agreed; `test_an_empty_inactive_container_matches_set_input` is a guard against change A's own interim regression, not an acceptance test of the original defect; kept as a guard.
- Finding 4 (Low, comment node, pre-existing): carried forward to `private_test_data/meta-tag-follow-ups.md`.
- The fix returns to the same Reviewer before merge (phase 6: accepted corrections go back to it).
