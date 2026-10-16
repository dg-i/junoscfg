## Reader and task

- Reader: a contributor or the owner who selects a backlog item, or who answers the device
  probe of 2026-10-16.
- Task: from one entry and the review it links, reproduce the finding, know the interim
  behaviour in force and the owner's ruling, and know which evidence would settle it.

## Authoritative sources

| Claim | Source |
|---|---|
| The owner's ruling "backlog", 2026-10-16 | owner request relayed by the coordinator (`instruction-integrity.md`, C1) |
| own-crash-fixes SC1, A1, A2, A3, C3, SC3, TC7 and their interim behaviour | `openspec/changes/archive/2026-10-16-own-crash-fixes/review.md` |
| device-validation SC1, SC2, SC3, R2-A1, R2-A3, A3, A7, D1 to D5, P4, B1 to B3 and their interim behaviour | `openspec/changes/archive/2026-10-16-device-validation/review.md` |
| Each reproducer's output at 716a9d1 | `private_test_data/makeover-work/backlog-open-findings/probes-716a9d1.txt`, from `run-probes.sh` beside it (synthetic inputs, local provenance) |
| Which probe section answers which item | `private_test_data/device-probe-2026-10-16/README.md` (synthetic; named as local provenance, never quoted) |
| Test names an entry cites | the test files at 716a9d1 (`git grep` on each name) |
| hold-time capture finding | `tests/data/device/expected-findings.json` (`mandatory-open`) |
| The NAT rename has no node in the shipped QFX schema | the probe README's section C note, and `src/junoscfg/validate/data/junos-structure-tree.json.gz` |
| The generic validation message and its reach | `src/junoscfg/validate/json_yaml_validator.py` `_message`; keyword count over the shipped JSON and YAML schemas (C4) |

## Affected documents

- `docs/BACKLOG.md`: it is the declared backlog destination ("Authoritative destination: this
  file"). New entries go after YAML-BREAKS-001, in the same shape; four existing entries gain
  one bullet each instead of a duplicate entry.
- `changelog.d/+backlog-open-findings.doc.md`: the stage gate wants a fragment; type `doc` as
  input-trust-rule used.

## Documentation QA

- Links and anchors: `uv run --locked --group docs mkdocs build --strict` reports no warning
  outside `BACKLOG.md`, and every warning beyond the 48 of master is a `BACKLOG.md` link to a
  file outside `docs/`, the class the existing entries already carry; each such target exists
  (`ls`).
- Commands and examples: every reproducer an entry names runs at the change head with the
  result the entry states (`run-probes.sh`, compared with `probes-716a9d1.txt`).
- Referenced paths: every repository path and test name the new text names exists
  (`ls` and `git grep -n`).
- Terminology: each new entry carries "Owner ruling 2026-10-16: backlog", its review IDs
  qualified by change slug, and the five fields Status, Finding and impact, Reproducer or
  Evidence, Proposed direction, Source change (`grep`).
- Coverage: every pending item the brief names appears exactly once as a new entry or an
  extension, and P1, P2, P3, A5 and R2-A2 appear in no entry (`grep` per ID).
- Privacy: no new text quotes `private_test_data` content; the probe README is named by path
  only; values are synthetic (AGENTS.md Test Data Conventions).
- Diátaxis placement: not applicable, because the backlog is a status record, not one of the
  four documentation kinds; no new page.
- Rendered output: markdownlint passes on the changed documents (pre-commit).
- One full checkpoint passes.
