# Backlog

Authoritative destination: this file.

This file and its contents belong to the application. Template updates preserve
it. If an existing issue tracker is declared, replace the destination above
with its URL and keep this file as a pointer only. Move active entries there,
preserving finding IDs and evidence links; maintain status only in that tracker.

Follow [review scope](how-to/review-scope.md). Each entry records:

- Finding ID: the existing review ID, qualified by its change slug if needed.
- Defect and impact.
- Reproducer or evidence.
- Source change: link to the original review evidence and authoritative ruling.
- Status: open, selected (with implementation-change link), or closed (with reason).

Ordinary entries are future work. Binding dependencies and carry-forward
acceptance conditions remain obligations under their original rulings.
Create an OpenSpec change only when an item is selected for implementation.

## YAML-JSON-001 — Share Junos JSON normalization with YAML

- **Status:** selected 2026-10-15 with an owner modification; implemented by the
  OpenSpec change `yaml-new-format` (archived under `openspec/changes/archive/`)
  as the parallel format `yaml-new`, with `yaml` unchanged. The rename of `yaml`
  to `yaml-old` and `yaml-new` to `yaml` stays open future work under
  [its decision record](decisions/2026-10-15-yaml-new-before-renaming-yaml.md).
- **Finding and impact:** YAML output currently dumps the IR directly, while
  the Junos JSON writer normalizes its own copy. JSON representation fixes
  therefore do not automatically reach YAML, and output shapes can differ.
- **Proposed direction:** share object-level Junos-data adapters between JSON
  and YAML, with separate parsers and serializers. Avoid serializing and
  reparsing JSON text merely to reuse the conversion rules. Retain YAML's
  metadata cleanup and scalar leaf-list promotion explicitly.
- **Compatibility proposal (owner suggestion):** preserve the existing YAML
  format as `yaml-old` when introducing the normalized `yaml` format, and
  support `yaml-old` → `yaml` conversion as a migration path. Define the legacy
  reader/writer behavior, format selection, deprecation policy and consumer/CLI
  migration before implementation; this entry does not introduce either format
  or approve a compatibility break.
- **Evidence:** read-only comparison on 2026-10-12 at commit
  `34bea1224999ab26d3fd97e990f78e33f25e3afd`. For each source in
  [the shape catalogue](../tests/support/shapes.py), parse with `to_dict`, then
  compare `yaml.safe_load(from_dict(ir, "yaml"))` with
  `json.loads(from_dict(ir, "json"))`, checking key order separately.
  Of 484 source/format combinations, 388 were identical, 57 differed only in
  key order and 39 differed structurally. Nine of ten hand-built IR cases in
  [the writer tests](../tests/unit/convert/test_convert_roundtrip.py) differed.
  Observed changes include unwrapping `groups.group`, converting `true` or
  empty mappings to `[null]`, collapsing single-element arrays for scalar
  leaves, and moving annotation/name keys. Actual leaf lists remain lists.
  The JSON writer also changes `true` markers inside `junoscfg:unplaced`.
  Of three synthetic device JSON captures, the two vMX captures had no
  structural differences; the QFX capture had 15 empty mappings rewritten to
  `[null]`. These observations describe current behavior, not proof that each
  rewrite is device-correct.
- **Input evidence:** among 40 YAML catalogue inputs, two produced different
  IRs when routed through `json.dumps(yaml.safe_load(source))` and the JSON
  reader: `yaml-with-ansible-meta-keys` and
  `universal-statements-below-the-root`. The JSON reader retains metadata and
  scalar leaf-list shapes that the YAML path cleans or normalizes; see the
  [conversion contract](../src/junoscfg/convert/CONTRACT.md).
- **Before selection:** settle empty-mapping and `junoscfg:unplaced` handling;
  measure effects on YAML consumers; define migration examples and acceptance
  coverage for `yaml-old` → `yaml`, input conveniences and JSON/YAML output
  equivalence. Seek path-scoped device evidence where correctness is unresolved.
- **Source and disposition:** owner-requested research and backlog disposition
  in the 2026-10-12 YAML/JSON conversion discussion; no implementation change
  or review ID exists yet. Owner requested recording the findings and the
  `yaml-old` compatibility proposal. Create and link an OpenSpec change only
  when this item is selected, as required by [review scope](how-to/review-scope.md).

## SIMPLIFY-001 — One schema-guided traversal instead of six

- **Status:** open; future work, not selected for implementation.
- **Finding and impact:** six modules each walk the dict IR (or token path)
  alongside the schema tree, and each re-implements the same descent rules:
  universal statements below the root, transparent containers (child entries
  plus sibling keys such as `interface-range`), `apply-groups`, list entries
  and unplaced records. Only the lookup `display.schema_child` is shared.
  A descent rule fixed in one walker must be fixed again in the others;
  [the field validator](../src/junoscfg/convert/field_validator.py) says so
  itself ("as in every walker of the tree (ARCH-C06)"), and NEW-A-S2 was this
  kind of divergence.
- **Walkers:** `anonymize/walker.py` (`_Walker.node`), `audit/walker.py`
  (`_walk_dict`), `convert/field_validator.py` (`_walk`, complexity 55),
  `convert/output/dict_walker.py` (`_walk`, complexity 75),
  `convert/input/set_input.py` (`_merge_tokens`, complexity 76 over 348 lines,
  and `_apply_meta`, complexity 48, which walks the same token path a second
  time to place a tag), and `display/to_yaml.py`.
- **Fix instruction:**
  1. Inventory each walker's descent rules into one table (rule × walker),
     marking where they disagree; every disagreement is a defect or a
     deliberate difference to record, never silently unified.
  2. Add one traversal to the `display` kernel that owns descent only:
     key resolution through `schema_child`/key aliases, universal statements,
     transparent containers, entry lists, `apply-groups` and unplaced records.
     It yields (path, key, value, schema node, kind) or calls per-kind hooks.
  3. Port walkers one per change, smallest first (`audit`, `to_yaml`), keeping
     each module's behaviour; the walker keeps only its own hooks.
  4. In `set_input.py`, split `_merge_tokens` into token resolution and merge,
     and let `_apply_meta` reuse the resolved path instead of re-walking;
     coordinate with MAKEOVER-14, which owns metadata traversal behaviour.
- **Acceptance:** the format matrix, device-set law and per-walker tests pass
  unchanged in their assertions (tests may move to public doors, never lose
  cases); a new descent rule is added in one place; no walker re-implements
  transparent-container or universal-statement handling.
