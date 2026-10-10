<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Immutable platform constraints (harness, organisation policy DG-i) | every action; no credentials, personal or operator data in output | 1 | yes | device captures are read, never copied; tests use the `AGENTS.md` test-data values; nothing from `private_test_data/` enters a tracked file |
| Runtime (Claude Code, model `claude-opus-5-5`, unattended Builder subagent of the nightly orchestrator) | tool access; roles | 2 | partial: the Builder cannot be its own Test/Challenge or Reviewer | the orchestrator runs those roles as fresh agents at STOP-T and STOP-R (builder brief) |
| Invoked skill `agent-ready-change` (`SKILL.md`, `batches.md`, phase files) | lanes, phases, roles, gates | 3 | yes | standard lane, type `bug`; one coherent change (C3) |
| Repository `AGENTS.md`, `ARCHITECTURE.md` (§1 correctness, §8 layering), `tests/CONTRACT.md`, `src/junoscfg/{display,convert,validate}/CONTRACT.md`, `tach.toml`, `pyproject.toml` `[tool.template.*]` | house rules, evidence hierarchy, layer DAG, stage `beta`, version rules | 4 | yes | fix at the owning layer (the curly lexer in `display/set_converter.py`); `validate` may not import `convert` (C4); patch or minor per surface |
| Owner instructions: `private_test_data/makeover-work/builder-brief.md` and its intake answers of 2026-10-11, the mission `private_test_data/niglty_makeover_propmt.md`, the plan `private_test_data/makeover-ledger.md` row 1 | IDs OPEN-1 (=NEW-A1), NEW-B6, DEV-18, OPEN-10, NEW-B5; assurance; integration; unattended approvals | 5 | yes | assurance `balanced`; branch `change/structured-one-line-blocks`; fast-forward into local `master`, archive, tag, never push; this change carries the run's working ledger (`ledger.md`) |
| Approved specifications and decisions: `openspec/specs/conversion/curly-meta-tags`, `conversion/diagnostics`, `validation/set-command-validation`; `docs/decisions/2026-10-09-scope-compatibility-to-production-consumer.md`, `2026-10-10-commit-device-captures-as-the-oracle.md` | what structured input, diagnostics and the secondary doors promise | 6 | yes | `SetConverter`, `StructuredValidator`, `JunosValidator` are secondary doors: they may change in a minor release, so a deprecation is the conservative step |
| Acceptance and contract tests: strict xfails in `tests/unit/display/test_set_converter.py` (3, OPEN-10); `tests/contract/test_every_door.py`; the device law `tests/corpus/test_device_renderings.py` with `known-differences.json` | the oracle | 7 | yes | extended, never weakened; `omitted-block-emitted` leaves only through `tools/device_differences.py` |
| Observed behaviour on `a19e978` (`private_test_data/makeover-work/structured-one-line-blocks/p1.py`, `p2.py`, synthetic values) | structured input and validation | 8 | yes | one-line blocks convert to nothing silently; `a; b;` on one line and a trailing `## x; y` or `/* a; b */` comment fold into a value; `} x {` drops the block; the `{ /* OMITTED */ }` placeholder becomes a set line; unbalanced braces pass silently; `validate_structured` rejects `hold-time up 2000 down 0;` |
| Device evidence: `tests/data/device/synthetic/{vmx-23.2R2-S7.5,qfx5120-25.2R2-S1.5}/junoscfg-oracle.*` | the `apply-flags omit` placeholder; one-line container statements | evidence, above the schema model | yes | the device's curly prints `system { /* OMITTED */ };` for a group with `apply-flags omit` and `hold-time up 2000 down 0;` on one line; its display set prints the two hold-time leaves as two lines |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Mission prompt "dedicated `codex/` branches" versus owner intake 8 "`change/<slug>`, not `codex/`" | automatically resolved by precedence | Builder: the later, explicit owner answer wins | branch `change/structured-one-line-blocks` |
| C2 | Skill phase approvals by the owner versus an unattended run | automatically resolved by precedence | Builder: each approval reads "approved under the owner's unattended-run instruction of 2026-10-11" (brief) | phases progress without a relay |
| C3 | Five IDs versus `batches.md` (one coherent change needs one outcome and one acceptance story) | automatically resolved by precedence | Builder: one outcome, "structured text is read by one token lexer, and nothing it holds vanishes": OPEN-1, NEW-B6 and DEV-18 are the lexer; NEW-B5 and OPEN-10 are the second reader of curly text (validation through the schema-free `to_set()`) | one change, one review |
| C4 | Inventory fix sketch for NEW-B5/OPEN-10 ("route `validate_structured` through `structured_to_dict` + `dict_to_set`") versus `tach.toml` and `ARCHITECTURE.md` §8 (`validate` may not import `convert`; widening a boundary is a human decision) | automatically resolved by precedence | Builder: curly validation is composed at the surface, which may import both packages; the validate package's own structured doors (`StructuredValidator`, `JunosValidator.validate_structured`) cannot reach the schema walk, so they are deprecated with `SetConverter.to_set()`, behaviour unchanged until removal in the next minor | no new import edge |
| C5 | Inventory sketch "validate through the IR and the set writer" versus executed evidence (`p2.py`): the IR route accepts `description a b c;` (the walker joins the tokens into one quoted value) and rejects `overload timeout 300;` (writer defect DEV-2) | automatically resolved by precedence (inventories are leads, `AGENTS.md`: device and observed evidence outrank) | Builder: validation checks the input's own tokens, split into set statements exactly where the conversion walk starts a sibling | no new false acceptance or rejection from writer defects |
| C6 | Mission "never remove a strict xfail without fixing its cause" versus deprecating `to_set()` | automatically resolved by precedence (owner brief: "fix it or deprecate it") | Builder: the two `to_set()` strict xfails stay; their reasons name the deprecation and the removal | OPEN-10 closes as deprecated; removal is a recorded follow-up |
| C7 | Owner brief "patch for a bug" versus `agent-ready lane`, which requires a `declared-break` entry for any edit under `src/junoscfg/__init__.py` or `cli.py` (the version string included) | owner decision required (underneath: the gate cannot tell a version bump from a surface change) | owner, at the end of the run. Interim, the precedent of v0.15.1/v0.15.2 (meta-tag changes A and B, accepted as patches): `declared-break` entries name the behaviour fixes and their migration, the bump is a patch | lane passes; the owner may raise it to a minor |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Owner-confirmed preference: balanced (owner intake answer 1, 2026-10-11)
- Mandatory risk floor: high. The change crosses domains (kernel, conversion, validation, surface) and touches both named surfaces' files. Required whatever the preference: independent Test/Challenge after phase 4 (STOP-T) and a fresh Reviewer at least as capable as the Builder after phase 5 (STOP-R); every acceptance test fails on the merge base; one full check before review; `agent-ready lane`, `fields`, `reconcile`; OpenSpec strict validation; `known-differences.json` regenerated only by `tools/device_differences.py`.

## Owner decision batch

None asked: the owner is asleep and the run is unattended. Intake answers 1–8 settle assurance, integration, challenges and evidence; C7's interim action follows the accepted precedent and is reported at the end of the run.

## Delta log

<!-- Append later instructions or evidence and their consistency result. -->

- Initial preflight: consistent; C1–C6 resolved by precedence, C7 interim per precedent. Approved under the owner's unattended-run instruction of 2026-10-11.
