## Why

The owner ruled on 2026-10-15 that configuration input is trusted in every format: "whoever
writes malicious Juniper config can do far worse than wrecking the junoscfg process, so this
must be trusted input; therefore I do not want to fix yaml bugs here", and asked for the rule
in `ARCHITECTURE.md`. The yaml-depth-ceiling change recorded only a narrower YAML wording,
because the rule reached its Builder second-hand (its conflict C8).

## What Changes

- `ARCHITECTURE.md` section 8: a cross-cutting rule, "Configuration input is trusted, in every
  format", with the owner's reason, what junoscfg does not guard against, which own defects are
  still fixed, and that a caller with untrusted input bounds it first. The yaml-new paragraph
  points at it instead of restating a YAML-only assumption.
- A decision record `docs/decisions/2026-10-15-configuration-input-is-trusted.md`, and the
  rendered `docs/decisions/index.md`.
- Pointers to the record from the conversion guide, the `input` API page, the `input` and
  `convert` contracts and record 2026-10-15-yaml-nests-at-most-64-levels.

Reader: a contributor deciding whether to add a guard or limit, or a caller deciding whether
junoscfg protects them from hostile input. Sources: `docs-plan.md`.

## Capabilities

### New Capabilities

### Modified Capabilities

None: documents only, `skip_specs: true`.

## Non-goals

- Code and test docstrings and the main spec that say YAML "is not hostile" (C2, C3): true
  under the rule, outside the docs lane.
- The trusted-input review's owner questions (ceiling at the shared door, YAML-BREAKS-001).
- Own crashes the rule says to fix, reported by yaml-depth-ceiling as owner questions and
  found again by this change's Reviewer: legacy `yaml` input with a non-string key
  (`AttributeError` in `yaml_input.py`, its C5) and JSON nested about 1,500 deep
  (`RecursionError`, its C6). Code changes, outside the docs lane; reported to the owner.

## Impact

Documents and two module contracts; no code, test, configuration or spec.
