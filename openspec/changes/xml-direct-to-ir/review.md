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
- **Decision:** Pending owner decision. Safe interim action: restore the proven
  XML→YAML→IR path and leave this change unmerged.

### Private helper cannot cross the package door

- **Artifact:** `proposal.md`, private shared display helper.
- **Counterexample:** `tach check` rejects `junoscfg.display._xml_to_dict`
  because it is not in the declared interface; exposing it would contradict
  the proposal's no-public-API claim.
- **User impact:** Bypassing the interface would weaken enforced layering.
- **Proposed correction:** Resolve together with the normalization challenge.
- **Decision:** Pending owner decision; baseline interface restored.
