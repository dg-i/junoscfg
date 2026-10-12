## Specification challenges

### SC1: An existing singleton entry loses its key prefix under global fallback removal

- Artifact: conversion/entry-keys delta, Requirement "Known containers do not borrow the name entry fallback": "WHEN a known schema container has a child named name THEN the shared writer SHALL traverse its children rather than consume name as an entry key"; convert/CONTRACT.md preserves supported reader/writer IR round trips.
- Counterexample: executed source-only public conversion of `set access securid-server SRV-A configuration-file sample-1`. The actual current-base writer preserves that one statement. The proposed writer now emits `set access securid-server SRV-A` and `set access securid-server configuration-file sample-1`, losing the entry key on its child. Bundled root/grouped securid-server nodes are non-L homogeneous containers with scalar positional name; original selected25.2 source declares that name an identifier. The existing reader still holds one dictionary. This is source/model preservation evidence, not a device acceptance or second-entry claim.
- User impact: a previously retained single supported entry no longer round-trips after the proposed writer change. Ordinary transport-class and snmp containers do need the correction; their name child is respectively a list or a keyworded value, not a scalar positional entry identifier.
- Proposed correction: qualify ordinary-container wording to distinguish positively source-declared singleton identifiers; preserve the existing single entry. Minimal alternatives for independent review are (A) an owning structural correction of additional exact source-qualified singleton paths with explicit slot/provenance inventory, or (B) an explicitly source-qualified key answer retained for singleton nodes while ordinary containers never consume a name child. Neither permits a global name/homogeneous sweep, a second SecurID entry/cardinality promise, or a hidden-list expansion. Runtime source-marker availability and blast radius must be proved before choosing B.
- Decision: Accepted correction C by root-sc1-correction-ruling.json after independent 595 PASS/ADEQUATE. Suppress fallback only for a known name child with L, container c, ll, p, or l without nk; preserve unknown-schema and legacy scalar positional-name ambiguity. Delta/freeze/docstring explicitly narrowed, independent 16 command/IR and 7 shape controls appended without changing original valid negatives. Alternative A additional SecurID model allowance is not admitted; B new metadata is unnecessary. Original failed global-removal and rejected A evidence retained privately. OPEN-5 second-entry/cardinality and direct device validity remain carry.

## Source-only evidence

The accepted three-path fix changes is_list only after an actual scalar positional identifier declaration and preserves children, key order and combinator. Private exact snippets from the physical selected25.2 dump, parsed only as narrow fragments, show three actual shared nodes and six projected root/grouped paths. The full physical schema is not parsed/generated. Negative source tests cover value versus identifier, keyworded/freeform name, key leaf-list, node leaf/leaf-list/presence, unkeyed homogeneous, alternate key order and outside path. Focused source/writer/immutability checks:572 passed. Exact command/source/diff/projection/probe hashes are retained in private makeover-work/keyed-single-entry-lists/source-only-snapshot.json.

### SC2: Named parent definitions retain uncorrected singleton shapes

- Artifact: frozen schema-pipeline/entry-key-fields singleton list promise and conversion/entry-keys public validation acceptance; approved six-slot/root-group structural plan.
- Counterexample: the single authorized public25.2 build exits0 and changes exactly six structure-tree nodes (L6 plus SRGB o2), but post-build tests have12 semantic JSON/YAML validation failures/317 passes. All three named singleton arrays are rejected as non-list containers. Current schemas cache named definitions by type_ref; current root/group tree entries are L while equivalent named-parent hierarchy copies remain non-L and can supply the cached definition reused on the corrected paths. Exact reference traces and ancestor type identities are retained privately in phase5-current-base/schema-reference-counterexample.json. No assertion or product is manually changed.
- User impact: JSON/YAML conversion output for the promised three singleton paths still fails public validation despite successful readers/writers. Six tree changes alone do not fulfill the frozen promise.
- Proposed correction: independently assess the minimum source-qualified set of equivalent declaration copies needed by the owning fix, with exact path inventory and untouched negative controls, or a bounded schema-reference correction that distinguishes differing corrected shapes. No blanket692 promotion, identifier inference from names/flags, new second-entry allowance, SecurID model change or generic framework is proposed. An additional public generation requires an explicit evidence-based root ruling.
- Decision: Accepted scoped owning-generator correction by root-sc2-generator-extension-ruling.json following independent assessment SHA33cd7e01ec558d1ca142832695594e177063e86626685618738291a939ba4c9f. Extend only schema_generator.py and its owning tests; descendant shape and effective cutoff context must qualify named reuse, with compatible reuse/cycle/determinism preserved. No broader source promotion or second product build authorized. First build, twelve failures, prior SC1/A evidence and carries retained.

