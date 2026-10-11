# Working ledger of the nightly makeover run (2026-10-11, base a19e978)

The inventory every change of the run works from, carried by the run's first
change. Revalidated on `a19e978`. Synthetic values only (`AGENTS.md` test-data
table); a capture is named by its committed path under `tests/data/device/`
(vmx = `synthetic/vmx-23.2R2-S7.5`, qfx = `synthetic/qfx5120-25.2R2-S1.5`, jvd =
`jvd/vmx-23.2R2-S7.5`), an unanswered device probe by its number in the run's
probe list (P1–P5). "Change" is the run's change number and slug. Status words:
OPEN, FIXED_ALREADY, INTENTIONAL, DUPLICATE, EVIDENCE_BLOCKED,
OUT_OF_SCOPE_FEATURE (the owner took XML output and annotate/insert/replace into
scope: FEATURE).

Changes: 1 structured-one-line-blocks · 2 json-writer-pure · 3
kept-whole-statements · 4 universal-statements-from-tree · 5
anonymize-every-placed-value · 6 group-wildcards-pass · 7
anonymize-embedded-values · 8 value-quoting-by-type · 9 xml-leaf-text-verbatim
· 10 keyword-leaves-keep-keyword · 11 keyed-single-entry-lists · 12
hidden-list-names · 13 one-ir-at-reader-boundary · 14 meta-commands-one-walker
· 15 unsupported-set-commands-reported · 16 diagnostics-load-vs-commit · 17
grammar-keyword-boundaries · 18 schema-model-gaps · 19 xsd-fix-telemetry · 20
posix-bracket-escape · 21 audit-key-keywords · 22 docs-corrections · 23
xml-output · 24 set-edit-commands.

Verification to close, for every OPEN row: a regression test that fails on the
merge base and passes after, every affected door and format checked, a negative
case, the device law unchanged or losing only the classes the fix explains, the
full check, a fresh review. The last column adds what is specific to the row.

## Conversion, tags and input loss