- **Evidence:** graphify code graph rebuilt 2026-10-14 at `6498ec9` (v0.28.14),
  plus AST branch counts per function; `get("t")`/`["t"]` transparent handling
  appears in seven `src` files.
- **Source and disposition:** owner-requested complexity-versus-value analysis,
  2026-10-14; no review ID exists. Related: ARCH-C06
  ([universal statements from the tree](../openspec/changes/archive/2026-10-11-universal-statements-from-tree/proposal.md)),
  MAKEOVER-13, MAKEOVER-14. Create an OpenSpec change only when selected.

## SIMPLIFY-002 — Anonymizer wildcard-pattern machinery

- **Status:** open; future work, not selected for implementation.
- **Finding and impact:** `anonymize/rules/__init__.py` (+325 net lines since
  2026-09-01) and `anonymize/walker.py` (+422) carry a small glob engine
  (`_glob_positions`, `_accepts`, `_class_members`, `_may_be_no_digit`,
  `spells_through_syntax`, `prefix_pattern`) whose only job is anonymizing
  group name patterns such as `<ge-*>` (ANON-P3, challenges S1–S3). The
  behaviour is specified, but its cost is high for configurations that rarely
  hold sensitive values inside wildcard names.
- **Fix instruction:** keep the specified behaviour; measure how many corpus
  and device configurations exercise each branch; then decide with the owner
  whether to (a) simplify to one rule (for example, return every non-`*`
  pattern by its schema path and rewrite nothing inside it), or (b) keep it but
  isolate it in its own module behind `Rule.wildcard`. Option (a) changes a
  spec and needs a declared ruling.
- **Evidence:** as SIMPLIFY-001; growth from `git log --numstat` since 2026-09-01.
- **Source and disposition:** same analysis, 2026-10-14. Do after SIMPLIFY-001
  ports the anonymize walker, so the pattern code is measured on its own.

## SIMPLIFY-003 — Field validation beside the `validate` package (lead)

- **Status:** open; unverified lead, not selected for implementation.
- **Finding and impact:** `convert/field_validator.py` (714 lines, three
  `src` consumers; `_validate_leaf` complexity 32, `_validate_ip` 19)
  validates leaf values while `validate/` runs XSD and grammar validation.
  Whether the two check the same value types differently is not established.
- **Fix instruction:** list each value check in both stacks against the schema
  types it covers; if they overlap, give each type one owner and route the
  other stack through it. If they do not, record why both exist in
  [the conversion contract](../src/junoscfg/convert/CONTRACT.md) and close.
- **Source and disposition:** same analysis, 2026-10-14. Its walk is ported
  under SIMPLIFY-001 either way.

## SELECT-SCAN-001 — Package-wide source scanners miss package changes

- **Status:** open; future work, not selected for implementation.
- **Finding and impact:** a change under `src/junoscfg/<package>/` selects that
  package's unit tests, its importers' and `tests/contract/`, but not tooling
  tests that scan the whole package source, such as
  `tests/tooling/test_entry_key_spellings.py` and
  `tests/tooling/test_universal_statement_names.py`. Such a regression passes the
  commit hook and fails only at the full checkpoint, which runs before review.
- **Reproducer:** append `_probe = {'fe': 1}['fe']` to
  `src/junoscfg/edityaml/rules.py`; the selection omits
  `test_entry_key_spellings.py`, whose `test_no_module_keeps_its_own_key` fails.
- **Proposed direction:** select modules that read `PACKAGE_SRC`, or another
  named directory above a changed source file, without letting the selector's
  and door check's own tree scans add their tooling consumers to every package
  change.
- **Source change:** independent challenge of `affected-test-scope`
  (2026-10-14), finding 5; pre-existing behaviour outside that change's frozen
  outcome.

## YAML-DATE-001 — `yaml` input drops a statement holding an unquoted date

- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-15 on yaml-new-format PO-3: backlog.
- **Finding and impact:** PyYAML reads an unquoted date such as `2026-10-15` as a
  `datetime.date`. The legacy `yaml` reader keeps it in the IR, and the set
  writer then writes no line for that statement, so set output silently loses
  it; JSON output of the same IR fails with `TypeError`. `yaml-new` refuses such a
  value with its path, and its writer refuses it on migration.
- **Reproducer:** `convert_config("configuration:\n  system:\n    host-name:
  2026-10-15\n    location:\n      building: b1\n", from_format=Format.YAML,
  to_format=Format.SET)` gives only `set system location building b1` (reproduced
  at `87e14cd`).
- **Proposed direction:** refuse a value JSON cannot hold on `yaml` input too, as
  `yaml-new` does through `junoscfg.input.find_non_json_value`, or read a date as
  its text; the rename of `yaml` to `yaml-old` decides which.
- **Source change:** `yaml-new-format` review, Reviewer A6
  ([review](../openspec/changes/archive/2026-10-15-yaml-new-format/review.md)),
  pending owner decision PO-3; recorded by change `yaml-new-alias-cycles`.

## YAML-BREAKS-001 — `yaml` output writes NEL, LS and PS unescaped

- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-15 on yaml-new-format PO-4: backlog.
- **Finding and impact:** the legacy `yaml` writer leaves NEL (U+0085), LINE
  SEPARATOR (U+2028) and PARAGRAPH SEPARATOR (U+2029) unescaped in a single-quoted
  scalar, and YAML 1.1 reads them as line breaks. A value holding NEL reads back
  changed (`a\x85b` as `a b`; `a\x85\x85b` as `a\nb`); LS and PS are written raw
  too, and PyYAML happened to read them back unchanged in the five positions
  probed, which another YAML 1.1 reader need not. `yaml-new` writes all three
  double-quoted and escaped (`test_a_yaml_only_line_break_reads_back_as_written`).
- **Reproducer:** `from_dict({"system": {"host-name": "a\x85b"}}, "yaml")`, loaded
  with `yaml.safe_load`, gives `host-name: "a b"` (reproduced at `87e14cd`).
- **Proposed direction:** give the `yaml` writer the yaml-new string representer
  (`_JunosYamlDumper` in `src/junoscfg/convert/output/json_output.py`), or retire
  the question with the rename of `yaml` to `yaml-old`.
- **Source change:** `yaml-new-format` review, Reviewer A2
  ([review](../openspec/changes/archive/2026-10-15-yaml-new-format/review.md)),
  pending owner decision PO-4; recorded by change `yaml-new-alias-cycles`.