## Implementation evidence after accepted SC2

Independent source-only assessment667 PASS/ADEQUATE and root-second-product-build-ruling.json authorized the second selected25.2 public implementation build. Actual1329 definitions/18019 refs match projected names/bodies exactly; all refs close. Raw tree/grammar remain first-build-identical, six nodes/eight flags and SEC allowance unchanged. Focused actual products370 PASS, including all twelve original JSON/YAML failures. Fresh phase6 Reviewer remains required after current-base checkpoints.

Private first-build slot-audit output was accidentally overwritten by the second audit invocation; restored exact original bytes from preserved first products and verified original manifest hash. Both audit versions, correction manifest and raw log remain explicit evidence. No source/public products were modified by recovery.

### SC3: Correct implementation leaves obsolete bundled-model guards and grammar inventory

- Artifact: existing anonymizer routing-instance non-L guard; artifact-builder exact one-line carrier pin; device corpus exact false-rejection record. Owner intake section6 governs concrete obsolete expectation correction with independent review.
- Counterexample: normal atomic commit hooks execute3 failures/10205 passes,37 skips/20 existing xfails. The admitted list now has L; root/group SRGB add exactly two `o` carriers (3552 to3554, key-only1286 unchanged). Exactly56 original recorded grammar rejections now accept, not55: port-mirroring1, IS-IS attribute-group28, IS-IS-instance attribute-group25, SRGB2. Exact source/products/hook failure snapshot retained.
- User impact: correct bounded source/products cannot pass normal commit while old guards and recorded false rejections contradict them. No new device syntax, cardinality or global correctness follows.
- Proposed correction: positive L guard preserves original offered-IP assertion and strengthens two-entry synthetic visitation; exact3554/1286 count and digest retains semantic carrier-map/child assertions. Adopt independent tracked-only corpus candidate: all255 original statement/origin pairs preserved,246 accepted/9 unchanged rejected, exact414 rule union and8713 input inventory. Native greedy extra-row adoption is excluded.
- Decision: Accepted by root-obsolete-guard-correction-ruling.json under owner section6 after independent ADEQUATE (assessment SHA967944107f3031efebdefad54685c78d444ca0e9311f43d790e354eced285161). Exact candidate SHA7ab722cbf209fa8da0cbe9c69ca41a95fb7bf8afd778126399ce41e9b8ded2e1 adopted; narrow three extra paths admitted. Original hook failure, native greedy alternative/rejection, all source-generation audits and carries preserved. Optional TestEveryDeviceLine skip is not PASS; native all8713 classification is distinct evidence. No live corpus regeneration/new rows/third product build.


## Fresh independent phase 6 review

# Done

**PASS for the accepted bounded phase6 scope.** No surviving MUST, SHOULD or NICE finding; no new specification challenge. Recommend accepting this fresh review and proceeding with the bounded phase7 work. This verdict does not close the deferred physical-schema checkpoint or authorize integration/archive.

Reviewed candidate `62146d2c70b6302bd2b74cbf4d4847d898c03c96` against base `3d60e0a04c42c3afa9049e922d70a0cb47fd14b5`. Public committed freeze, deltas, contracts, SC1–SC3 rulings, tests and diff supplied the baseline in phase6 order. No Builder implementation report or private reasoning supplied the verdict.

# Evidence

