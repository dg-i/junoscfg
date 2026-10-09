## Specification challenges

### Direct XML output is not the same normalized IR

- **Artifact:** `proposal.md`, direct reuse of the existing XML walker.
- **Counterexample:** `TestXmlAndStructuredInputAgreeOnTheIr` fails when XML
  bypasses `yaml_to_dict()`: that adapter performs schema-driven leaf-list
  promotion in addition to YAML deserialization.
- **User impact:** A nominal optimization would make equivalent XML and
  structured inputs produce different IRs.
- **Proposed correction:** Move leaf-list promotion to the common input boundary
  and explicitly decide whether the shared XML walker becomes a supported
  package-door API or whether layering/interface policy should change.
- **Decision:** Accepted by the owner on 2026-10-09. The owner supplied the
  device-derived `private_test_data/anaon.conf`, `anaon.xml`, and `anaon.json`
  representations and authorized package API changes that preserve the
  production Ansible collection. The private XML capture showed 22 raw
  scalar-to-list normalization differences and no other difference from the
  current XML IR, so leaf-list promotion moves to the common input boundary.

### Private helper cannot cross the package door

- **Artifact:** `proposal.md`, private shared display helper.
- **Counterexample:** `tach check` rejects `junoscfg.display._xml_to_dict`
  because it is not in the declared interface; exposing it would contradict
  the proposal's no-public-API claim.
- **User impact:** Bypassing the interface would weaken enforced layering.
- **Proposed correction:** Resolve together with the normalization challenge.
- **Decision:** Accepted by the owner on 2026-10-09. The helper becomes the
  supported `junoscfg.display.xml_to_dict()` package-door API. Inspection of
  the production collection at its current HEAD confirms it imports only
  `FieldValidationError`, `Format`, `convert_config`, and `validate_config`
  from the top-level package; none changes here.

## Owner acceptance evidence

- The three private capture files are different device renderings of the same
  anonymized configuration after it was loaded back onto a Juniper device.
- The direct XML path produces the same canonical private-capture IR SHA-256 as
  the bridge path: `0c8b63bb622e3722820c613f2d66c3a6051dd6c9621b524de12a575028098a89`.
- The public synthetic acceptance test fails if XML input calls
  `xml_to_yaml()` and pins the schema-backed singleton leaf-list result.

## Findings

1. **MUST — the shared normalizer changes every input format, not only the XML
   bridge it replaces.** The proposal requires parsing, errors, normalization,
   and public output to remain exact and names changing the dict IR schema as a
   non-goal (`proposal.md:13-14,28`). Instead, `to_dict()` now calls
   `normalize_leaf_lists()` unconditionally after JSON, YAML, XML, set, and
   structured parsing (`src/junoscfg/convert/input/__init__.py:24-49`), and that
   helper always loads the schema tree
   (`src/junoscfg/convert/input/normalization.py:10-12`). A review probe replaced
   the schema loader with an unavailable-artifact error: a valid JSON document
   that previously needed only `json.loads()` now raises that schema error.
   Scalar values in schema leaf-list positions also change from scalars to
   arrays for JSON, set, and structured input, although the accepted defect was
   specifically the normalization formerly supplied by XML's YAML bridge.
   Restrict schema-backed promotion at the shared dispatcher to the two formats
   that require it to preserve established behavior (YAML and XML), and add a
   regression proving JSON parsing neither calls the schema loader nor changes
   its input value shapes.

## Already provided

- `normalize_leaf_lists()` is the existing extracted implementation needed by
  both YAML and direct XML input; no second normalizer is needed.
- `display.xml_to_dict()` is the sole XML walker, and both conversion and
  XML-to-YAML serialization consume it through the package door.
- The XML parser retains the lazy `lxml` import and existing malformed-input
  error conversion.

## Review prompts

- **Trust-boundary input:** XML text remains attacker-controlled and crosses
  the same hardened `lxml` parser and `ValueError` boundary. The direct walker
  adds no parser bypass or new entity-resolution path.
- **Incompatible-but-valid input:** valid JSON is incompatible with the new
  assumption that a schema artifact is available. The monkeypatched loader
  probe raises `RuntimeError: schema unavailable` for a simple JSON
  configuration; the merge-base JSON path has no schema-loader call.
- **Shared blind spot:** all acceptance tests run with bundled schema artifacts
  present, so they can pass while JSON acquires an unrelated runtime dependency.
  The proposed JSON no-loader regression checks this independently of XML
  parity.
- **Second answer:** none. `display.xml_to_dict()` owns XML walking;
  `convert.input.xml_input.xml_to_dict()` only unwraps and validates that
  mapping for the conversion boundary.
- **Stated figures and non-goals:** the private device capture reproduces 22
  raw scalar-to-singleton-list promotions, direct XML equals the former YAML
  bridge, and its canonical SHA-256 remains
  `0c8b63bb622e3722820c613f2d66c3a6051dd6c9621b524de12a575028098a89`.
  The behavior-preservation non-goal does not hold for non-XML formats because
  of finding 1.

## Verdict

Ready to archive after correction. Finding 1 is resolved: the common dispatcher
invokes schema-backed leaf-list normalization only for YAML and XML, while JSON
retains its supplied shapes without loading schema artifacts. The contract and
module description now state that boundary.

The fresh correction review independently passed 12 leaf-list and JSON
round-trip tests. The private device capture still gives identical direct and
former-bridge IR with canonical SHA-256
`0c8b63bb622e3722820c613f2d66c3a6051dd6c9621b524de12a575028098a89`, and
all 33 production collection tests pass. No correctness, contract,
trust-boundary, second-answer, or documentation finding remains. The separate
`control-as-list-type` defect described in `private_test_data/bugreport.txt` is
not introduced or masked by this leaf-list correction and remains outside this
behavior-preserving refactor.