| ID | Source | Reproduction / test node | Status | Impact | Owning layer | Formats / doors | Device evidence | Change | Also to close |
|---|---|---|---|---|---|---|---|---|---|
| OPEN-1 (=NEW-A1) | mission conv. 1 | `system { host-name router1; }` on one line; `a; b;` on one line; `} interfaces {` | OPEN | silent total loss, wrong configuration | `display/set_converter.py` lexer | structured input: convert, validate, audit | none needed (lexical) | 1 | non-empty input yielding nothing is a diagnostic |
| NEW-B6 | inventory B | `host-name r1; ## note; see` | OPEN | wrong configuration | curly lexer | structured input | none needed | 1 | `/* a; b */` too |
| DEV-18 | device findings 18 | curly `system { /* OMITTED */ };` | OPEN | invalid output | curly lexer | structured input | vmx, qfx `.conf` (class `omitted-block-emitted`) | 1 | warning, class gone via the tool |
| OPEN-10 | strict xfails `test_set_converter.py` (3) | `inactive: route 10.98.0.0/16 reject;` through `to_set()` | OPEN | wrong configuration (secondary door) | `SetConverter.to_set()`, its caller `validate/structured_validator.py` | `to_set()`, `validate_structured` | vmx `.set` (tag on the path) | 1 | deprecated; xfails until removal |
| EMPTY-BLOCK | Test/Challenge F2 (change 1) | curly `protocols { lldp { } }` reads as nothing; `lldp;` gives `set protocols lldp` | EVIDENCE_BLOCKED | possible silent loss of a presence statement (now reported as a warning) | curly lexer | structured input | missing: P6 | 1 (warning), decision after P6 | |
| SET-HOLD-TIME-VALUE | Test/Challenge F1 (change 1) | `validate_set("set interfaces ge-0/0/0 hold-time down")` is valid | OPEN | false acceptance (set door) | grammar merged rule (`hold-time` takes a value) | set validation | none (schema: `down` takes an unsignedInt) | 17 | curly doors already reject it (change 1) |
| STMT-ACROSS-LINES | Reviewer R2 (change 1) | curly `host-name\n router1;` refused (as on the base) | EVIDENCE_BLOCKED | possible false rejection of hand-written curly | curly lexer | structured input | missing: P7 | 1 (corpus heuristic kept), decision after P7 | |
| CURLY-UNQUOTED-WILDCARD | Reviewer carry-forward (change 1) | curly `interfaces { <ge-0/0/*> { … } }` unquoted is refused (`/*` opens a comment); refused on the base too | EVIDENCE_BLOCKED | possible false rejection | curly lexer | structured input | device prints `<xe-0/0/1*>` unquoted; missing: a probe of `<ge-0/0/*>` | after a probe | |
| NEW-B5 | inventory B | curly `hold-time up 2000 down 0;` through `validate_structured` | OPEN | false rejection | structured validation | every structured validation door | vmx curly one line, display set two lines | 1 | every door agrees |
| OPEN-2 | mission conv. 2 | `set apply-groups G1` + bare `set apply-groups` | OPEN | silent loss, false UNPLACED | `convert/input/set_input.py` `_keep_whole` | set input | device rejects the bare line (corpus) | 3 | |
| NEW-C1 | inventory C | `set system host-name router1` + `set system host-name` | OPEN | silent loss, invalid output | set reader value-less leaf | set, curly input | corpus `CORRECTLY_REJECTED` | 3 | |
| OPEN-3 | mission conv. 3 | `apply-macro 12345 "A B" balks X` | OPEN | invalid output | `_keep_whole` quote loss | set, curly input | probe round 5 | 3 | |
| OPEN-4 | mission conv. 4 | `deactivate apply-groups G1 G2` | OPEN (root of OPEN-9) | wrong configuration | `_apply_meta` | set input | leaf-list value rejected (round of 2026-10-10) | 14 | |
| OPEN-5 | mission conv. 5 | second `securid-server` entry + `deactivate` | DUPLICATE of OPEN-21 | invalid output | keyed `h` container | all | as OPEN-21 | 11 | |
| OPEN-6 | mission conv. 6 | `deactivate system ntp` alone | EVIDENCE_BLOCKED | wrong configuration if refused | `_apply_meta` creates nodes | set input | missing: P2 | 14 | |
| OPEN-7 | mission conv. 7 | `annotate`, `insert`, `replace pattern`, typos | OPEN + FEATURE | silent loss | `set_to_dict` dispatch | set input | annotate JSON shape in vmx | 15 (report), 24 (feature) | reader and validator share one vocabulary |
| OPEN-8 | mission conv. 8 | XML `protect="protect"` | FIXED_ALREADY | — | `display/to_yaml.py` | XML input | — | — | shape rows `tests/support/shapes.py` |
| OPEN-9 | mission conv. 9 | `deactivate ... members 64496:1` | OPEN | wrong configuration, false acceptance | `_apply_meta`, set validator | set input, validation | leaf-list value rejected | 14 | |
| OPEN-11 | mission conv. 11 | `_apply_meta` re-walks `_merge_tokens` | OPEN | architecture-only | set reader | set input | — | 14 | one walker |
| OPEN-12 | mission conv. 12 | audit paths of `virtual-link` keys | OPEN | invalid audit scripts | `audit/walker.py` `_key_tokens` | audit CLI | keys without keywords rejected (door row) | 21 | |
| NEW-C3 | inventory C | `validate_set` of the device's `protect` lines | OPEN | false rejection | `validate/set_validator.py` | set validation | vmx `.set` | 14 | |
| NEW-C4 | inventory C | `validate_set("deactivate system host-name")` | OPEN | false rejection and acceptance | set validator meta lines | set validation | vmx `.set` | 14 | |
| NEW-C9, NEW-C10 | inventory C | curly `/* note */`; JSON `comment` to set | FEATURE (documented loss) | silent loss | readers and writers | structured, set | vmx comments | 24 | |

## Grammar, schema and validation