The exact git archive SHA256 is `84a556b15477c37e3064acc969ca19db5de590fabe522d0e0c8351b03822f78e`; binary base/candidate diff SHA256 is `d740d775ae1f1d2f9e5a59b10a3f5ee1ae2bcef73dad4474a19015619a4e06f2`. Execution used `/private/tmp/junoscfg-fresh-phase6-_m5tukr0` and the cached candidate Python3.13 interpreter. `binding.json` proves package, generator, writer and test-support imports resolve inside that archive. `locked-environment.raw` independently confirms installed dependencies match the committed lock. Live and isolated copies retain all1247 tracked hashes; all76 held native-evidence hashes match their frozen receipt; live HEAD/status remain exact and clean. `before.json`, `after.json`, `executions.json` and `evidence-sha256.json` preserve complete binding and raw-output hashes.

| Independent execution | Result |
|---|---|
| Owning generator, singleton fix, full roundtrip/immutability controls, original missing-entry-key and partial/surplus meta-key controls | 718 PASS; zero failures/errors/skips |
| Five accepted catalogue rows through all format laws | 255 PASS;4817 deselected; zero failures/errors/skips |
| Independent accepted SC2 definition-context and SC1 C shape controls | 27 PASS; zero failures/errors/skips |
| Existing tracked grammar pairs parsed independently; no corpus generation | 255 expected classifications;414 rule union |

**Source correctness and scope.** `xsd_fixes.py` changes only admitted paths after a scalar positional identifier declaration, without changing child/key order. Independently comparing serialized trees finds exactly six nodes/eight flag additions: L on the six root/group slots and o on the two SRGB copies. All remaining nodes, keys, children and order retain their original values. The historical candidate scan independently reproduces all692 exact paths/366 homogeneous nodes; those counts remain inventory, never promotion evidence. The owning registry has42 fixes, with7 in the structure/combinator group, matching both document edits.

**SC1 C and second answers.** The shared writer retains the accepted scalar positional-name and unknown-schema fallback while ordinary L/c/ll/p/keyworded-l name children traverse separately. Existing entry-key order and positional formatting still come from display's `entry_keys()`/`key_is_positional()`. The added branch decides whether the historical fallback applies; it does not establish a second key catalogue, device identifier claim or runtime override. Root/group SecurID preservation and unchanged caller IR execute successfully. Accepted `root-sc1-correction-ruling.json` remains authoritative; rejected additional SecurID model allowance is not reintroduced.

**SC2 and trust boundary.** JSON/YAML data from callers cross the structural-validation boundary. Named definition reuse must not borrow array permission or cutoff-weakened descendants from an incompatible context. Owning and independently authored controls execute both encounter orders, ordinary-array rejection, compatible separate allocations/depths, cutoff preservation, active recursive registration, resolvable refs and leaf/presence/key/switch/groups discrimination. The semantic discriminator mirrors emitted constraints; per-generation object/depth memoization only bounds rescans. No runtime network/process input, dependency, schema fallback or new public parameter is added. Accepted `root-sc2-generator-extension-ruling.json` and `root-second-product-build-ruling.json` govern this extension.

Independent read-only inventory verifies both shipped schemas:917→1329 definitions,8708→18019 refs,412 added names,zero removed names and36 changed same-name bodies. Every reference resolves and SecurID definitions remain identical. This is product inspection, not a new physical parse/build or stability proof.

**Shared blind spots and SC3.** Format roundtrips alone could preserve the same wrong IR; the independently expected device-backed arrays, public validation assertions, ordinary-container negatives and independently authored definition-context controls address that risk. The accepted original255 grammar statement/origin pairs remain exact:190 old accepted plus56 newly accepted gives246;9 old rejections remain unchanged. The tracked file matches approved SHA256 `7ab722cbf209fa8da0cbe9c69ca41a95fb7bf8afd778126399ce41e9b8ded2e1`. Independently parsed pairs cover414 rules. Oneliner inspection reproduces3554 non-key carriers/1286 key-only carriers and digest `b4c53cfcd0df5ab5237263a0aa18db90e7dde41ac76a378dd9607f3cfb397163`; original semantic carrier/child checks remain. Accepted `root-obsolete-guard-correction-ruling.json` governs those obsolete guards.

