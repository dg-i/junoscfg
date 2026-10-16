## Why

The owner ruled on 2026-10-16, relayed verbatim by the coordinator: "add the found issues to
the BACKLOG". The reviews of own-crash-fixes (v0.28.23) and device-validation (v0.28.24) left
findings pending with the owner, and both say nothing is backlogged without the owner. Each
finding now gets one entry in `docs/BACKLOG.md`, with the ruling and the interim behaviour the
review recorded as in force.

## What Changes

- Eleven new top-level entries in `docs/BACKLOG.md`, after YAML-BREAKS-001 and before
  "Consolidated issue inventory": RELATIVE-TAGS-001, LEAF-LIST-VALUE-TAGS-001,
  ANCESTOR-TAGS-001, SCHEMA-LEAF-VALUES-001, VALIDATE-MESSAGES-001, JSON-KEYWORD-ALIAS-001,
  RENAME-EVIDENCE-001, READER-TREE-001, UNDOCUMENTED-001, HOLD-TIME-001 and VERB-PREFIX-001.
  Each keeps its review IDs qualified by change slug, a reproducer or the device question, and
  the probe section of `private_test_data/device-probe-2026-10-16/README.md` that settles it.
- Four existing entries extended: YAML-BREAKS-001 (own-crash-fixes TC7, keys), DEVICE-EVIDENCE
  (device-validation B1), MAKEOVER-19 (device-validation B2), XML-INPUT (device-validation B3).
- A changelog fragment `changelog.d/+backlog-open-findings.doc.md`.

Reader: a contributor or the owner who selects a backlog item, or answers a device probe, and
must reproduce the finding from its entry and the linked review. Sources: `docs-plan.md`.

## Capabilities

### New Capabilities

### Modified Capabilities

None: documents only, `skip_specs: true`.

## Non-goals

- Fixing any finding, or changing an interim behaviour: code, tests and specs stay as they are.
- device-validation P1, P2, P3, A5 and R2-A2: implemented choices or recorded-only notes.
- own-crash-fixes SC4: already YAML-DATE-001. Running the device probe.

## Impact

`docs/BACKLOG.md` and one changelog fragment; no code, test, configuration or spec.
