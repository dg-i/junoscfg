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

- **Status:** open; future work, not selected for implementation.
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

- **IDs:** OPEN-14 remainder, OPEN-15, UNPLACED_IN_THE_EXAMPLE, NEW-R6;
  makeover #18; historical `control-as-list-type` report.
- **Defect/impact:** device-loaded statements can be unplaced or rejected by the
  model. Untyped empty values can pass silently. Native JSON `end-range`,
  `ieee-802.3ad` and singleton model shapes need owning-layer reconciliation.
- **Evidence:** [field validation regression](../tests/unit/convert/test_field_validator.py),
  [round-trip validation gaps](../tests/contract/test_round_trip_validates.py),
  [device evidence catalogue](../tests/support/devices.py).
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
