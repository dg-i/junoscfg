# Review

## Specification challenges

### SC1: exact sibling layout exceeds conversion-equivalence requirements
Artifact: tests/corpus/test_schema_data.py parity assertion.
Counterexample: retained selected 25.2 outputs contain the same 348 raw commands
and gold-before-bronze entries; only independent auto-create/fallback siblings
move relative to the entries. Original full run remains failed.
User impact: blocks valid equivalent non-XML conversion qualification.
Proposed correction: stable-partition only these exact control lines in one
contiguous root transport-class block; preserve every other raw line/order/count,
then supplement with existing read_ir equality. No generic equivalence promise.
Decision: accepted by root under original owner section 6 after independent
ADEQUATE assessment; no requirement changes. Fresh review remains pending.

Independent challenge report follows verbatim, as supplied before implementation.

# Independent Test/Challenge ruling

ADEQUATE: a narrow test-only correction is justified. This is an assessment, not implementation or an overall qualification pass. Frozen source HEAD: 58ce09b62622e89bf9ecfd4edd0c89e720c0b9bd. No source, requirements, runtime, gate, fixture, or shipped artifact changed. The failed selected run remains failed pending correction, independent review and rerun.

## Governing requirements

- ARCHITECTURE.md lines 18–25: converted configuration must mean what input meant; equivalence suffices, byte-identical device layout is not a goal; tests assert meaning/IR. The evidence hierarchy at lines 145 onward ranks device output first.
- tests/CONTRACT.md, Rules: assert meaning, never byte layout; preserve device truth and import through public doors.
- src/junoscfg/convert/CONTRACT.md: every supported pair round-trips without content loss and one configuration yields one IR.
- openspec/specs/conversion/entry-keys/spec.md, Known containers / Transport-class: both name entries and sibling auto-create survive. Earlier requirements retain entry order and key order. These are meaningful and cannot be sorted away.
- openspec/specs/conversion/writers/spec.md, writer immutability: retain the caller IR's key order exactly **in the caller object**. It does not require identical sibling serialization order across conversion routes. No requirement rewrite is needed.
- tests/support/shapes.py lines 2588 onward already models this exact container as a name-entry list plus sibling auto-create, independently specifying gold then bronze. Existing shape tests remain untouched.
- User attachment section 6 authorizes demonstrably unjustified test correction subject to challenge and independent review, with explicit preservation of meaningful order/multiplicity/value/activation/escaping. This ruling addresses challenge only; root retains authorization/workflow decisions.

## Actual independent device evidence

Read the compressed synthetic junoscfg-oracle captures for vmx-23.2R2-S7.5 and qfx5120-25.2R2-S1.5. Both native JSON captures contain the same transport-class object: auto-create [null], fallback {none:[null]}, and name ARRAY [gold(color4000,end-point10.255.0.3), bronze(color6000)]. Both native SET captures show the same five exact statements: auto-create; fallback none; gold color; gold endpoint; bronze color. The conf and XML captures provide the same sibling/container structure (example conf824–838, XML1246–1264). Device evidence establishes independent settings versus ordered entry array; it is not a live device reordering experiment. Configuration equivalence is inferred from that captured structure and the governing IR contract, not from a new device acceptance claim.

Retained direct versus via-JSON differ only by moving the two exact sibling statements after the three exact entry statements. Their 348-line multisets match; gold precedes bronze in both. Source and artifact SHA256 values are recorded in probe-results.json, including both compressed and uncompressed capture hashes.

## Minimum correction recommended

Reuse tests.support.shapes.read_ir for an additional public SET-to-JSON IR equality check. Do not create a new semantic-comparison framework. Retain a tiny local assertion/normalization specific to the evidenced exception in this corpus assertion:

1. Keep exact raw line multiplicity/content (Counter over splitlines(keepends=True), not stripped/sorted tokens).
2. Identify a contiguous block of lines starting with the exact root prefix `set routing-options transport-class `; permit no reordering outside that block.
3. Within that block only, stable-partition the two EXACT lines `set routing-options transport-class auto-create\n` and `set routing-options transport-class fallback none\n` ahead of all other block lines. Preserve their relative order and counts; preserve every other line's relative order and raw bytes. Compare resulting sequences exactly.
4. Assert existing read_ir outputs equal as a supplementary guard.

The private probe implements steps1–3 and separately verifies4. This is intentionally narrower than general semantic equivalence. It does not sort entry lines, policy terms, leaf lists, siblings globally, or values. It admits only the documented representational movement. No newline/whitespace/escaping normalization is allowed. It does not alter deterministic artifact or anonymization-reversal requirements.

Coverage removed: exact position of those two independently captured sibling statements relative to the unchanged entry statements. Coverage retained: every raw statement, duplicates, activation, values/references, whitespace/escaping, every entry's order and every other statement's order. Independent negative controls accompany the allowance. This localized test correction is more conservative than replacing the assertion with a generic comparator.

## Existing helper / guarded combination assessment

read_ir is an existing public-door helper and can be reused directly. tests/support/devices.py Capture.difference uses sets, discarding multiplicity; it is insufficient here. The _in_order helper in test_format_matrix.py makes all mapping order significant and would retain the unjustified failure; it is private to another test module and not a suitable import.

Counter plus read_ir equality is much stronger than either alone and rejects independently constructed policy-term and BGP import ordering reversals. However, two unknown commands `set unknown a` and `set unknown b`, reversed, yield equal read_ir results despite raw order changing. This does not prove a valid-device semantic failure, because these are unknown commands. It demonstrates that the pair cannot establish arbitrary meaningful ordering independently of placement/parser behavior. No broad acceptance guarantee is justified from it; the local raw-order guard removes this uncertainty for this correction. If root chooses a general guarded comparator instead, independent review must explicitly bound its claim to evidenced/placed shapes and ensure unknown/unplaced ordering is retained.

## Executed checks and limits

Commands (repository root):

- `graphify query 'conversion equivalence order transport-class' --budget 800`: exit0; graph context only, contracts/captures read directly for proof.
- `.venv/bin/python private_test_data/makeover-work/final-25.2-qualification/independent-parity-order-challenge/probe.py`: exit1, test helper import absent because script directory was import root; no conclusions from failed execution.
- `PYTHONPATH=. .venv/bin/python private_test_data/makeover-work/final-25.2-qualification/independent-parity-order-challenge/probe.py`: exit0, all13 result booleans true, including aggregate. Actual source of this bounded probe is preserved beside this report.
- Additional inline Python with `PYTHONPATH=.` and retained `JUNOSCFG_ARTIFACTS`: exit0, policy-term reversal rejected by IR; BGP import reversal rejected by IR; unknown statement reversal not rejected by IR.
- Inline gzip/JSON read of both device capture JSON and SET transport-class sections: exit0; independent structures identical as described above.
- `git status --porcelain`: empty; `git rev-parse HEAD`: frozen SHA above, exit0.

Negative controls: gold/bronze entry-order reversal, policy-term reversal, ordered leaf-list reversal, duplicate added statement, set-to-deactivate change, color value change, endpoint/reference change, extra internal space, quote/escaping spelling change, reversal of the two control lines. All rejected by narrow raw comparator. Observed sibling movement accepted; retained public IRs equal. These are adversarial controls, not a full suite.

Provenance: all FOUR retained generated product gzip files exactly equal shipped raw bytes (JSON schema, YAML schema, Lark grammar, structure tree); metadata gzip differs but decoded objects equal after removal of generated_at alone. Exact hashes in probe-results.json. No schema build, full tests, network, device access or commits performed. No pass2/sentinel started. Report does not override overall FAIL.
