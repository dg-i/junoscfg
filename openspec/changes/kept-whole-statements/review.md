## Findings

### Independent Test/Challenge (phase 4, STOP-T)

A fresh, context-isolated agent ran on `55ec2b2` (merge base `f0bb6aa`); its
report is copied to `test-challenge.md`, its probes are in
`private_test_data/makeover-work/kept-whole-statements/roles/`. The orchestrator
relayed the rulings of 2026-10-11: every finding accepted. Disposition, all in
the phase-5 commit:

1. F1 (high), C7 forced a regression on device XML: `<description></description>`
   and `<host-name/>` read alike, so reporting the XML door refused the device's
   own `description ""`. Ruling: fix A. `display/to_yaml.py` `_xml_leaf` reads an
   empty element of a leaf the tree says takes a value as `""`, the spelling the
   device writes in set and JSON for the same statement
   (`tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.{set,json,xml}.gz`).
   XML left `TestALeafWithoutItsValueIsUnplaced._SOURCES`;
   `test_an_empty_xml_leaf_is_the_empty_value` (both spellings) converts,
   strict-converts and anonymizes a device-like unit. `tools/device_differences.py`
   lost the `xml-empty-value-lost` rule and the regenerated record its 4 lines.
2. F2 (high), the public `anonymize()` had no refusal: `anonymize()` raises
   `ValueError` on any non-empty `junoscfg:unplaced` record, naming a count only;
   the pipeline's refusal now withholds the statement's text as well.
   `TestAKeptStatementIsRefused` covers a set-read and a JSON-read record, the
   no-rule case and the conversion message.
3. F3 (high), verbatim writers could print lines a record never held:
   `display.unplaced_record_problem()` (on the curly lexer's own tokens,
   `display.set_converter.reads_as_one_statement`) refuses a line break, a tab, a
   stray space, an unbalanced or inner quote, an unquoted `;`, `{`, `}` or `[`, or
   a comment, on read (`convert.input.to_dict`), in the set and structured
   writers, and in the set reader. `TestARecordOfKeptStatementsIsInput` holds the
   13 negative texts for JSON and YAML, the writer refusal, one validation report,
   and the line-count bound.
4. F4 (medium), C6's rationale was false and a record could arrive malformed:
   rationale corrected in `instruction-integrity.md` and the constant's comment;
   wrong shapes (string, list, number, a value, a non-mapping tag) are refused on
   read; `test_the_record_name_in_the_input_forges_nothing` covers
   `set system junoscfg:unplaced host-name` and a placed `ietf-netconf-acm:nacm`.
5. F5 (medium), `edityaml` `*` and glob segments now skip the record
   (`TestAWildcardSkipsTheRecordOfKeptStatements`).
6. F6 (medium), weaker implementations: quote cases `"abc"`, `""`,
   `"alpha  beta"` and an escaped quote; two kept statements give two reports;
   the presence leaf `no-redirects` as `null`, `[null]`, `true` and set is clean;
   a value-less leaf as JSON `[null]`, `true` and `[]` is reported.
7. F7 (low), coverage: a YAML source on the quote row (single-quoted keys with
   `"` and `!`); revert (`TestARecordOfKeptStatementsPassesRevert`), audit
   (`TestARecordOfKeptStatements`) and CLI (`TestAKeptStatementOnTheCommandLine`)
   cases. Line order is layout: the rows pin lines with `written`, the unit tests
   compare sorted lines.
8. F8 (low), C5 recorded below as a specification challenge; the negative
   siblings are `test_a_kept_sibling_leaves_the_placed_node_alone`.

