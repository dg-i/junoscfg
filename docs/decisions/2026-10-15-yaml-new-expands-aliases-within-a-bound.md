---
status: accepted
scope: ["src/junoscfg/input.py", "src/junoscfg/convert/input/json_input.py", "src/junoscfg/convert/output/json_output.py", "src/junoscfg/validate/json_yaml_validator.py"]
enforced-by: tests
review-by: 2027-04-15
---

# yaml-new expands aliases within a linear bound

## Context

yaml-new is the Junos JSON object spelled in YAML. YAML can share one mapping or list through
an anchor and its aliases; JSON cannot, and a file that shares a block means the same as the
file with the block written out at every place. A YAML parser keeps the sharing as one
object, so a cycle never ends and a few lines of nested aliases ("billion laughs") stand for
an exponentially large document. Until this record, yaml-new refused every mapping or list
reached a second time, which ended both dangers in linear time but also refused harmless
shared blocks. The owner ruled on 2026-10-15 (PO-2, SC-1 of the yaml-new-format review) that
only cycles are refused and denial-of-service protection stays.

## Decision

`junoscfg.input.find_non_json_value`, the boundary the yaml-new reader, the yaml-new writer
and yaml-new validation share, walks a shared mapping or list at every place it is reached.
It refuses a mapping or list reached inside itself (kind `cycle`), and an alias whose
expansion makes the written-out document hold more than twice the values the parsed
document holds (kind `alias`), each at its path and never with a value. Every document that
reaches each value at most twice passes; a document without aliases never reaches the
bound. The factor two is interim, pending the owner (SC-2 in
`openspec/changes/archive/*-yaml-new-alias-cycles/review.md`): it is the smallest bound that
accepts a block reached twice and keeps every stage linear in the parsed document, the
property the earlier rule had. The reader then reads the document written out, the writer
checks the IR before building the object, and validation judges the object written out.

## Consequences

Hand-written yaml-new may share blocks through aliases. A file reusing one block many times
in a small document can pass the bound and be refused; writing the block out, or a looser
bound the owner may choose, accepts it, and loosening is additive. A cyclic or bomb IR from
a caller now gets a `ValueError` from the yaml-new writer instead of a `RecursionError` or an
unbounded expansion. The legacy `yaml` format is outside this boundary: its reader still
recurses on a cycle and its writers expand a bomb, a separate decision for the owner.
