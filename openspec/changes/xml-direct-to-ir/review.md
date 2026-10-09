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
