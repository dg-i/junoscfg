## Why
Device-backed keyed singleton entries are modelled as containers, so valid device lines are rejected and inactive keys repeat. An unrelated container with a child named name is consumed as an entry and loses sibling content.

## What Changes
- Correct keyed singleton classification at the schema owner using declared positional identifier evidence; reuse existing list reader/writer branches.
- Restrict the shared writer's name fallback to an unavailable schema node; known containers keep all children.
- **BREAKING**: affected singleton IR dictionaries become one-entry arrays; consumer/CLI output corrects omitted siblings and repeated inactive keys.
- Preserve complete/incomplete key handling and existing true list behavior; add device-backed catalogue rows and negative container controls.
- No new override, parameter, environment read or dependency is introduced.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `schema-pipeline/entry-key-fields`: keyed singleton classification, preserving children and identifier order.
- `conversion/entry-keys`: all readers/writers retain singleton entry keys and entry tags without consuming ordinary container children.

## Non-goals
- Unkeyed homogeneous tunnel encapsulation, new second-entry cardinality guarantees, hidden-list names, whole IR normalization, and oneliner layout.
- P1/P6/P7/P8 unanswered device cases and unresolved DEV-V6 trigger equivalence; preserve existing behavior.
- Old entry-keys/flat-entries branch integration; workflow redesign and real full schema execution.

## Impact
Schema/conversion domains, named consumer/CLI surfaces; no public symbol removal. Scope: DEV-1/8/9, NEW-B1/B4, OPEN-5/21,56 historical OPEN-14 lines, meta-tag F1.
Current base public probes and shipped slot scan are retained privately in makeover-work/keyed-single-entry-lists/base-probes.json:692 candidate slots,366 homogeneous; inventory counts remain historical until independently verified.
Implementation, overlap with #15 set_input, serialized generation and known-differences changes wait for #15 integration, rebase, independent Test/Challenge, root ruling and admission.
