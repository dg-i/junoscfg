<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Phase 4 — Gates

## Outcome

`.copier-answers.yml` committed, which every later `copier update` reads; the
template's shipped check set installed and running on commit; `tach.toml`
derived; every gate the repository cannot yet pass in warn mode with a
committed baseline and an expiry date; the CI workflow in place where there is
a hosting platform to run it. `agent-ready gates` passes.

GitHub and GitLab run the same `uv run --locked --group dev --with griffe
--with tach --with towncrier --with vulture agent-ready check --set full --base
<target-ref>` command. It includes hooks, tach, OpenSpec validation, internal
gates, and tests. Run it locally before enabling CI. The gates are what `agent-ready check
--set fast` runs, the three stage gates among them: `agent-ready stage` with no
tool runs griffe, towncrier and vulture, and each one fails. `lane` reads red
on the onboarding branch until phase 7's first change opens a folder: the diff
carries governed files and no live change, which is what the gate refuses.
When the application has an existing
test adapter, declare its argv under `[tool.template]` as `test-command`; the
full set runs it and the fast set defers that environment-heavy command. GitLab
scheduled updates need CI job token push access to create `update/template`.

## Greenfield

The project arrived complete from `agent-ready init`, answers file included. `uv
lock` pins the check package from the template repository at the `checks-v*`
tag `[tool.uv.sources]` names; `agent-ready render codeowners` and `agent-ready
render toolbox` write the two generated files; the fast set runs green. A
skeleton that cannot pass its own gates has a bug in the gates.

## Brownfield — integrate and activate after validation

Keep the application's existing check adapter, test and acceptance commands,
canonical sources, hooks, CI, instruction files, and measured limits. Add
agent-ready fast and structural checks to the existing adapter; keep its native
acceptance route in the full set. `[tool.template].test-command` is argv for a
non-recursive native test or acceptance leaf. If the adapter calls `agent-ready
check --set full`, its test subcommand must not call full again. Fast never
substitutes for native acceptance. Run in the environment the application
requires, including containers.

Template caps are proposals. Preserve a measured local cap and its reason;
record new debt in approved baselines with expiry. Keep local safety checks.
Run `tach sync` during this bootstrap after the owner approves the boundary.
The seeded hook set has no type hook: run mypy in CI behind a dated decision
record and add the hook once it passes. ERA001 reads a `# Word: value` comment
as code; reword the comment, never suppress the rule.

Only after fast checks, gate and baseline validation, native acceptance, and
portable full pass in the required environment may hooks or hosting activate.
Merge invocations into existing CI jobs and hook configuration. If CI is absent,
enable only the owner-approved host in Copier answers; all other hosting stays
off. Existing CI files remain application-owned even when explicit workflow
flags are enabled. Remote branch protection requires separate verification.

For each gate that fails:

1. Run the gate and read the whole list with the human.
2. `agent-ready caps --write-baseline`, `agent-ready interfaces --write-baseline`,
   or the equivalent for that gate, to record today's debt; undeclared, the
   gate writes `.agent-ready/<gate>.json` and prints the stanza to add.
3. Declare the gate in `[tool.template.gates]` with `mode = "warn"` and the
   expiry date the human commits to.

From then on a violation absent from the baseline fails from day one, a
baselined one that gets worse fails too, because a baseline records a debt and
not a licence, and everything fails when the expiry passes.

This is where `tach sync` runs, and the only place: outside bootstrap it is out
of the agent's reach, because widening a boundary is a human decision under
review. Derive `tach.toml` even when phase 1 found the graph clean; it is the
one independent check on that reading. Do not baseline a cycle: record it in
`tach.toml` as declared debt under the same expiry, visible as a decision.

Where the remote is a directory rather than a hosting platform, there is no CI
and no CODEOWNERS review: the hooks are the whole enforcement and approval is
the human's commit, and `docs/how-to/work-with-agents.md` says so when phase 7
writes it, so nobody reads the rendered `CODEOWNERS` as a gate. The diff-reading
gates compare with the change's own base, the branch point with the local
default branch or the commit that opened the one live change; `base` under
`[tool.template]` is the fallback for a tree with neither, never a remote ref.

## Questions you must ask

1. For each warn-mode gate: what date do you commit to? Warn mode with no expiry
   is a configuration error, and a date nobody chose is a date nobody meets.
2. Is any of this debt deliberate? Deliberate debt gets a decision record, not a
   baseline entry: `agent-ready scaffold decision <slug>` writes it and
   `agent-ready decisions` fails until its fields are answered.
3. Which gate should start in enforce mode despite the noise, because a new
   violation there is genuinely unacceptable?

## Approval

The human approves the gate set, each baseline, and each expiry date. A cap is
raised in this phase only by a decision record naming its measurement. Stop here: the next phase is a new session, and `agent-ready status` resumes it.

## Verification budgets and quality

Use `docs/how-to/improve-verification.md` to initialise `docs/VERIFICATION.md`.
Agree separate baseline, accepted budget and target for each feedback stage,
plus behavioural assurance, reliability and corpus organisation targets.
Greenfield values are provisional; brownfield values use representative existing
evidence or measured commands, with missing evidence explicit. Preserve local
test structure and improve incrementally; urgent structural repair needs evidence
that reliable verification is prevented. Ask the owner to settle unresolved
budgets, critical risks, tolerances and selected gap owners with the gate decisions.
