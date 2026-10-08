---
status: accepted
scope: ["src/junoscfg/input.py", "src/junoscfg/convert/input/set_input.py", "src/junoscfg/validate/set_validator.py"]
enforced-by: tests
review-by: 2027-10-09
---

# Reject bracket shorthand in raw set input

## Context

Junos accepts interactive bracket lists, but its canonical `| display set`
output expands them into repeated commands. On 21.4R0 a VLAN members list was
accepted interactively, retained in structured output, represented as an array
in JSON and repeated elements in XML, but rendered as one display-set command
per member. On 23.2R2-S7.5 a quoted community list was accepted, deduplicated in
first-seen order and likewise rendered as repeated commands; an empty list was
a true no-op in every representation. Junoscfg's raw set reader is not
schema-aware enough to preserve those meanings and could instead construct an
incorrect IR.

## Decision

Raw set input intentionally supports canonical device-produced display-set
syntax, not interactive bracket-list shorthand. Every unquoted `[` or `]` is
rejected at the shared input boundary before IR construction; validation
reports the same condition as a normal line error. Quoted brackets remain
content, ignored comments remain ignored, and structured input continues to
accept bracket lists and emit repeated canonical set commands.

This exception is reviewed by 2027-10-09. Reopen it earlier only when a real
consumer provides sanitized device evidence and cannot provide canonical
expanded commands. If no such demand exists at review time, renew the
exception rather than automatically implementing bracket support.

If support is reconsidered, the deferred design is schema-aware and restricted
to leaf-list positions; accepts every delimiter-spacing variant plus quoted and
escaped items; removes duplicates while preserving first-seen order; treats
empty lists as valid no-ops that disappear during normalization; requires `]`
to end the command apart from whitespace; and always emits one set command per
value. Scalar bracket lists remain invalid. Bracket behavior for meta commands
remains deliberately unresolved until implementation and requires device
evidence. Rejection tests would then be replaced by bracket/repeated-input
equivalence and processing tests. This design is not a roadmap commitment.

## Consequences

Raw set ingestion fails loudly instead of risking a wrong IR, at the cost of
requiring callers with interactive syntax to expand it first or use structured
input. The distinct `INTENTIONALLY_UNSUPPORTED` corpus category keeps this
device-valid exclusion separate from malformed commands and accidental grammar
over-rejection.
