## Why

Name-wide Group-H hints omit keyworded leaf names and silently drop nested content under unrelated trigger containers (NEW-A-S1, DEV-2, DEV-3, NEW-B2, NEW-B3).

## What Changes

Correct positional metadata at its XSD owner: flat positional hints apply only where the node actually declares nokeyword, preserving freeform keywords.
Scope flat-dict trigger metadata to event-options policy within trigger, including its copied groups path; retain its currently supported after/count behavior.
Make flat emission decline unsupported child shapes so normal traversal retains every nested child.
Regenerate bundled artifacts through the public schema generate command; measure changed slots and device outputs; regenerate only owned known-differences from captures.
**BREAKING** consumer and CLI output now retains previously omitted keywords and nested trigger content; reconvert originals and update output expectations.
No override, fallback, environment read or new parameter is added.

## Capabilities

### New Capabilities

- `schema-pipeline/conversion-hints`: contextual metadata for positional leaves and flattened trigger containers.

### Modified Capabilities

- `conversion/writers`: additive keyword and nested-content preservation requirements.

## Non-goals

DEV-V6 trigger Set equivalence remains evidence-blocked; preserve current event-options flattening. No wildcard/group feature expansion, keyed-list repair, hidden-list repair or canonical IR redesign.

## Impact

Schema fixes and shared DictWalker own the repair; grammar/artifact consumers and all five reader formats/four writer formats supply validation. Generated files and count docs change only through real generation/evidence. Independent Test/Challenge and Reviewer are required. Real full schema verification is deferred by the owner schedule ruling; ordinary full later requires admission. Approved under the owner's unattended-run instruction of 2026-10-11.
