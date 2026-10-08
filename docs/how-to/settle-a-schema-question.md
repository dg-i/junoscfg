# Settle a schema question

Four rules for anyone — human or agent — changing what junoscfg accepts.
They exist because each has already been broken here, at a cost.

## 1. Ask for a device artefact before inferring one

A question about what Junos accepts, or about the shape a statement takes, is
settled by a device. Ask for the subtree, in **set, JSON and XML**, and wait.
Do not derive it from the XSD, from another vendor's parser, or from what the
three renderings "must" agree on, because they do not:

| Disagreement | Where it shows |
|---|---|
| Junos wraps a statement it does not publish in `<undocumented>` | XML only |
| `enable-disable` renders as `disable` | JSON and set |
| A policy expression is one opaque string, not a parse tree | JSON settles it |

`set groups <name> chassis dump-on-panic` is the standing example: it sits
inside `<undocumented>` in the device's XML and appears in no NETCONF XSD at
any release, so no schema will ever model it. Only a capture shows it exists.

The four `apply-*` meta-statements are the other: `apply-groups`,
`apply-groups-except`, `apply-flags` and `apply-macro` appear nowhere in the
21.4R0, 23.2R2, 23.4R2 or 25.2R2 dumps — not as an element, not as a ref, not
as a substring — while every real configuration uses them.

## 2. Never request a whole configuration

Every capture request names a path. No `show configuration` without one, and
never `| display json` on the whole tree: it carries `system login user` with
its `$9$` and `$6$` hashes, `snmp community`, `radius-server secret` and
`system services ssh` host keys, none of which a parser question needs.

Ask for what the question needs and nothing else:

```text
show configuration policy-options policy-statement <name> | display json
show configuration forwarding-options analyzer | display set
```

Real captures live in `private_test_data/`, which is gitignored. Committed
fixtures use the synthetic ranges in `AGENTS.md`.

## 3. Fix at the owning layer, or record why not

A fix that compensates downstream for knowledge missing upstream must say so
in the change record, name the upstream owner, and state what would let it
move. `apply-*` is the worked example: the schema did not model it, so six
modules each worked around it separately — the set validator with three
regexes that cut the statement off the line before parsing, a quote-aware
guard so a `description` mentioning `apply-groups` survived that cut, and an
early return for the line those regexes reduced to a bare `set`. The schema's
*generator* models it now, the shipped artifacts do not yet carry it, so the
three compensations remain -- labelled a temporary bridge in the module
docstring, with two tests that go red together on the day they can go. That is
what "or record why not" looks like when the answer is "not yet".

## 4. Measure the blast radius before loosening

Any change widening what the grammar or the validator accepts states how many
nodes or slots it affects, and carries a negative test.

`EXPRESSION: /\([^\n]*\)/` was added to `QUOTED_OR_VALUE` to accept one policy
expression. `QUOTED_OR_VALUE` is written in 11,853 value slots of the generated
grammar, so `set system host-name (anything at all goes here)` validated.
Scoped by the XSD type reference `policy-algebra`, the same alternative reaches
159 slots. The number was available before the change and nobody took it.

The counterpart is a test that must stay red. `tests/test_set_validator.py`
ran entirely against a three-rule grammar, so every assertion in it was
positive, and a validator that accepts everything passes every positive test
there is. It now also runs against the artefact we ship, and
`tests/test_set_corpus.py` records each rejection by name so a new false
positive and a fixed one are both visible in the diff.
