## 1. Tests

- [x] 1.1 Restore the artifact-count assertions to five.
- [x] 1.2 Rewrite the characterization class as
  `TestValidateXmlNeedsACleanedXsd`, carrying the measured lxml error and the
  85-name count so the next person does not repeat the experiment.

## 2. Implementation

- [x] 2.1 Remove the XSD write from `build_from_netconf_dump` and
  `build_from_xsd`.
- [x] 2.2 Correct `src/junoscfg/CONTRACT.md`.
- [x] 2.3 Correct `docs/guide/validation.md`, which promised the workflow
  produced the XSD.
