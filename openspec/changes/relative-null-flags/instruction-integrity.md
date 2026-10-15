## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Synthetic values only; no credentials or personal data in records |
| Owner ruling 2026-10-15 on PO-1, relayed by the Orchestrator | This change | Owner | yes | Fix as its own change: relative JSON output writes `[null]` where absolute output does; regression test observed failing first; state the user-visible effect; decide and record whether it is a break; unattended; local merge, archive, tag; no push |
| AGENTS.md, ARCHITECTURE.md | Repository | Repository | yes | Equivalent-not-identical output, fix at the owning layer, version rule, doors, test data conventions |
| agent-ready-change skill, batches.md and phases | Workflow | Skill | yes | Two changes from this batch (this one, then the yaml-new alias policy); standard lane, tests first, one full checkpoint, fresh Reviewer |
| docs/how-to/run-a-batch-of-changes.md, docs/how-to/verification-evidence.md | Evidence procedure | Repository | yes | Device before/after comparison, PYTHONDONTWRITEBYTECODE, readiness declaration in `.agent-ready/activation.json` |
| src/junoscfg/convert/CONTRACT.md, tests/CONTRACT.md | Modules, tests | Repository | yes | Writer purity, one IR, tests through package doors |
| openspec/specs/conversion/path-filtering, conversion/writers, conversion/junos-json-yaml | Approved specs | Specs | yes | Relative output is the selected subtree; the JSON writer spells flags `[null]`; yaml-new equals JSON output, relative selections included |
| Archived review `openspec/changes/archive/2026-10-15-yaml-new-format/review.md` (B7, PO-1, C8) | Evidence | Evidence | yes | The failure and its probe; C8 stays an open device question |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Owner: "the fix lane fits if it is one failure mode"; `[tool.template.fix-lane]` caps a fix at 2 files outside the change folder, and strategy-a admission needs this branch assessed in `.agent-ready/activation.json` on the branch (no loose master commits), a third file | automatically resolved by precedence | Builder; run the standard lane as type `bug`, which the owner's permission does not forbid and the cap requires | More records (delta, freeze, metrics); same single failure mode |
| C2 | Batch how-to puts worktrees in `../junoscfg-wt`; owner says `/private/tmp` | automatically resolved by precedence | Builder; `/private/tmp/junoscfg-relative-null-flags`, branch `change/relative-null-flags` | Location only |
| C3 | Batch how-to: Builders do not bump, archive on the branch; owner: Builder merges `--no-ff` into master, archives and bumps there, as `ea18fab` did | automatically resolved by precedence | Builder | Finalisation order |
| C4 | path-filtering spec: "preserve the existing relative ... output semantics"; owner ruling changes relative JSON output | specification/test disagreement | Owner ruled; the delta adds the requirement that relative output spells flags as absolute output does | Spec delta |
| C5 | Relative output of a selected mapping also skips schema-context scalar-leaf coercion (`class: ["super-user"]` stays a list relative, a scalar absolute; probe in the freeze) | owner decision required | Not in the ruling, which names `[null]`; a context-dependent second behaviour; reported to the owner as a pending decision with a recommended default, not acted on | Out of scope here |
| C6 | Device question C8 (QFX5120 25.2R2-S1.5 and `[null]` for `system services netconf ssh`) is open | owner decision required | Owner has not ruled; no device claim is made; this change only makes relative output match the absolute output junoscfg already writes | Reported, not acted on |

## Assurance

- Standing preference: economy
- Standing record: `pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; keys matched: `default`, `zones`
  (none for conversion).
- Required roles: Builder; independent Test/Challenge (fresh agent); fresh isolated
  Reviewer at least as capable as the Builder; Finalizer (Builder, bounded).
- Application policy: AGENTS.md Verification; device before/after comparison for a writer change.
- Mandatory risk floor: high. The output of `convert_config` and `junoscfg convert --path
  --relative`, both named surfaces (`consumer`, `cli`), changes; zone conversion (yellow).

## Execution checkpoint

Base `ea18fab544a055935abaab09f6b550b1d889c049` (master, v0.28.16). Standard lane, type
bug (no design phase). Command: `uv run --locked --group dev --with griffe --with tach
--with towncrier --with vulture agent-ready check --set full --base ea18fab`; schema tiers
only if selected. Cadence: invitation already pending at `5ec3682`; no new assessment.
Integration: merge `--no-ff` into master, archive commit with patch bump (pyproject.toml,
`src/junoscfg/__init__.py`, uv.lock), VERIFICATION.md note, activation park, annotated
tag; no push. The next change (yaml-new alias policy) branches from the updated master.

## Owner decision batch

None blocking: the owner ruled on PO-1; C5 and C6 are reported, not asked, because neither
blocks this change.

## Delta log

- Initial preflight: consistent after C1 to C6. Resume: phase 1 proposal.
