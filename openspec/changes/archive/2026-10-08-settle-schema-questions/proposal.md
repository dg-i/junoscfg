## Why

Four defects reached a release this session because a question that a device
could have settled was inferred instead:

- A policy expression was assumed to need tokenising. The device's own
  `| display json` showed one opaque string, and junoscfg already produced
  exactly that — only the grammar was wrong.
- `EXPRESSION` was then added to every value slot rather than the 159 that
  carry the type. `set system host-name (foo bar)` validated for two releases.
- Oneliner lists were assumed uniformly keyword-first. Measured, that took
  rejections from 507 to 1,025.
- A whole-configuration capture was requested when a named subtree would have
  answered the question, pulling user accounts and secrets into a file that
  did not need them.

None was a hard problem. Each was a guess that a two-minute capture would have
replaced, and in three of the four the measurement that would have caught it
was available before the commit.

## What Changes

- `docs/how-to/settle-a-schema-question.md`: the four rules, each with the
  worked example from this session that cost something, plus the exact capture
  commands and the three renderings' known disagreements.
- A six-line section in `AGENTS.md` pointing at it, within the 100-line cap.
- `mkdocs.yml` nav entry.

## Capabilities

### New Capabilities

None; this is process documentation.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Enforcing any of it in a gate. There is no check that can tell an inference
  from a measurement; this is a rule people follow or do not.
- Rewriting `conversion-bugfix-guide.md`, which routes symptoms to layers and
  remains correct. This sits beside it and answers a different question: not
  where a fix goes, but how to know what the fix is.

## Impact

Documentation only; no runtime code. The rules are stated where an agent reads
them before editing, and the evidence for each is a defect in this repository's
own history rather than a general principle.
