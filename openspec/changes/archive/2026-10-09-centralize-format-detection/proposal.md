## Why

Conversion, validation, and audit currently infer input formats in separate
branches, and their implicit policies differ. A shared classifier should make
those differences explicit without widening any caller's accepted inputs.

## What Changes

- Add one parse-confirming classifier for JSON, XML, YAML, display set, and
  structured input, with an explicit accepted-format policy per caller.
- **BREAKING CLI BEHAVIOR:** Make conversion and audit use the five-format policy while validation keeps
  its existing set-versus-structured auto-detection contract.
- Characterize empty input, JSON, XML, block and flow YAML, set, structured,
  and brace-prefixed ambiguity before replacing the existing branches.
- Remove the CLI-local detector and top-level inline set check.

## Capabilities

### New Capabilities

- `conversion/format-detection`: Content classification and caller-specific
  accepted-format policies.

### Modified Capabilities

- None.

## Non-goals

- Do not change explicit `-i/--import-format` or `format=` handling.
- Do not make validation auto-detect JSON, XML, or YAML.
- Do not change parser acceptance or error recovery after classification.

## Impact

The shared display kernel, top-level validation facade, conversion and audit
CLI paths, their tests, API documentation, and interface declaration change.
No dependency or environment lookup is added.
