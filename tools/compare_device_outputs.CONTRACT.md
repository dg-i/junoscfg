# compare_device_outputs — contract

## Not for

Not a conversion implementation, device-law classifier, semantic equivalence proof, schema verifier or evidence cache. tools/device_differences.py remains the device-law classifier. Records belong in private change evidence directories.

## Invariants

- record OUT.json [--anonymize] reads the current tree's tests/data/device/manifest.json and available conf/set/json/xml gzip renderings in memory; it never modifies captures. Every available rendering converts to SET, STRUCTURED, JSON and YAML through junoscfg.convert_config_result. Missing rendering files retain the source template's skip behavior.
- Sorted JSON keys identify capture, output format and rule. Each successful result preserves output, sorted unique (source, severity, path) triples with a missing path as empty, and sorted field-prefixed diagnostic messages including warnings and errors. A conversion exception stores only its class, and later conversions continue.
- Plain is always included. --anonymize adds each of the ten template rule selections and all together, with fixed salt compare-salt; the current manifest's 24 renderings yield 96 plain or 1,152 optional-rule records.
- diff BASE.json HEAD.json compares the sorted union of keys and reports changed/total counts. Output edits use zero-context unified diffs; other changed fields show base/head values. Added and removed keys remain visible.
- Frozen synthetic acceptance: tests/tooling/test_compare_device_outputs.py checks complete matrices, immutable captures, diagnostics, exceptions, individual/all modes, changed fields/keys and positional script commands. Private template preservation checks do not replace shared-tool acceptance.

## Precedent

Promoted from the single private compare-template.py answer. This tool is the shared comparison entry point; per-change scripts are superseded. Public junoscfg and junoscfg.anonymize doors supply conversion and its configuration type; no product module is changed.
