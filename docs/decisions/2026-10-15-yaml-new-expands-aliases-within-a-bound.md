---
status: accepted
scope: ["src/junoscfg/input.py", "src/junoscfg/convert/input/json_input.py", "src/junoscfg/convert/output/json_output.py", "src/junoscfg/validate/json_yaml_validator.py"]
enforced-by: tests
review-by: 2027-04-15
---

# yaml-new expands aliases within linear bounds

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
It refuses a mapping or list reached inside itself (kind `cycle`), and the outermost alias
whose expansion makes the written-out document hold more than twice the values the parsed
document holds, or nest deeper than the parsed document's deepest value (kind `alias`),
each at its path and never with the offending value. The count is per written-out value,
not per alias: every document reaching each value at most twice, no deeper than written,
passes; a document without aliases never reaches either bound. Both bounds are interim,
pending the owner (SC-2 and SC-A in
`openspec/changes/archive/*-yaml-new-alias-cycles/review.md`): the factor two is the
smallest that accepts a block reached twice, and together they keep every stage linear in
the loaded object and no deeper than an alias-free document, the property the earlier rule
had. Scalar aliases and merge keys are expanded by PyYAML while loading and are not
bounded here (SC-B). The reader then reads the document written out, the writer
checks the IR before building the object, and validation judges the object written out.

## Consequences

Hand-written yaml-new may share blocks through aliases. A file reusing one block many times
in a small document, or aliasing a block deeper than anything written, can pass a bound and
be refused; writing the block out, or a looser
bound the owner may choose, accepts it, and loosening is additive. A cyclic or bomb IR from
a caller now gets a `ValueError` from the yaml-new writer instead of a `RecursionError` or an
unbounded expansion. The legacy `yaml` format is outside this boundary: its reader still
recurses on a cycle and its writers expand a bomb, a separate decision for the owner.
