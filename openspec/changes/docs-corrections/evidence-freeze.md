## Resolved instructions

As resolved in `instruction-integrity.md`: docs lane, NEW-C7 only (C2 holds NEW-C8 behind the
live Builder #7's `developer-guide.md`; C3 holds NEW-C14 outside the docs lane), no owner
questions (C1), the guide states only code- and capture-backed claims (C4), and the validation
paragraph stays true when live change #8 merges (C5). Assurance `economy`.

## Requirements

None: `skip_specs: true`. The reader task in `docs-plan.md` is the acceptance target.

## Evidence

At master 13719d9 (`private_test_data/makeover-work/docs-corrections/probe_validate.py`):

- `validate_set`: `set system location dc-a` invalid; `set system location building "B 2"`,
  `set system domain-name example.net`, `set protocols bgp group RR family inet6 labeled-unicast
  per-prefix-label` valid; `set groups foo snmp location`, `set snmp location`, `set system
  name-server` invalid (the last three are a value leaf or keyed list with nothing after it).
- Captures (vMX 23.2R2-S7.5; QFX5120 25.2R2-S1.5), `junoscfg-oracle.set.gz`: `system location
  building "B 2"`, `domain-name example.net`, `snmp location "rack 4, row B"`,
  `name-server 192.168.0.53`, `family inet6 labeled-unicast per-prefix-label`.
- Bundled tree: `system name-server` `L` keyed `name`; `snmp location` `l` `xsd:string`;
  `system location` a container; `per-prefix-label` under `family inet labeled-unicast` only.
- Shipped grammar: both `labeled_unicast` variants offer `per-prefix-label` (merged-family union).
- `grammar-corpus.json`: 8,713 device lines, 66 rejected; 65 in #8's worktree at ef06855.
- Worked example rerun with `domain-name example.net`: JSON → YAML, YAML → curly, JSON → set and
  JSON → curly all exit 0; outputs recorded in `tasks.md`.
- Inventory lead C7 ("swap in the `OVER_REJECTED` lines") rejected on this evidence (C4); new
  finding NEW-R20 and device probe P14 recorded in the ledger and `makeover-probes.md`.

## Non-goals

As in `proposal.md`: NEW-C8, NEW-C14, and the test's `OVER_REJECTED` classification.

## Acceptance criteria

Every `docs-plan.md` QA item passes as recorded in `tasks.md`; `agent-ready check --set full`
passes once.

## Performance expectations

None, because no runtime code changes.

## Outstanding decisions

None, because the scope narrowing follows precedence (C2, C3) and the owner choice of NEW-C14
travels with that item, outside this change.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: normal (no red zone, break, trust boundary, public surface or cross-domain work)
- Roles required: Builder; Finalizer bookkeeping by the Builder; no Test/Challenge, no Reviewer
- Resume point: phase 4 (QA tasks); last valid evidence 13719d9 plus this freeze

## Delta log

- Freeze established: preflight 33227f5, proposal f9a588c, `docs-plan.md` and this file at the phase-2 commit; approved under the owner's unattended-run instruction of 2026-10-11.