Also removed from the acceptance tests, without evidence to keep it: a bare
`set apply-macro` beside a placed macro. `apply-macro` is in the tree as a list
keyed by `name`, so its bare keyword takes the generic bare-list path (the
device's own `snmp filter-interfaces interfaces`); whether the device rejects it
is unprobed, and it is not one of this change's IDs.

### Fresh Reviewer (phase 6, STOP-R)

A fresh, isolated Reviewer read the freeze, the delta, the touched contracts, the
Test/Challenge record, the tests and the diff `f0bb6aa..f8ea357` (`f52838a`
records only), with base runs from a `git archive` of `f0bb6aa`; probes `rv_*` in
`private_test_data/makeover-work/kept-whole-statements/roles/`. Verdict:
**CHANGES REQUIRED** (R1 and R2 blocking, R3 fix or carry-forward, R4–R7 low).
Every figure reran and matched: `known-differences.json` regenerated
byte-identical (928 lines, 17 to 16 classes); the reproductions fixed on head;
the value-less-leaf radius 12 to 0; identical `UNPLACED` counts on base and head
over 37 device captures and 1,699 JVD files (79,873 each); the 57 delta test ids
collect. Rulings relayed by the orchestrator on 2026-10-11, dispositions:

1. R1 (high), second answer at the anonymization boundary: the pipeline refuses
   every `UNPLACED` statement, the public `anonymize()` only a non-empty record, so
   a 0.16.1 joined key (`"bogus 203.0.114.9 G-SECRET": [null]`) or an unknown leaf
   from JSON passes it with its values (`rv_public_anon.out`; the base has the same
   gap). Ruling: carried forward, not fixed here; owner answer 5 governs unknown
   paths (anonymize IP-shaped values by pattern and warn), change 5
   `anonymize-every-placed-value`, ledgered NEW-R5. The claims are narrowed to the
   record (proposal, delta, `anonymize/CONTRACT.md`, the test class docstring);
   the specification challenge is below.
2. R2 (medium), the migration note was false for JSON and YAML 0.16.x wrote from
   XML (`"description": [null]` is now reported): fixed in `.openspec.yaml`
   (`consumer` and `cli` migrations) and the removal changelog fragment: regenerate
   from the XML or write `""`.
3. R3 (medium), `""` on a leaf whose type refuses it passed silently on every door
   (`<host-name/>`, `<mtu/>`, `<root-login/>`; the skip in `_validate_leaf`): fixed
   at field validation, which now checks `""` like any value. `TestAnEmptyValueIsCheckedLikeAnyOther`
   (XML host-name, family-inet mtu, enum; JSON and set) and `description ""` clean
   on three doors; `TestStructuralValidation::test_empty_value_skipped`, which pinned
   the skip with a `uint16` leaf, became `test_an_empty_value_is_checked_by_its_type`.
   Radius (`empty_radius.py`, 1,775 device and JVD files): no new error. Not
   covered: a leaf the tree gives no type (`interfaces interface mtu`, 103,217 such
   leaves), carried forward as a schema-model gap (change 18).
4. R4 (low), the record accepted an unquoted `]` the set reader refuses: the record
   check now applies `junoscfg.input.find_unsupported_set_brackets`, one rule with
   the set reader; negative texts `bogus ]` and `bogus <[gx]e-*>`. Refusal radius
   over 1,716 files still 0.
5. R5 (low), an empty record (written `[null]`, refused on read) and a tag with no
   meta command were accepted: both refused (`unplaced_record_problem`), with tests.
6. R6 (low), stale freeze lines on DEV-16: amended, recorded in the delta log.
7. R7 (nit), a tagged statement counted twice in the `anonymize()` refusal: the
   count is of statements now (`test_a_tagged_statement_counts_once`).

Carry-forwards: NEW-R5 (R1) and NEW-R4 (the set reader's bracket refusal prints
the original line, also in an anonymized run; pre-existing), both change 5; the
untyped-leaf gap of R3, change 18.

## Already provided

- `display.set_converter._TOKEN`, the curly lexer, decides what reads back as one
  statement; the record check uses it rather than a second tokenizer.
- `convert.field_validator.UNPLACED` and the pipeline's `_refuse_unplaced` carry
  the report and the conversion's refusal; the record adds no new mechanism.

## Specification challenges

### C5: a valid statement after a bare keyword is placed, not kept

- Artifact: `openspec/specs/conversion/entry-keys/spec.md`, requirement "A statement the reader cannot complete is kept whole", and its tests `TestApplyGroups::test_a_group_after_a_bare_one_is_kept_too` and `TestTokensTheReaderCannotPlaceAreKept::test_a_keyed_entry_after_a_bare_keyword_is_kept_too`.
- Counterexample: executed on `f0bb6aa`: `set apply-groups` then `set apply-groups G1` gives IR `{"apply-groups": true, "apply-groups G1": true}`, and both lines are reported `UNPLACED`; the same for `as-path-neighbors` bare then `as-path-neighbors as-list SAMPLE-AS-LIST`. The approved requirement text never says the valid line is kept; only the two test names pinned it, a side effect of the kept key sharing the placed node's name. The device loads `apply-groups G1` and rejects only the bare line (corpus `CORRECTLY_REJECTED`).
- User impact: a valid group or entry is reported as not placed, so `--strict` fails and anonymization refuses a configuration for a line it could place, and the audit misses the group.
- Proposed correction: the delta places the valid statement and keeps only the bare one, in either order; the two tests are renamed `..._is_placed` and assert one report; the main spec's `Tests:` line names the new ids.
- Decision: Pending owner decision. Interim action: the delta and tests as proposed (the valid statement is placed, the bare one kept and reported), which is reversible by restoring the two tests and the shared key (owner intake 2026-10-11: merge with recorded interim action).

### R1: the public `anonymize()` refuses only the record

- Artifact: delta `specs/conversion/entry-keys/spec.md`, "`junoscfg.anonymize.anonymize()` SHALL refuse an IR whose record holds a statement".
- Counterexample: executed by the Reviewer (`rv_public_anon.out`): a 0.16.1 joined key `"bogus 203.0.114.9 G-SECRET": [null]` and an unknown leaf `"bogus-peer": "203.0.114.9"` read from JSON pass `anonymize(ir, AnonymizeConfig(ips=True, groups=True))` with `203.0.114.9` and `G-SECRET` intact; the pipeline refuses both. The base behaves the same.
- User impact: a library caller who anonymizes migrated or hand-written JSON or YAML publishes original addresses and names.
- Proposed correction: "`anonymize()` SHALL refuse an IR holding any statement that field validation reports `UNPLACED`, naming none."
- Decision: Pending owner decision. Interim action: the record is refused by anonymize(); the general unknown-key rule is change 5 (NEW-R5) per owner answer 5.

## Verdict

CHANGES REQUIRED at f8ea357 (fresh Reviewer); R2–R7 fixed and R1 carried forward with its challenge recorded, in the review-fix commit. Pending the same Reviewer's confirmation.
