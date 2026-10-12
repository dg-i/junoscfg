## Supplementary synthetic generator coverage
Add one representative synthetic NETCONF-to-artifacts test through public ArtifactBuilder.build.
Preserved behaviour: generator outputs, existing focused tests and narrowed real-schema qualification policy stay unchanged; no runtime edits.
Verification: reload five artifacts, compile and exercise grammar, validate both schema definitions and valid/invalid documents, inspect representative tree semantics, compare fresh builds excluding only generated_at.
Verification: measure focused wall time against an approximately five-second target; no timing assertion; fresh lightweight review before root-coordinated full.
Changelog: changelog.d/+synthetic-schema-check.misc.md; the mandatory full-stage gate requires a fragment.
Scope: tests/unit/validate/test_artifact_builder.py and the existing developer-guide testing section.
Synthetic evidence supplements device and large-schema evidence; it cannot establish release compatibility or scale behavior.
