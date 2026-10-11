<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values in output | 1 | yes | tracked text holds synthetic values only (`router1`, `example.net`); nothing is pushed, no external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, Builder subagent of the batch orchestrator (lane D, wave 2), scratchpad | tool access | 2 | yes | the orchestrator runs any independent role; this Builder finishes through phase 7 bookkeeping when none is required |
| Skill `agent-ready-change` v0.9.0 (`SKILL.md`, `batches.md`, phase 0, `types/docs.md`) and the lane gate of `agent-ready-checks` 0.15.11 | lanes, phases, gates | 3 | yes | docs lane: `skip_specs: true`, `docs-plan.md`; the gate accepts only `.md/.mdx/.rst/.txt` and images outside the change folder (C3) |
| `AGENTS.md`, `ARCHITECTURE.md`, `pyproject.toml` `[tool.template.*]`, `docs/how-to/run-a-batch-of-changes.md` | house rules, zones, stage (beta), worktree, versioning, serialized paths | 4 | yes | worktree `../junoscfg-wt/docs-corrections`; no version bump on the branch; no serialized path; device claims cite capture, family and release |
| Owner instructions, 2026-10-11: nightly makeover intake (`private_test_data/makeover-work/builder-brief.md`, `builder-kickoff.md`) | scope, approvals, no questions, coordination | 5 | yes | every approval recorded as "approved under the owner's unattended-run instruction of 2026-10-11" |
| Orchestrator task for ledger row #22 (NEW-C7, NEW-C8, NEW-C14), lane D | scope, coordination with live Builders #7, #8, #9 | 5 (relays the owner) | yes | every claim verified at the checked head; a correction touching a live Builder's behaviour is written only if it stays true after that change |
| Main spec `openspec/specs/validation/set-command-validation/spec.md` (scenario "Lines the device rejected") | behaviour | 6 | yes | `system location dc-a` is invalid, as on the device (vMX 23.2R2-S7.5): the authoritative source for NEW-C7 |
| Tests under `tests/` (`tests/corpus/test_set_corpus.py`) | the oracle | 7 | yes | `CORRECTLY_REJECTED` holds `set system location dc-a`; `OVER_REJECTED` holds two hand-written lines with code `merged` (C4) |
| Observed: `git status` clean on `master` 13719d9; live worktrees `anonymize-embedded-values` (#7), `value-quoting-by-type` (#8), `xml-leaf-text-verbatim` (#9) and their `files.txt` | tree state, coordination | 8 | yes | C2, C5 |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Skill "ask once" and owner approval of the proposal versus the owner's unattended-run instruction of 2026-10-11 (no questions, owner away) | automatically resolved by precedence | Builder: the ledger row, the inventory evidence and the device evidence are the approved intent | no owner batch |
| C2 | Ledger row #22 assigns NEW-C8 (`docs/architecture/developer-guide.md:599`, "json/xml — not supported") versus the batch rule "two changes that edit the same file never overlap" and the kickoff's overlap stop: live Builder #7 (`anonymize-embedded-values`) lists `docs/architecture/developer-guide.md` (anonymization pipeline section) in its `files.txt` | automatically resolved by precedence | Builder: NEW-C8 is not edited here; the overlap is reported to the orchestrator; the verified one-line correction (JSON is filtered by `filter_json_by_path()` in `display/to_json.py`; only XML has no filter) is recorded for a change after #7 merges | NEW-C8 stays OPEN, blocked by the overlap |
| C3 | Ledger row #22 assigns NEW-C14 (`.pre-commit-config.yaml:20-23` describes a whole-package mypy hook that does not exist) to a `docs` change versus the docs-lane gate, which refuses every non-document suffix (`agent_ready_checks/lane.py` `DOCUMENT_SUFFIXES`); both fixes the inventory offers ("add the hook or fix the comment") edit the YAML file, and the choice between them is the owner's | automatically resolved by precedence (lane gate); owner decision required (hook or comment) | Builder: NEW-C14 is not edited here; reported for a non-docs change (`refactor`) with the owner's choice | NEW-C14 stays OPEN |
| C4 | Inventory lead for NEW-C7 ("swap the example for the `OVER_REJECTED` lines `set groups foo snmp location` and `set system name-server`") versus the evidence: `system name-server` is a keyed list (`L`, key `name`) and `snmp location` a value leaf (`l`, `xsd:string`) in the bundled tree, so both lines lack the entry name or value the model requires, the shape `CORRECTLY_REJECTED` calls malformed for `set system host-name`; no capture in `tests/data/device/` prints either bare line (both devices print `name-server <address>` and `snmp location "rack 4, row B"`), and no probe answers it | specification/test disagreement | Builder: the guide does not present either line as valid Junos; it states only what the code and captures show (the merge-by-name union, verified on `labeled-unicast`). New finding NEW-R20 (the test's `merged` classification) and device probe P14 recorded in `private_test_data/`; the test edit belongs to a non-docs change | the validation guide no longer lists a merged-rule over-rejection example |
| C5 | Live Builder #8 (`value-quoting-by-type`) regenerates the grammar and `tests/data/device/grammar-corpus.json` (rejected 66 → 65 at ef06855) without listing `docs/guide/validation.md`, whose "it rejects 66" then goes stale | automatically resolved by precedence (orchestrator rule: write only what stays true after the live change) | Builder: the sentence names the share ("fewer than one in a hundred" of 8,713, true for 66 and 65) and points at the corpus record instead of a count; every other value written (`router1`, `example.net`, `building "B 2"`) is unquoted or quoted identically under #8 (device captures print them so) | no overlap with #8; no later edit needed when #8 merges |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance` (`record = "docs/how-to/run-a-batch-of-changes.md#assurance"`), matched key `default`; `zones` is empty, no declared break, no trust boundary
- Zone: none owns `docs/guide/`; recorded as `surface` as in earlier zone-less docs changes
- Mandatory risk floor: not high (no red zone, no security or trust-boundary work, no migration, no declared break, no named public surface changes: two user guides' examples and one paragraph; one documentation slice). No Test/Challenge or Reviewer role is required. Unwaivable: the one full checkpoint, `agent-ready fields`, `caps`, `lane`, `openspec validate --strict`, markdownlint and the strict MkDocs build

## Owner decision batch

None, because the owner asked for no questions (C1); the only owner choice found (NEW-C14 hook or comment, C3) belongs to a change outside this lane and is reported, not decided.

## Delta log

- Initial preflight, 2026-10-11: scope narrowed to NEW-C7 (C2 overlap with #7 holds NEW-C8; C3 lane gate holds NEW-C14); C4 replaces the inventory's example lead with code- and capture-backed text; C5 keeps the validation paragraph true across #8. Approved under the owner's unattended-run instruction of 2026-10-11. Resume point: phase 1.
- Phase 1, 2026-10-11: proposal (NEW-C7 only), lane fields and metrics ledger approved under the owner's unattended-run instruction of 2026-10-11. Resume point: phase 2.
- Phase 2, 2026-10-11: `docs-plan.md` and `evidence-freeze.md` approved under the owner's unattended-run instruction of 2026-10-11; `files.txt` written (two guide pages and this folder), no overlap with a live Builder. Resume point: phase 4.
- Phase 4, 2026-10-11: QA tasks 1.1–1.7 approved under the owner's unattended-run instruction of 2026-10-11; baselines recorded (strict build exit 0; seven stale lines). Resume point: phase 5.