Known differences are precisely old data minus three classes/88 lines:transport-class80, inactive-name-leak4, inactive-repeat4;544 lines and every remaining class/body are unchanged. Recounting held raw base/final outputs gives1152 cases,624 changed, twelve rules each96 cases/52 changed/50 output/32 diagnostics/32 field-validation/zero exception changes. The held case audit covers exactly every changed key and reports no unexplained case. This recount does not relabel those prior conversions as fresh executions.

The actual ordinary/fast raw hashes independently verify as `35aef1bdb6d9518b1cab5b35c88c21a8fd4dd84e31ee16d4bc2bc40023ea738b` and `6daf13bae942834e92af19c77badcfb2c1233a072c9f1bb0800fdb2b2c295f59`. Their checked identity remains `608265030be20c639e2364e72e8a715c5cad7ce4`, not the record-only review candidate. All runtime/test/product/tool/config bytes bind exactly to the candidate. Reported ordinary10210 PASS/37 SKIP/20 existing strict XF,92.99% coverage above unchanged91.47 floor, and supported fast exit0 are held native evidence, not this review's reruns. Schema and optional device-grammar skips remain skips.

# Changed paths

Only this private report and generated review execution/binding receipts were written under `private_test_data/makeover-work/keyed-single-entry-lists/independent-fresh-phase6`; an exact immutable source/test snapshot was extracted into `/private/tmp`. No live source, test, specification, product, metric or lifecycle checkbox was edited. Root owns the review checkbox after accepting this verdict.

Context rows for root to preserve with phase6 evidence:

| Field | Value |
|---|---|
| Context expansion: src/junoscfg/display/constants.py | Confirm one authoritative key/positional answer under qualified writer fallback |
| Context expansion: src/junoscfg/CONTRACT.md | Confirm public validation doors and cleaned-XML-XSD limitation |
| Context expansion: tests/unit/convert/test_field_validator.py | Independently execute existing missing-key rejection controls |
| Context expansion: tests/unit/convert/test_set_input.py | Independently execute original partial/surplus meta-key preservation |
| Context expansion: tools/device_grammar_corpus.py | Confirm grammar rule-union meaning without regenerating the native corpus |

# Commands and exit status

Exact argv/cwd/env, exit codes and raw hashes are retained in `executions.json`. All three focused pytest commands exit0; Python inventory/environment probes exit0. Selection includes the full owning `test_schema_generator.py`, `TestKeyedSingletonLists`, `test_convert_roundtrip.py`, `TestAnEntryWithoutItsKeyIsUnplaced`, `TestAMetaCommandIsNeverPartiallyApplied`, the five-row `test_format_matrix.py` selector, and independent SC1/SC2 controls. Each pytest command uses `-p no:cacheprovider`, private JUnit output and offline/bytecode-disabled environment.

Read-only git archive/diff/hash/binding and raw-output recount commands exit0. One combined read command exits1 solely because it requested `instruction-integrity.md` at repository root; the exact change-folder file was then read successfully. Initial inventory querying added an extra non-leaf exclusion and produced624 candidates; correcting the query to the recorded non-L/nk-name definition independently reproduces692 exact paths. Neither exploratory result is product counterevidence or a failed test.

# Open questions for the owner

None newly required by this review. Existing carries remain:OPEN-5 second SecurID entry/device validity, historical OPEN-14/56, unkeyed tunnel/P4, P1/P6/P7/P8, DEV-V6 and unresolved scalar positional-name ambiguity. No second-entry or global normalization guarantee is established.

The required final entire-makeover checkpoint remains open under `OWNER-SCHEMA-SCHEDULE-2026-10-12`:selected physical25.2R2-S1.5_qfx5120.xsd only; original doublepass/four raw stable products, canonical metadata excluding only generated_at and fresh uncached sentinel. No21/23 schema or canonical full ran here. Preserve this in the root carry-forward list; phase7/main-spec finalization and integration are still pending.

# Deviations

Owner scheduling overrides per-change physical/full verification, without weakening assertions. Isolated focused execution and held native ordinary/fast evidence fulfill this review's assigned verification scope; the two earlier admitted implementation builds are not called final stability/full proof. Parent explicitly owns live lifecycle marking and requested private reviewer output, so this report leaves those live records unchanged. No early stop or correction implementation occurred.


## Fresh independent generated main-spec affirmation

