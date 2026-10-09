# Junoscfg Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `agent-ready-change` for each item. Do not implement this roadmap as one
> sweeping change.

**Goal:** Simplify junoscfg by removing duplicated conversion paths and reducing
maintenance surfaces without weakening correctness or compatibility.

**Architecture:** Preserve the dict IR as the single conversion boundary.
Consolidate behavior before deleting compatibility wrappers, and treat each
roadmap item as an independently testable change.

**Tech Stack:** Python 3.10+, Click, PyYAML, pytest, OpenSpec, agent-ready.

**Spec:**
`openspec/changes/archive/2026-10-08-save-simplification-plan/proposal.md`

## Global Constraints

- Preserve `convert_config`, `validate_config`, `Format`, and
  `FieldValidationError` for the production Ansible consumer at
  [https://github.com/dg-i/ansible-collection-junos-config](https://github.com/dg-i/ansible-collection-junos-config).
- Respect the beta API and CLI deprecation rules before removing exports.
- Ask for a named device artifact before changing accepted Junos syntax.
- Keep the package offline and retain the dict IR as the sole interchange form.
- Run the full suite and all repository gates for every implementation change.

## Review Focus

- Identity conversions must still normalize without losing content.
- XML, JSON, YAML, set, and structured inputs must produce equivalent IR.
- `--path` and `--relative` must retain identical output semantics.
- Library calls must never emit unaddressable terminal output.
- Custom and bundled schema artifact resolution must remain isolated.

## Roadmap

### 1. Collapse conversion dispatch

- [ ] Replace the 20 private format-pair wrappers in `junoscfg.__init__` with
  direct, table-driven dispatch to the unified pipeline.
- [ ] Preserve every supported pair and the current public signature.

### 2. Centralize format detection

- [ ] Add one classifier with explicit per-caller accepted-format policies for
  conversion, validation, and audit; do not widen an existing public contract
  merely because the shared classifier recognizes more formats.
- [ ] Pin JSON, XML, YAML, set, structured, empty, and ambiguous inputs with
  characterization tests, including flow-style YAML beginning with ``{`` and
  an explicit parse-confirmed classification or ambiguity error.

### 3. Remove redundant conversion shims

- [ ] Delete the unused JSON-to-YAML helper.
- [ ] Remove the XML-output module stub while preserving the documented
  `NotImplementedError` through both `convert_config(..., to_format=XML)` and
  the exported `junoscfg.convert.from_dict(ir, "xml")` package door.

### 4. Convert XML directly to the IR

- [ ] Make the existing XML walker return the dict IR directly.
- [ ] Remove the XML-to-YAML-to-dict serialization round trip after parity
  tests pass.

### 5. Filter once at the IR boundary

- [ ] Select `--path` subtrees before rendering instead of reparsing each
  output format.
- [ ] Deprecate exported format-specific filters before their permitted
  removal.

### 6. Return structured diagnostics

- [ ] Add an opt-in structured-result API alongside the existing
  string-returning `convert_config` and `junoscfg.convert.pipeline` APIs, then
  replace library-side `stderr` writes with diagnostics carried by that result.
- [ ] Keep both existing package-door return contracts, CLI wording, and exit
  codes stable while the CLI becomes the sole renderer of warnings.

### 7. Reduce documentation and workflow surface

- [ ] Generate CLI option reference from Click and publish only supported
  package-door APIs.
- [ ] Measure OpenSpec artifact readership for one release, then propose
  deleting only artifact types with no recorded readers.

## Verification for Every Change

- [ ] Add or update characterization tests before implementation.
- [ ] Run `uv run pytest tests/ -q`.
- [ ] Run Ruff, deptry, tach, interface, stage, and documentation checks.
- [ ] Commit and review each roadmap item independently.
