---
status: accepted
scope: ["src/junoscfg/**"]
enforced-by: none
review-by: 2027-04-15
---

# Configuration input is trusted

## Context

The yaml-new changes of 2026-10-15 added, then removed, bounds against YAML alias bombs.
The owner first ruled: "I do not want to fix PyYAML problems; if this is a genuine junoscfg
problem fix it, if not leave it." Asked whether the remaining limits were needed, the owner
then gave the reason that applies to every format, first-hand on 2026-10-15 (recorded in
the archived input-trust-rule change's `instruction-integrity.md`): "whoever writes
malicious Juniper config can do far worse than wrecking the junoscfg process, so this must
be trusted input; therefore I do not want to fix yaml bugs here", and asked for the rule in
`ARCHITECTURE.md`. `docs/reviews/2026-10-15-trusted-input-retirement.md` found that the
alias bounds were the product's only hostile-input protection.

## Decision

Configuration input is trusted in every format junoscfg reads. junoscfg adds no limits
(size, time) against hostile input such as alias bombs or resource exhaustion, and does not
work around a parser's limits on such input (PyYAML's alias expansion, its nesting failure
past about 490 levels). Defects in junoscfg's own code are still fixed: wrong output, a
silently dropped statement, or a crash or loop in its own processing, as the 64-level
ceiling and cycle refusal of 2026-10-15-yaml-nests-at-most-64-levels fix. A caller that
feeds junoscfg untrusted input bounds it before the call.

## Consequences

A proposed guard is first asked whose defect it answers: a crash or wrong result in
junoscfg's own code is fixed; amplification or a limit inherent to the input format or a
parser's handling of hostile input is not, and does not go to the backlog. Privacy is
unaffected: an anonymized run's messages keep withholding configuration values
(`tests/contract/test_every_message.py`), and anonymization is unchanged. A deployment that
accepts configuration from untrusted parties needs its own bounds; offering junoscfg as
such a service would reopen this decision.