- **Keys too (own-crash-fixes/TC7):** Owner ruling 2026-10-16: backlog. The writer
  quotes a key the same way. `from_dict({"system": {"a\x85b": "x"}}, "yaml")`, loaded
  with `yaml.safe_load`, gives the key `a b`. The review says a key holding LS or PS
  reads back with a space too. At 716a9d1, PyYAML read both back unchanged in five
  key positions (inner, leading, trailing, doubled, space-padded), as it does for
  values. NEL changed the key in four of them (`"a b"`, `" ab"`, `"ab "`, `"a\nb"`). Interim behaviour, kept: the `yaml` writer
  stays as it was (owner instruction 2026-10-15), and such keys are outside the
  round-trip law of
  `tests/unit/convert/test_convert_api.py::TestTheYamlWriterDumpsTheIr::test_every_key_it_writes_reads_back`.
  Source: [own-crash-fixes review](../openspec/changes/archive/2026-10-16-own-crash-fixes/review.md),
  finding 7 and the pending owner decisions.

## RELATIVE-TAGS-001 — Tags of a leaf selected relative

- **IDs:** own-crash-fixes/SC1, own-crash-fixes/A1; probe SC1.
- **Status:** closed 2026-10-17 by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/) (owner ruling 2: a tag the output cannot
  write is dropped with a note, as structured output did; never a bare verb).
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: at `edit routing-options static route 198.51.100.0/24`,
  a bare `deactivate` and a bare `protect` are refused ("syntax error, expecting
  <statement>, <attribute-name>, <flag-value>, or <identifier>"); `edit ...
  description` (a leaf) is refused ("syntax error.").
- **Resolution:** every writer drops a tag at or above a relative path and gives one
  note, "N tag(s) at or above the selected path dropped: relative output writes what
  lies below the path" (spec conversion/selection-tags). Set output writes no bare
  verb; json, yaml and yaml-new note a dropped `@<key>` and keep a selected
  container's own `@`. A dropped comment gets its own note in json, yaml and yaml-new
  ("N comment(s) at or above the selected path dropped"); set and structured output
  write no comment in any selection.
- **Source change:** own-crash-fixes review, specification challenge SC1 and Reviewer
  A1 ([review](../openspec/changes/archive/2026-10-16-own-crash-fixes/review.md)).

## LEAF-LIST-VALUE-TAGS-001 — Set and structured output drop one value's tag

- **IDs:** own-crash-fixes/A2; probe A2.
- **Status:** open, narrowed. The silent drop is fixed by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/): set and structured
  output note it ("N tag(s) on single values of a leaf-list dropped: set and structured text have no form for one"); json, yaml and yaml-new keep it. Open: whether a
  device loads a per-value tag from JSON (`"@community": [null, {"inactive": true}]`).
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: `deactivate routing-options static route 198.51.100.0/24
  community 64496:2` is refused ("syntax error, expecting ';', [Enter], or '|'"),
  and the device's JSON is `"community": ["64496:1", "64496:2"]` with no per-value
  annotation, so set and curly text have no form for such a tag.
- **Proposed direction:** device question 10 in DEVICE-EVIDENCE. If the device refuses
  it, the JSON reader may report it; if it loads it, record how the device prints it.
- **Source change:** own-crash-fixes review, Reviewer A2
  ([review](../openspec/changes/archive/2026-10-16-own-crash-fixes/review.md)).

## ANCESTOR-TAGS-001 — An absolute selection drops an ancestor's tag

- **IDs:** own-crash-fixes/C3; probe C3.
- **Status:** closed 2026-10-17 by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/).
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: with the route deactivated, `show routing-options static
  route 198.51.100.0/24 description` prints `deactivate routing-options static route
  198.51.100.0/24` in set, `"@": {"inactive": true}` on the route in JSON, `<route
  inactive="inactive">` in XML and a `## inactive: ...` header in curly; with
  `routing-options static` deactivated, set adds `set routing-options static` and
  `deactivate routing-options static`.
- **Resolution:** an absolute selection keeps every annotation along its path (each
  step's `@<key>` and each ancestor's own `@`), in every format; equivalent, not
  identical: no bare `set routing-options static` (spec conversion/selection-tags).
- **Source change:** own-crash-fixes review, preflight item C3
  ([review](../openspec/changes/archive/2026-10-16-own-crash-fixes/review.md)).

## SCHEMA-LEAF-VALUES-001 — JSON and YAML validation accept any leaf value

- **IDs:** own-crash-fixes/A3, own-crash-fixes/SC3.
- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-16: backlog. Interim behaviour, kept: the JSON and YAML validation schemas
  accept any value at a leaf (the schema generator gives a leaf `{}`). Since
  v0.28.23, `validate_json` reports a value nested deeper than 64 levels, as yaml
  and yaml-new validation do, and `junoscfg convert -v -i json` exits 1 for it. That
  depth check is a Builder ruling (SC3); the owner has yet to confirm it.
- **Finding and impact:** a leaf holding an object, a list or nested lists
  validates. So JSON validation says OK for a document that no device holds. Before
  v0.28.23, `convert -v -i json` printed "Validation: OK" for a leaf holding 1,600
  nested lists, then crashed; SC3 is the guard for that case alone.
- **Reproducer:** `junoscfg convert -v -i json FILE` with `{"configuration":
  {"system": {"host-name": {"1": "x"}}}}` prints "Validation: OK" and exits 0.
  `junoscfg.validate_json` judges `host-name` inside 30 nested lists valid. Inside
  70 lists it reports "JSON value is nested deeper than 64 levels". Reproduced at
  716a9d1. Tests: `tests/unit/validate/test_json_yaml_validator.py::TestJsonValidationDepth`,
  `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_json_past_64_levels_exits_one`.
- **Proposed direction:** give a leaf the shapes Junos JSON gives it, and leave value
  types to field validation (SIMPLIFY-003). First measure that every device capture
  still validates. The owner then confirms or reverses SC3; with leaf values
  constrained, the depth check may become redundant.
- **Source change:** own-crash-fixes review, Reviewer A3 and specification challenge
  SC3, finding 12 ([review](../openspec/changes/archive/2026-10-16-own-crash-fixes/review.md)),
  pending owner decisions.

## VALIDATE-MESSAGES-001 — Some schema failures do not name the constraint

- **IDs:** device-validation/A3.
- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-16: backlog. Interim behaviour, kept: a failure other than an unknown key
  or a wrong type says only "fails the schema's 'X' constraint here", where X is the
  JSON Schema keyword. No message reprints a value; that is pinned by
  `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys`.
- **Finding and impact:** `_message` in `src/junoscfg/validate/json_yaml_validator.py`
  names the unknown keys of an `additionalProperties` failure and the expected type
  of a `type` failure. Any other keyword, such as `required`, `enum` or `pattern`,
  gets the generic text. The user learns which keyword failed, but not which key,
  value set or pattern the schema wanted. The schema's own key, values or pattern
  could be named without quoting the user's value.
- **Evidence:** code reading at 716a9d1. The shipped
  `src/junoscfg/validate/data/junos-json-schema.json.gz` and
  `junos-yaml-schema.json.gz` hold no `required`, `enum` or `pattern` keyword
  (counted at 716a9d1; every `"pattern"` there is a statement's name). No probed
  input reached the generic text with the shipped schemas: a failing `oneOf` or
  `anyOf` is reported by its type error (`_cause` in the same module). So today the
  text shows only with an artifacts directory whose schema has such keywords.
- **Proposed direction:** before selecting this item, find an input that reaches the
  generic text with the shipped schemas, or close the item if none exists. Otherwise
  name the schema's key for `required`, its values for `enum` and its pattern for
  `pattern`, and never the input's value.
- **Source change:** device-validation review, round 1 advisory A3, recorded only
  ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## JSON-KEYWORD-ALIAS-001 — When to retire the keyword alias in JSON

- **IDs:** device-validation/SC2, device-validation/R2-A1, device-validation/R2-A3;
  probe D3.
- **Status:** closed 2026-10-17 (owner ruling 1, recorded in [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/)): the alias stays
  for good and is no longer deprecated; R2-A3 (a deprecation note) is moot.
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: `load merge json` of `"802.3ad"` and `"to"` loads, and
  display set shows the same two lines as the element-name control (`ieee-802.3ad`,
  `end-range`). junoscfg keeps writing the element name; the JSON and yaml-new
  schemas take the keyword as an alias where the node records an element name
  (`802.3ad`, `to`, `hello-padding`).
- **Source change:** device-validation review, specification challenge SC2, round 2
  advisories R2-A1 and R2-A3
  ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## RENAME-EVIDENCE-001 — Six renames reach JSON from the XSD alone

- **IDs:** device-validation/SC3; probe D2.
- **Status:** open for the NAT rule `match` only; the five others closed 2026-10-17
  by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/).
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: `load merge json` of junoscfg's JSON loads, and the device
  prints `"system-name"`, `"ethernet-1g": [null]` (XML `<speed
  unsupported="unsupported"><ethernet-1g/>`) and `equal-literal`, `plus-literal`,
  `minus-literal` with `community-name`, in JSON and XML; display set shows
  `ether-options speed 1g` and `then community = | + | - JUNOSCFG-C1`. The tests
  `tests/corpus/test_device_probes.py::TestJunoscfgWritesTheDevicesJsonNames` hold
  junoscfg's JSON to the device's. The set grammar took `eq_literal` for `=`; it now
  takes the literals (same change).
- **Open:** the NAT rule renames (`dest-nat-rule-match`, `src-nat-rule-match`,
  `static-nat-rule-match`) have no node in the shipped QFX5120 schema; they need a
  platform whose schema has NAT rules.
- **Source change:** device-validation review, specification challenge SC3
  ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## READER-TREE-001 — The JSON and yaml-new readers need the structure tree

- **IDs:** device-validation/SC1, device-validation/A7.
- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-16: backlog. Interim behaviour, kept (coordinator ruling RC2a): the JSON
  and yaml-new readers read names off the structure tree, as every reader does, so
  they load `junos-structure-tree.json`. Restoring a static name table in the
  reader would reverse it.
- **Finding and impact:** device JSON writes `"ieee-802.3ad"` and `"end-range"`.
  The IR read from set, curly or XML holds `802.3ad` and `to`. One IR for every
  reader needs the tree in the JSON and yaml-new readers too. So
  `junoscfg.convert.to_dict` now raises `ValueError` for JSON or yaml-new text when
  the artifacts directory lacks the tree; before v0.28.24 it read. Every conversion
  past the reader already needed the tree, and `junoscfg` does not export `to_dict`,
  so the consumer surface does not see the change (A7).
- **Reproducer:** `with junoscfg.display.artifacts_dir(EMPTY_DIR):
  junoscfg.convert.to_dict('{"configuration": {"system": {"host-name": "r1"}}}',
  "json")` raises `ValueError` ("No junos-structure-tree.json in artifacts
  directory"). yaml-new text does the same. Reproduced at 716a9d1. Tests:
  `tests/unit/convert/test_convert_api.py::TestLeafListPromotion::test_json_scalar_leaf_list_stays_scalar`,
  `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_scalar_leaf_list_stays_scalar`.
- **Proposed direction:** the owner confirms the requirement as the main spec now
  states it, or chooses the static name table. No device evidence is needed.
- **Source change:** device-validation review, specification challenge SC1 and
  advisory A7 ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## UNDOCUMENTED-001 — Undocumented statements no committed capture shows

- **IDs:** device-validation/D4, device-validation/P4; probe D4, P4.
- **Status:** closed 2026-10-17 by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/).
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: the device takes grpc `clear-text address 127.0.0.1` beside
  `port 32767` (JSON `"clear-text": {"address": ..., "port": ...}`), `system
  debugger-on-break` and `debugger-on-panic` (`<undocumented><x/></undocumented>`),
  `chassis dump-on-panic` (`<chassis><undocumented><dump-on-panic/>`, JSON
  `"dump-on-panic": [null]`) and `system dump-on-panic`, which XML prints as an open
  and a close tag with nothing inside; every reader takes it as the flag `[null]`
  (`tests/corpus/test_device_probes.py::TestEveryAcceptedLineReadsAsOneIrInEveryFormat`;
  its JSON rendering is device question 9 in DEVICE-EVIDENCE).
- **Resolution:** five `_UNDOCUMENTED` rows in `src/junoscfg/validate/xsd_fixes.py`
  (still 44 fixes), artifacts regenerated; `grammar-corpus.json` records no rejection.
- **Source change:** device-validation review, device question D4 and pending
  decision P4 ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## HOLD-TIME-001 — `hold-time` with only `down`

- **IDs:** device-validation/D1; probe D1.
- **Status:** closed 2026-10-17 by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/): the warning is device-confirmed.
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: `set interfaces ge-0/0/1 hold-time down 0` loads, and
  `commit check` fails ("Missing mandatory statement: 'up'"); `up 0` alone fails
  with `down` missing; `up 0 down 0` passes. The expected finding of
  `jvd/vmx-23.2R2-S7.5/mdr1_acx7509` is now class `mandatory-commit-refuses` in
  `tests/data/device/expected-findings.json`. The recorded case sits in a group no
  `apply-groups` names; whether `commit check` refuses an unapplied group is device
  question 5 in DEVICE-EVIDENCE.
