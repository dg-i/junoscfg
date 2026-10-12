## Why

T4 replaces the private comparison script copied for every change with one reusable, tested developer tool.

## What Changes

Promote compare-template.py to tools/compare_device_outputs.py with its module contract, preserving record and diff behavior.
Keep record OUT.json [--anonymize] and diff BASE.json HEAD.json; use the current tree's manifest and public conversion API.
Search: manifest.json, Path.cwd, compare-template, record/diff and convert_config_result in tools and the batch guide found only the private template as this comparison reader; device_differences remains the separate device-law classifier, schema_verification resolves schema evidence only.
Update the existing batch-guide comparison instructions to use the shared tool; add synthetic tooling tests.

## Capabilities

### New Capabilities

- `conversion/device-output-comparison`: reproducible base/head output and diagnostic records with explanatory diffs.

### Modified Capabilities

None.

## Non-goals

No conversion, validation, anonymization, schema, cache, device-law, consumer API or junoscfg CLI behavior changes. No new corpus, comparison framework, overrides, dependencies or speculative cases.

## Impact

Owned paths: tools/compare_device_outputs.py, tools/compare_device_outputs.CONTRACT.md, tests/tooling/test_compare_device_outputs.py, docs/how-to/run-a-batch-of-changes.md comparison subsection, changelog.d/+compare-device-outputs-tool.feature.md and this change folder.
The baseline template records 24 renderings × 4 outputs = 96 plain runs, and 12 modes = 1,152 with anonymization, over tests/data/device/manifest.json; later shared record commands reproduce these counts.
Nothing on a named surface is removed: the copied private script becomes superseded by the shared tool.