| ID | Source | Reproduction / test node | Status | Impact | Owning layer | Formats / doors | Device evidence | Change | Also to close |
|---|---|---|---|---|---|---|---|---|---|
| OPEN-13 | strict xfail `test_every_door.py` bare keyword (5) | `... from as-path-neighbors` | OPEN | false acceptance | `validate/grammar_generator.py` keyword terminals | set validation | bare forms rejected (probe rounds) | 17 | corpus: no new rejection |
| KEYWORD-SURPLUS | mission high-impact 3 | `... transit-area 0.0.0.2 EXTRA` | EVIDENCE_BLOCKED | wrong configuration | `display` `enum_is_fragment`, set walker | set, curly, validation | missing: P1 | 17 after P1 | |
| OPEN-14 | corpus `--device-grammar` | 66 device lines rejected | OPEN | false rejection | keyed containers (56), schema gaps (8), name (1), escape (1) | set validation | the lines themselves | 11, 18, 12, 8 | |
| OPEN-15 | strict xfails `test_round_trip_validates.py` (4), `test_field_validator.py` (1) | the example's schema and field errors | OPEN | false rejection | schema gaps, reader aliases, keyed containers | JSON/YAML schema, field validation | vmx, qfx | 18, 13, 11 | `UNPLACED_IN_THE_EXAMPLE` emptied |
| OPEN-16 | mission valid. 16 | `radius-server 10.0.0.9 timeout 10` without `secret` | OPEN | inconsistent diagnostics | `convert/field_validator.py`, `convert/__init__.py` | convert, CLI | loads without `secret` | 16 | |
| NEW-C2 (=NEW-B7) | inventory C | warnings dropped unless an error exists | OPEN | lost diagnostic | `convert/__init__.py` | convert, CLI | — | 16 | |
| DEV-V3 | device ledger | "Missing mandatory field 'secret'" | OPEN | misleading diagnostic | field validator wording | all | load OK, commit needs it | 16 | |
| OPEN-17 | mission valid. 17 | `to_format=XML` raises | FEATURE (owner: in scope) | — | `convert/output`; decision lifting the ban | convert, CLI | device XML of every capture | 23 | decision record first |
| DEV-V1 | device ledger | `protect` lines, `\"`, quoted wildcard group | OPEN (protect, escape); FIXED_ALREADY (wildcard group) | false rejection | set validator, `QUOTED` terminal | set validation | vmx, qfx `.set` | 14 (meta), 8 (escape) | |
| DEV-V5 (=NEW-A4) | device ledger | `FutureWarning: Possible nested set` | OPEN | cosmetic | `convert/field_validator.py` `_posix_to_python_re` | every validating door | — | 20 | warnings as errors |
| DEV-V6 | device ledger | `within 1800 trigger after 1` | EVIDENCE_BLOCKED | none known (class `open`) | `fd` flag | set output | missing: P5 | after P5 | |
| DEV-V7 | device ledger | quoted `$junos-...` | INTENTIONAL | cosmetic (class `equivalent`) | `display/value_format.py` | all | device loads both | — | |
| NEW-C7, NEW-C8, NEW-C14 | inventory C | stale examples and tooling comments | OPEN | cosmetic | docs, `.pre-commit-config.yaml` | docs | — | 22 | |

## Anonymization