- **Source change:** device-validation review, device question D1
  ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## VERB-PREFIX-001 — A verb that stops before a list entry's name

- **IDs:** device-validation/D5; probe D5, A2.
- **Status:** closed 2026-10-17 by [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/).
- **Evidence:** QFX5120 25.2R2-S1.5 probe of 2026-10-16, sanitized record `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`: `protect policy-options policy-statement` and `deactivate
  policy-options policy-statement` are refused ("syntax error, expecting
  <identifier>"); one leaf-list value is refused too (A2). An earlier probe took
  `deactivate forwarding-options port-mirroring family inet output routing-instance`,
  a list the XSD marks `homogeneous` (`private_test_data/deactivate6.txt`).
- **Resolution:** one read-only walk, `junoscfg.display.meta_target`, decides what a
  verb line names, for the set reader and for `-v`: a container, a list entry after
  its whole key, a leaf before its value, or a homogeneous list whole. Another list's
  bare keyword, a tag on `family` itself (which the device refuses under `interfaces …
  unit`, "missing argument"; set output drops it with a note; the same rule covers
  `family` elsewhere by extension and `tunnel encapsulation` without device evidence,
  device question 12) and a leaf's value are refused, a stop inside a key is
  invalid and kept unplaced. Owner ruling 2026-10-17 on review S-6: keep the
  `homogeneous` reading as built, inferred from two lists; binding carry-forward: device
  questions 6 and 7 in DEVICE-EVIDENCE are its checkpoint.
- **Source change:** device-validation review, device question D5
  ([review](../openspec/changes/archive/2026-10-16-device-validation/review.md)).

## WHOLE-LIST-TAGS-001 — A whole-list tag on a list the device tags by entry

- **IDs:** device-probe-fixes Test/Challenge S4, S7; Reviewer A5.
- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-17: keep it in the backlog with its strict xfails.
- **Finding and impact:** set input refuses a verb on a list's bare keyword unless the
  XSD marks the list `homogeneous` (probe D5; [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/)). JSON (`"@policy-statement"`) and
  curly input (`protect: policy-statement {`) still carry such a tag, and the set
  writer writes it as `protect policy-options policy-statement`, a line `-v` and the
  device refuse; curly validation takes it. Separately, `deactivate groups` places a
  tag on `groups` that the writers drop without a note.
- **Reproducer:** `{"configuration": {"policy-options": {"policy-statement": [{"name":
  "P1", "then": {"accept": [null]}}], "@policy-statement": {"protect": true}}}}`
  with `-i json -e set`. Pinned by the strict xfail rows of
  `tests/contract/test_every_door.py::TestEveryVerbNamesAStatementPath`
  (`protect-a-list-without-its-entry`, structured doors).
- **Proposed direction:** ask the device whether it ever prints such a tag; if not,
  readers report it and writers drop it with a note, as for per-value tags.
- **Source change:** [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/), Test/Challenge report (S4, S7).

## JSON-NUMBER-IR-001 — The JSON reader keeps a number the set reader keeps as text

- **IDs:** device-probe-fixes Reviewer R2-A2.
- **Status:** open; future work, not selected for implementation. Owner ruling
  2026-10-17: backlog.
- **Finding and impact:** ARCHITECTURE.md section 8 says one configuration has one IR and
  leaf values are strings. The JSON reader keeps a JSON number as an int, the set reader
  keeps the same value as text, so the two IRs differ; set-to-JSON output writes
  `"mtu": "9000"` where a device's JSON holds `9000`. This predates the change.
- **Reproducer:** `junoscfg.convert.to_dict('{"configuration": {"interfaces": {"interface":
  [{"name": "ge-0/0/0", "mtu": 9000}]}}}', "json")` gives `"mtu": 9000`;
  `to_dict("set interfaces ge-0/0/0 mtu 9000", "set")` gives `"mtu": "9000"`. The probe test
  `tests/corpus/test_device_probes.py::TestEveryProbedRenderingReadsAsItsSet` compares the two
  through `_values_as_text`. Device question 11 (DEVICE-EVIDENCE) asks whether the device
  loads a quoted number.
- **Source change:** [device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/), review round 2, advisory R2-A2.

## Consolidated issue inventory

Reconciled on 2026-10-12 against `34bea12` (v0.28.7 plus admission records).
This is the current status destination for the remaining makeover issues,
strict expected failures and roadmap follow-ups. Earlier private TODOs and
archived reviews remain historical evidence, not competing status lists.
The existing YAML-JSON-001 entry above is retained without modification.

Unless an entry says otherwise, **status is open, owner-deferred and not selected
for implementation**. Historical observations must be reproduced on the then-current
release before being treated as current defects. Entries preserve the original
IDs; related IDs share one owning task rather than duplicate implementation work.
Backlog placement does not waive an existing requirement or binding decision.
Private evidence paths below are local provenance only; their contents are not
published here. No new device execution or configuration capture was performed.

### MAKEOVER-13 — Common reader IR and malformed input handling

- **IDs:** ARCH-C09, ARCH-C10, NEW-A2/A3, NEW-C5 (= NEW-B8), DEV-15/19,
  OPEN-18, NEW-R2/R11/R12; makeover #13.
- **Defect/impact:** readers can disagree on numeric/string keys, aliases,
  singleton shapes and universal leaf lists. Historical candidates include
  presence flags represented as `[true]`, YAML dates/non-string keys and a
  non-object `configuration` wrapper causing errors or misleading output.
- **Evidence:** [reader shape regression](../tests/unit/convert/test_convert_api.py),
  [JSON shape qualification gaps](../tests/contract/test_round_trip_validates.py),
  and the historical intake in `private_test_data/makeover-ledger.md`.
- **Source/disposition:** [hidden-list exclusions](../openspec/changes/archive/2026-10-12-hidden-list-names/proposal.md)
  and the owner's reduced-scope deferral in `private_test_data/makeover-deferred-todo.md`.
  Coordinate YAML normalization with YAML-JSON-001; do not silently change consumers.

### value-quoting-by-type/SC1 — Expressions inside bracket lists

- **IDs:** SC1 in value-quoting-by-type; owning task MAKEOVER-13; probe P13.
- **Defect/impact:** the lexer splits a parenthesized expression inside a bracket
  list into words instead of preserving it as one list value.
- **Evidence:** strict expected failure
  `TestStructuredBracketLists.test_an_expression_in_a_bracket_list_is_one_value`
  in [set converter tests](../tests/unit/display/test_set_converter.py).
- **Source/disposition:** [quoting review](../openspec/changes/archive/2026-10-11-value-quoting-by-type/review.md).
  Device evidence exists for the two-value spelling; the owning reader repair
  remains deferred. Preserve complete expression and list order controls.

### MAKEOVER-14 — Metadata traversal and absent targets

- **IDs:** OPEN-4/6/9/11, NEW-C3/C4, DEV-V1 metadata portion; makeover #14.
- **Defect/impact:** metadata on an absent NTP target can create an extra empty
  set statement; an absent hostname target can lose its deactivate command.
  A second securid-server value has a historical malformed-target case.
  Runtime effects of absent-target output are not device-proven.
- **Evidence:** `private_test_data/makeover-work/codex-resumption/leaf-list-deactivation-current/remaining-report.md`
  and its adjacent historical report; P2 distinguishes absent NTP from an
  existing hostname. Diagnosed/unplaced cases should use strict conversion.
- **Source/disposition:** [bounded scalar refusal review](../openspec/changes/archive/2026-10-12-reject-leaf-list-meta-values/review.md).
  Surplus scalar/leaf-list target widening is already fixed in v0.27.0; do not
  reopen it. Broader metadata handling still needs its own compatibility scope.

### MAKEOVER-21b / NEW-R19 — Audit entry keys

- **Defect/impact:** audit/display paths can omit keyword fields from composite
  keys or name the wrong list; users can mistake a finding label for a device path.
- **Evidence:** prepared, parked `codex/audit-entry-key-from-kernel` at `4de5f92`
  retained 30 failing cases and 49 controls; this is preparation, not a fix.
- **Source/disposition:** [audit review F1](../openspec/changes/archive/2026-10-11-audit-key-keywords/review.md).
  The earlier OPEN-12 repair was partial. Rebase/revalidate the prepared change
  before selection; meanwhile verify audit labels against schema-backed conversion.

### MAKEOVER-17 — Grammar boundaries and required values

- **IDs:** OPEN-13, SET-HOLD-TIME-VALUE, KEYWORD-SURPLUS; makeover #17.
- **Defect/impact:** `as-path-neighbors` may be consumed as `as` plus a suffix;
  missing values such as `hold-time down` can be accepted, and valid captured
  lines can be rejected. Surplus nokeyword-enum handling needs evidence.
- **Evidence:** grammar expected failures through
  [the public-door catalogue](../tests/contract/test_every_door.py) and
  [shape catalogue](../tests/support/shapes.py); probe P1 remains a carry.
- **Source/disposition:** [one-line parsing review](../openspec/changes/archive/2026-10-11-structured-one-line-blocks/review.md)
  and the makeover ledger. Obtain path-scoped device evidence before broadening syntax.

### MAKEOVER-18 — Residual schema/model gaps

- **IDs:** OPEN-14 remainder, OPEN-15, NEW-R6; makeover #18; historical
  `control-as-list-type` report.
- **Defect/impact:** untyped empty values can pass silently. The
  device-loaded statements `UNPLACED_IN_THE_EXAMPLE` recorded, native JSON
  `end-range` and `ieee-802.3ad` and the isis-instance singleton were
  reconciled by change device-validation; the device-capture law
  (`tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted`)
  now fails on a new one.
- **Evidence:** [field validation regression](../tests/unit/convert/test_field_validator.py),
  [recorded capture findings](../tests/data/device/expected-findings.json).
- **Source/disposition:** [hidden-list exclusions](../openspec/changes/archive/2026-10-12-hidden-list-names/proposal.md)
  and [XML refactor's separate defect](../openspec/changes/archive/2026-10-09-xml-direct-to-ir/review.md).
  Reproduce historical cases against later keyed-list repairs; a schema validation
  result is not device commit qualification. Keep diagnostics and strict refusal.

### MAKEOVER-18 / NEW-R15 — LRF single-choice names

- **Defect/impact:** `services lrf profile … rule … from application-groups`
  can be unplaced or gain an unwanted `name` keyword. `application-names` shares
  the historical single-choice key issue.
- **Evidence/source:** [hidden-list freeze](../openspec/changes/archive/2026-10-12-hidden-list-names/evidence-freeze.md)
  explicitly excludes NEW-R15: its node lacks the L+nk shape repaired there.
- **Disposition:** keep this distinct from the completed hidden-list fix;
  establish the captured syntax and measure affected slots before repair.

### MAKEOVER-18 / NEW-R18 — Address-shaped typed identifiers

- **Defect/impact:** `--anonymize-ips-in-strings` (also selected by anonymize-all)
  can rewrite an SNMP OID such as `1.3.6.1` as an IP address.
- **Evidence/source:** [embedded-values scenario](../openspec/changes/archive/2026-10-11-anonymize-embedded-values/specs/anonymization/embedded-values/spec.md)
  explicitly retains NEW-R18 for #18; [IP-rule controls](../tests/unit/anonymize/test_ip_rule.py)
  distinguish ordinary IP anonymization from this broader option.
- **Disposition:** owner-policy/model follow-up, not a new privacy-leak claim.
  Preserve current option semantics until the owning rule and migration are decided.

### anonymize-embedded-values/S3 — OSPF area identifiers

- **Defect/impact:** with `--anonymize-ignore-reserved`, an OSPF area list key
  `0.0.0.0` can be rewritten even though it denotes the backbone area.
- **Evidence:** strict expected failure
  `TestTheLeafsTypeAnswers.test_the_backbone_area_is_unchanged_s3` in
  [IP-rule tests](../tests/unit/anonymize/test_ip_rule.py).
- **Source/disposition:** historical S3 policy carry retained by
  [anonymization coverage](../openspec/changes/archive/2026-10-12-anonymization-rule-coverage/review.md)
  and the private deferred-work record. Keep default reserved-address handling
  as the workaround; exact identifier policy requires its owning decision.

### MAKEOVER-19 — XSD fix telemetry and idempotence

- **IDs:** ARCH-C12/C13, NEW-A-X1/X2/X4, KEY_ALIASES NAT entries; makeover #19.
- **Defect/impact:** a fix can report success without mutation or never match a
  release; group-structure changes have historical idempotence concerns.
  Counters alone do not prove applied fixes or correct products.
- **Evidence/source:** registry/build observations and original IDs in
  `private_test_data/makeover-ledger.md`; [schema internals](architecture/schema-internals.md).
- **Disposition:** audit real mutations and repeated application with meaningful
  controls. Historical counts are not current measurements; the SRX feature
  expansion previously declared out of scope is not reopened.
- **device-validation/B2:** Owner ruling 2026-10-16: backlog. Eight registered
  fixes change nothing in the shipped schema: `route-filter-arg`,
  `source-address-filter-arg`, `classifiers-default`, `teardown-forms`,
  `single-hop`, `enable-interface`, `name-freeform`, and `wildcard-star`, which
  matches no element. The shipped `src/junoscfg/validate/data/junos-schema-meta.json.gz`
  records `fixes_applied` 41 of `fixes_registered` 44, so the counter alone does not
  show which fixes changed nothing. B2 is an instance of this entry's first defect,
  "a fix can report success without mutation": `apply_all_fixes` in
  `src/junoscfg/validate/xsd_fixes.py` counts each fix that reports success, and
  checks no change. To check one fix, apply it alone to the parsed tree and compare
  the tree before and after. Interim behaviour, kept: the eight stay registered.
  Source: [device-validation review](../openspec/changes/archive/2026-10-16-device-validation/review.md), backlog candidate B2.

### DEVICE-EVIDENCE — Remaining narrow probes and hidden names

- **IDs:** P1/P6/P7/P8 carries, OPEN-22 (QFX tunnel), DEV-V6 (P5).
- **Defect/impact:** QFX `interfaces … unit 0 tunnel encapsulation`, daemon-process
  syntax and residual hello-padding names lack sufficient positive qualification.
  Whether a one-line `within N trigger after 1` loads equivalently to device
  display-set output remains unresolved.
- **Evidence/source:** [hidden-list review](../openspec/changes/archive/2026-10-12-hidden-list-names/review.md),
  [keyword review](../openspec/changes/archive/2026-10-12-keyword-leaves-keep-keyword/review.md),
  [known differences](../tests/data/device/known-differences.json).
  The remaining `xml-element-name-leak` and `trigger-after-one-line` classes
  must not be dismissed as formatting. Other classes marked equivalent/device
  quirk are not automatically product defects.
- **device-validation/B1:** Owner ruling 2026-10-16: backlog. The rest of
  `xml-element-name-leak`: from XML or JSON, an element the CLI hides appears in the
  set path (`rf_list`, `server-group server-group`, `other-variables`,
  `bridge-domains domain`, `dynamic-tunnels dynamic-tunnel`; the class definition in
  `tools/device_differences.py`). These are hidden list names, not renames, so
  device-validation's rename rule does not cover them. They show only in private
  captures: no line of `tests/data/device/known-differences.json` holds the class at
  716a9d1. Interim behaviour, kept: the tool keeps the class as a `defect`. Source:
  [device-validation review](../openspec/changes/archive/2026-10-16-device-validation/review.md), backlog candidate B1.
- **device-probe-fixes questions** ([device-probe-fixes](../openspec/changes/archive/2026-10-17-device-probe-fixes/), review): the next probe asks, paths only,
  in `configure private`, never committed: (1) `delete policy-options community
  JUNOSCFG-C1 members 64496:2` after two `members` lines; (2) `delete system apply-groups
  JUNOSCFG-G` with the group defined; (3) `delete policy-options policy-statement` with one
  policy defined; (4) `deactivate routing-options static route 198.51.100.0/24 description
  JUNOSCFG-PROBE` (a scalar value after a verb); (5) `set groups JUNOSCFG-G interfaces <*>
  hold-time down 0` with no `apply-groups`, then `commit check`; (6) `deactivate system
  login user` and `deactivate routing-options static route` (lists not marked homogeneous)
  with entries defined, and more lists of that kind; (7) `deactivate system name-server`,
  `deactivate firewall family inet filter F term T from source-prefix-list` (homogeneous)
  and more of that kind, with display set, JSON and XML; (8) `set interfaces ge-0/0/1
  hold-time up 0 down 0`, then `show interfaces ge-0/0/1 | display set`; (9) `show system
  dump-on-panic | display json` after `set system dump-on-panic`; (10) `load merge json` of
  `"@community": [null, {"inactive": true}]` beside two community values under the probe
  route; (11) `load merge json` of grpc `"clear-text": {"port": "32767"}` with the number
  quoted, as junoscfg writes it; (12) `deactivate interfaces ge-0/0/1 unit 0 tunnel
  encapsulation` with a tunnel encapsulation defined (no answer recorded for
  `deactivate7.in`), and `deactivate firewall family` with a filter defined, a `family` outside
  `interfaces`: refused as `deactivate … unit 0 family` is? `-v` refuses both today (review
  R2-A1). Questions 6 and 7 are the checkpoint of the owner ruling
  on review S-6 (the `homogeneous` reading, VERB-PREFIX-001).
- **Disposition:** request only the named set/JSON/XML subtrees and needed load
  results; retain platform qualifications and private probe provenance.

### value-quoting-by-type/SC2 — Backslash literal compatibility

- **Defect/impact:** broad quoted-value round trips still fail for backslashes.
  P11 supports some internal spellings but rejects its trailing-backslash form.
- **Evidence:** two strict expected failures in
  [value formatting tests](../tests/unit/display/test_value_format.py).
- **Source/disposition:** [quoting review](../openspec/changes/archive/2026-10-11-value-quoting-by-type/review.md).
  Separate supported device spellings from compatibility assumptions; do not
  relax value/escape preservation to make the general round-trip law pass.

### posix-bracket-escape/F1 — Unshipped malformed pattern policy

- **Status:** open owner decision; recorded interim action remains effective.
- **Defect/impact:** the POSIX translation repair preserves shipped pattern
  programs but changes behavior for unterminated `^[[:alpha:]$` and bare
  `[:alpha:]` shapes in other potential schemas.
- **Evidence/source:** [F1 specification challenge](../openspec/changes/archive/2026-10-11-posix-bracket-escape/review.md).
  Its pending decision is separate from T5's completed shipped-pattern sweep.
- **Disposition:** decide the malformed/custom-pattern contract before claiming
  general equivalence; do not retroactively mark the interim ruling final.

### OPEN-10 — Retire deprecated conversion and validation doors

- **Defect/impact:** deprecated `SetConverter.to_set` and structured-validation
  methods cannot provide all supported schema-aware semantics. Unsafe terminal
  tags now fail safely; five retained expected failures are not complete support.
- **Evidence/source:** [original deprecation](../openspec/changes/archive/2026-10-11-structured-one-line-blocks/review.md)
  and [bounded terminal refusal](../openspec/changes/archive/2026-10-12-reject-deprecated-tagged-statements/review.md).
- **Disposition:** carry the existing removal/migration obligation under beta
  compatibility rules; use `convert_config` and public `validate_structured`.
  Backlog placement does not postpone a binding removal policy without a ruling.

### MAKEOVER-T1 — Complete captured-format qualification

- **Defect/impact:** existing corpus checks do not qualify every capture against
  every supported non-XML output; partial passing cases do not prove the matrix.
- **Evidence/source:** [device corpus](../tests/corpus/test_device_rule_values.py),
  [anonymization coverage scope](../openspec/changes/archive/2026-10-12-anonymization-rule-coverage/review.md)
  and T1 `oracle-every-format` in the private makeover ledger.
- **Disposition:** add the complete matrix with exact diagnostics/known-difference
  dispositions. XML cells remain gated by the separate XML work below.

### MAKEOVER-T2 — Full-capture IR and round trips

- **Defect/impact:** fragment tests do not establish full-capture equality,
  meaningful ordering and multiplicity across readers and writers.
- **Evidence/source:** [shape catalogue](../tests/support/shapes.py),
  [round-trip laws](../tests/contract/test_round_trip_validates.py), and T2
  `oracle-one-ir` in the private makeover ledger.
- **Disposition:** define per-contract equivalence with independent negative
  controls; coordinate MAKEOVER-13 and YAML-JSON-001 without normalizing away defects.

### MAKEOVER-22b — Documentation and hook guidance

- **IDs:** NEW-C8, NEW-C14; makeover #22b.
- **Defect/impact:** historical path-filtering guidance and the mypy-hook comment
  may describe obsolete behavior; documentation and cosmetic/performance carries
  were not part of the reduced makeover completion.
- **Evidence/source:** [original documentation correction](../openspec/changes/archive/2026-10-11-docs-corrections/proposal.md)
  and the private deferred-work record.
- **Disposition:** check current guidance before editing: later mypy/workflow
  changes may already supersede the historical wording. Do not blindly restore
  the old assertion that mypy is merely reported in CI; record actual behavior.

### XML-INPUT — Qualify XML input and its IR

- **IDs:** XML input scope, MAKEOVER-13 XML portion, NEW-A-S3 XML portion.
- **Defect/impact:** unresolved metadata, whitespace, names, aliases and singleton
  shapes leave XML input BUGGY and unqualified, although the API is available.
- **Evidence/source:** [public XML scope](roadmaps/xml-work-todo.md) and
  [owner-approved deferral](../openspec/changes/archive/2026-10-12-xml-status-and-todo/proposal.md).
- **Disposition:** retain existing tests; record each actual defect with exact
  bounded input/result/evidence. Passing isolated controls or historical repairs
  do not qualify the complete surface.
- **device-validation/B3:** Owner ruling 2026-10-16: backlog. `-v` on XML input
  needs a cleaned XSD, and none ships. `junoscfg convert -v -i xml FILE` on
  `<configuration><system><host-name>r1</host-name></system></configuration>` exits
  3 with "XSD not found in …/src/junoscfg/validate/data. XML validation requires a
  cleaned XSD artifact." Interim behaviour, kept: that error, as
  [the validation guide](guide/validation.md#xml) warns. Source:
  [device-validation review](../openspec/changes/archive/2026-10-16-device-validation/review.md), backlog candidate B3.

### MAKEOVER-23 / OPEN-17 — XML output

- **Defect/impact:** XML output is unimplemented and raises `NotImplementedError`.
- **Evidence/source:** [XML scope](roadmaps/xml-work-todo.md) and
  [compatibility decision](decisions/2026-10-09-scope-compatibility-to-production-consumer.md).
- **Disposition:** explicitly deferred feature. Reconcile accepted scope and
  import bans before design and device-backed acceptance; this entry does not
  lift the ban or authorize implementation.

### XML-QUALIFICATION — XML device matrix and full IR loops

- **IDs:** XML portions of T1/T2.
- **Defect/impact:** XML is not qualified alongside every captured format or over
  full-capture reader/writer loops.
- **Evidence/source:** [XML roadmap](roadmaps/xml-work-todo.md) and the
  [deferral review](../openspec/changes/archive/2026-10-12-xml-status-and-todo/review.md).
- **Disposition:** preserve meaningful order, multiplicity, metadata and values
  with independent negative controls after the owning XML repairs are selected.

### MAKEOVER-24 / OPEN-7 — Set edit-command features

- **IDs:** OPEN-7 feature half, NEW-C9/C10; makeover #24.
- **Defect/impact:** `annotate`, `insert`, `replace pattern` and broader edit-script
  support are not implemented as configuration-input features.
- **Evidence/source:** [explicit rejection repair](../openspec/changes/archive/2026-10-12-unsupported-set-commands-reported/proposal.md).
- **Disposition:** owner deferred implementation and accepted explicit errors.
  Keep #15 closed; request ordinary display-set configuration as the workaround.

### READERSHIP — Observe OpenSpec artifact use before removal

- **Defect/impact:** without a release observation, there is no measured basis
  for deleting supposedly unread artifact types or claiming reduced overhead.
- **Evidence/source:** [simplification roadmap item 7](roadmaps/2026-10-08-junoscfg-simplification.md)
  and [observation protocol](how-to/observe-openspec-readership.md#observe-openspec-artifact-readership-for-one-release).
- **Disposition:** retain the v0.14.0 baseline/protocol and verify whether the
  required release window has usable observations. Missing records remain
  UNMEASURED, not zero readers; propose removal only from actual evidence.

## Reconciled closures — do not reopen as ordinary backlog

- **Schema-run cost/trigger TODO:** addressed after the makeover by
  [streamlined qualification](../openspec/changes/archive/2026-10-12-streamline-schema-qualification/review.md)
  (v0.28.3), [dependency trigger reduction](../openspec/changes/archive/2026-10-12-reduce-schema-qualification-triggers/review.md)
  (v0.28.4), [synthetic generator coverage](../openspec/changes/archive/2026-10-12-synthetic-schema-check/review.md)
  (v0.28.5), [complete test selection](../openspec/changes/archive/2026-10-12-test-selection-completeness/review.md)
  (v0.28.6), and [tooling fixture performance](../openspec/changes/archive/2026-10-12-test-tooling-performance/review.md)
  (v0.28.7). Further improvements need a new concrete finding.
- **Reduced makeover completion:** #10/#11/#12, T3/T4/T5, #15/#16, scalar
  target-widening refusal, deprecated terminal-tag refusal and the narrow schema
  parity assertion correction are completed. Historical planning rows calling
  them open/prepared are superseded by their releases and completion report.
- **Final makeover schema evidence:** the selected 25.2 qualification passed;
  old per-change notes saying it was still pending are historical. Neither that
  result nor newer optimization work qualifies the deferred XML surface.