# Done

**PASS** for the exact generated phase7 main-spec edits. No finding or new specification challenge. Recommend root accept the generated files with the hashes below; this affirmation does not authorize integration/archive or close existing carries.

# Evidence

Reviewed immutable candidate `62146d2c70b6302bd2b74cbf4d4847d898c03c96`, base `3d60e0a04c42c3afa9049e922d70a0cb47fd14b5`, against preserved public source/delta/base/generated artifacts. All four source inputs equal the exact reviewed commit. Both old main specs equal the baseline versions. Each generated file is exactly its existing main-spec body plus its already reviewed ADDED delta, with no modification/removal of any old requirement, scenario or test binding. Four requirements are added, two per capability.

| Exact generated artifact | SHA256 |
|---|---|
| schema-pipeline/entry-key-fields/spec.md | `65594ab9eb2b8456a332826b365a201acff87993f5b293ac7e910c0202af2b95` |
| conversion/entry-keys/spec.md | `b12489629e72ab5a4a353ee09041ecb51ddf26d59d2bcf92b54a60ba4a490986` |
| proposed-main-spec.diff | `0ae938013ac97365678147dfed6a5dfb5d04929c3a9e31bca96f07ea6e478780` |

All23 referenced new test nodes resolve in the exact previously reviewed archive. The earlier718 focused/255 five-row format-law/27 independent-control PASS remains the execution evidence; no test was rerun or relabelled here.

The schema singleton requirement retains the bounded three named root/group paths, positional-identifier qualification, unchanged child/key ordering and ordinary-container/unkeyed/value negatives. It establishes no broad692-slot promotion or second-entry device cardinality claim. The conversion requirement preserves one-entry arrays/tags through the existing IR and writes inactive keys once. Accepted SC1 C ordinary-shape qualification, unknown-schema/scalar positional-name fallback, caller immutability and single SecurID preservation remain verbatim. Its explicit no-second-entry/no-device-validity wording remains. Snmp remains a corrected-schema control without a device acceptance claim.

Accepted SC2 definition-context constraints remain verbatim: compatible emitted descendants/effective depth, compatible separately allocated reuse, recursive registration, depth cutoff, deterministic closed references and semantic child gates. It explicitly changes no source cardinality or accepted device syntax. No generator framework, additional runtime parameter, fallback, global IR normalization or broad syntax assertion is introduced by synchronization.

Existing carries and source-review qualifications are unchanged:OPEN-5 second-entry/device validity, historical OPEN-14/56, tunnel/P4, P1/P6/P7/P8, DEV-V6 and scalar positional-name ambiguity. Required final entire-makeover selected25.2 physical original-doublepass/four-stable-raw-products/canonical-metadata-only-generated_at-exclusion/fresh-uncached-sentinel remains open under OWNER-SCHEMA-SCHEDULE-2026-10-12. No21/23/full/schema execution occurs here.

`mainspec-binding.json` records all exact input/output/diff hashes and preserves the original review and evidence-manifest hashes. Live candidate HEAD/status remain exact and clean. This bounded affirmation relies on byte equality to the reviewed deltas, text review and test-name binding; it introduces no new runtime scope.

# Changed paths

Private supplemental `mainspec-review.md`, `mainspec-binding.json` and `mainspec-evidence-sha256.json` only. Original `review.md` and `evidence-sha256.json` remain untouched. No live public spec or lifecycle record was edited; root retains integration/archive/metrics approval.

# Commands and exit status

Read-only manifest/diff inspection and directory enumeration completed. The first combined read command exits1 because rg excluded the gitignored private tree; the requested manifest and diff were read, and Python path enumeration then confirms all preserved inputs. The bounded Python integrity check exits0: exact commit/base comparison, generated-body equality, four added requirement counts,23 AST test bindings, expected hashes and live clean HEAD/status. No source test, ordinary/full, physical schema, generator or native-corpus command was run.

# Open questions for the owner

None new. Accept these exact two generated hashes for root-controlled application; existing finalization/integration approvals and deferred carries remain pending.

# Deviations

None to the bounded phase7 affirmation. Prior phase6 findings/verdict/evidence are unchanged.