| ID | Source | Reproduction / test node | Status | Impact | Owning layer | Formats / doors | Device evidence | Change | Also to close |
|---|---|---|---|---|---|---|---|---|---|
| ANON-1..5 | anonymizer bug list | 11 cited tests under `tests/unit/anonymize/` pass | FIXED_ALREADY | — | `anonymize` | all | — | — | keep regressions |
| ARCH-C05 | mission high-impact 1 | `unknown-knob: 203.0.114.9` under a BGP group | OPEN | data leak | `anonymize/walker.py` (`child_schema is None`) | library and pipeline | none needed | 5 | owner: lexical IP pattern + warning naming the path |
| ANON-P1 (=NEW-C13) | strict xfails `test_every_rule.py` (2) | groups + sensitive word on `apply-groups` | OPEN | wrong configuration, revert failure | `anonymize/__init__.py`, `rules/group.py` | all | — | 5 | |
| ANON-P2 | strict xfails `test_integration.py` `MISSED` (2) | values left by every rule in the example | OPEN | data leak | IP typing, walker coverage | all | vmx | 5 | `MISSED` empty |
| NEW-R1 | Reviewer re-review (change 1) | `junoscfg convert -v --anonymize-all` on input with an invalid statement prints `Invalid syntax: set system bogus-statement 203.0.114.9` | OPEN | data leak (validation errors before anonymization; same on the base) | CLI `-v` with anonymization | CLI | none needed | 5 | |
| NEW-A-N1, N2, N3, N6 | inventory A | nested universal statements, transparent siblings, host types | OPEN | data leak | `anonymize/walker.py`, `rules/ip.py` | all | — | 5 | |
| NEW-A-S2 | inventory A | transparent-container siblings in field validation | OPEN | false rejection, silent acceptance | `convert/field_validator.py` | all, strict | — | 5 | |
| NEW-C11 | inventory C | interface-range description, tacplus addresses | DUPLICATE of ANON-P2 | data leak | as ANON-P2 | all | vmx | 5 | |
| ANON-P3 (=NEW-C12) | strict xfail `test_a_wildcard_group_name_passes_the_group_rule` | `group <*>` rewritten | OPEN | wrong configuration | `rules/group.py` | all | vmx `.set` | 6 | |
| ANON-P4 | strict xfail `test_the_mapping_restores_the_set_output` | `\"` in a description | DUPLICATE of DEV-7 | invalid output | `display/value_format.py` | set, curly output | vmx, qfx | 8 | |
| ANON-P5, NEW-A-N4, N5, N7 | mission evidence item; inventory A | IP and user in `scp://` values; substring revert; `apply-path` group | OPEN | data leak, wrong revert | `anonymize` embedded values, `revert.py` | all, revert | — | 7 | |

## Device oracle

| ID | Source | Reproduction / test node | Status | Impact | Owning layer | Formats / doors | Device evidence | Change | Also to close |
|---|---|---|---|---|---|---|---|---|---|
| DEV-1 | findings 1 | `transport-class name gold color 4000` + `bronze` | OPEN | silent loss | `dict_walker._entry_key` fallback | set, curly output | vmx, qfx, jvd (`transport-class-dict`) | 11 | |
| DEV-2, DEV-3, NEW-A-S1, NEW-B2 | findings 2, 3; inventories | `overload timeout 300`, `radius-server ... timeout 10` | OPEN | invalid output, silent loss | `validate/xsd_fixes.py` `_fix_positional_keys` | set, curly output | vmx, qfx, jvd | 10 | classes `overload-timeout-dropped`, `radius-timeout-dropped` gone |
| NEW-B3 | inventory B | `otn-options trigger oc-los hold-time up 100` | OPEN | silent loss | `_fix_flat_dict_elements`, `_emit_flat_dict` | set, curly output | — | 10 | |
| DEV-4..7, NEW-C6 | findings 4–7 | `import ( P-A )`, `"( P-A && P-B )"`, `""( P )""`, `\"` | OPEN | wrong configuration, invalid output | `display/value_format.py`, readers | all | vmx, qfx, jvd | 8 | four classes gone |
| DEV-8, DEV-9, NEW-B1, NEW-B4, OPEN-21 | findings 8, 9; inventories | port-mirroring `routing-instance VRF-A` | OPEN | invalid output, false rejection | schema model: keyed single-entry types | all | vmx, qfx; `deactivate6.txt` | 11 | declared break |
| DEV-10..14, DEV-V2, DEV-V4 | findings 10–14 | `rf_list`, `server-group server-group`, `other-variables`, `bridge-domains domain`, `dynamic-tunnel` | OPEN | invalid output, false rejection | `L`+`nk` transparent list keys | XML, JSON input; set, curly input | vmx, qfx, jvd (`xml-element-name-leak`) | 12 | JVD unplaced measured |
| DEV-V2 apply-flags | device ledger | `set groups G system apply-flags omit` UNPLACED | OPEN | false rejection | universal statements from the tree | set, curly | vmx, qfx | 4 | |
| DEV-15 | findings 15 | `hello-padding strict` from XML | OPEN | invalid output, false rejection | XSD rename | all | vmx, qfx | 13 | |
| DEV-16, DEV-17 | findings 16, 17 | XML empty description, `"^show "` | OPEN | invalid output, wrong configuration | `display/to_yaml.py` `_xml_leaf` | XML input | vmx, qfx `.xml` | 9 | two classes gone |
| DEV-19, OPEN-18, NEW-A2 | findings 19; mission one-IR 18 | JSON numbers, scalar leaf-lists | OPEN | architecture-only | common input boundary | JSON, YAML input | device JSON prints numbers | 13 | |

## Architecture and one IR

| ID | Source | Reproduction / test node | Status | Impact | Owning layer | Formats / doors | Device evidence | Change | Also to close |
|---|---|---|---|---|---|---|---|---|---|
| ARCH-C11 | mission high-impact 2 | `from_dict({"system":{"services":{"ssh":true}}}, "json")` mutates | OPEN | caller mutation | `convert/output/json_output.py` | `junoscfg.convert.from_dict` | none needed | 2 | writer-family purity law |
| ARCH-C15 | mission format 10 | native JSON `groups` list | INTENTIONAL | — | `json_output._native_groups` | JSON output | vmx, qfx, jvd JSON | 2 (kept, made pure) | |
| ARCH-C06, ARCH-C08, NEW-A-X2 | mission schema 4, 5 | `UNIVERSAL_STATEMENTS` copies; Group-H name fallbacks fire 0 times | OPEN | architecture-only | `display/constants.py`, `validate/xsd_fixes.py` | all | none needed | 4 | retirement trigger and tripwire |
| ARCH-C09, NEW-C5 (=NEW-B8), NEW-A3 | mission schema 6 | JSON `ieee-802.3ad`, `end-range` unplaced | OPEN | false rejection | one rename table at the reader boundary | JSON, YAML input | vmx, qfx JSON | 13 | |
| ARCH-C10 | mission format 9 | JSON scalar `extended-vni-list` | OPEN | architecture-only | common input boundary | JSON input | device JSON prints arrays | 13 | contract reconciled |
| NEW-A-S3 | inventory A | XML `snmp system-name`, `ethernet-10g` | EVIDENCE_BLOCKED | possible false rejection | rename table | XML, JSON input | missing: `display xml`/`json` of each | 13 after evidence | |
| ARCH-C12, ARCH-C13, NEW-A-X1, NEW-A-X4 | mission schema 7, 8 | fixes report success without a mutation; three never fire | OPEN | architecture-only | `validate/xsd_fixes.py`, `artifact_builder.py` | build time | XSD dumps | 19 | doc counts |
| NEW-A-X3 (+ C13 `nat-rule-match`) | inventory A | SRX `security nat` absent from every dump | OUT_OF_SCOPE_FEATURE | — | schema | — | missing: an SRX XSD | — | |
| OPEN-19 | mission one-IR 19 | XML single leaf-list value | FIXED_ALREADY | — | `convert/input` | XML input | — | — | `TestLeafListPromotion` |
| OPEN-20 | mission one-IR 20 | BGP traceoptions `flag update send` | EVIDENCE_BLOCKED | none observed | IR shape | all | missing: P3 | after P3 | |
| OPEN-22 | mission one-IR 22 | `tunnel encapsulation vxlan-gpe` | EVIDENCE_BLOCKED | unknown | keyed `h` rule | all | missing: P4 | 11 after P4 | |

## Not junoscfg work

Device platform rejections, `$9$` re-encryption, device warning comments,
error-recovery artefacts, the device quirks `omitted-curly`,
`trigger-after-split` and `bare-deactivate-route-filter`, and recapture notes
superseded by the oracle capture.

## Strict xfails at the start of the run

19 nodes, none passing: OPEN-13 (5), OPEN-15 (5), OPEN-10 (3), ANON-P2 (2),
ANON-P3 (1), ANON-P4 (1), ANON-P1 (2).
