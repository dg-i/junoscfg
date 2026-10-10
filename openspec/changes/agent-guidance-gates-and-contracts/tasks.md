## 1. Verification

Every check runs against a named commit, in a detached worktree of that commit where the
check reads the tree (`git worktree add --detach <dir> <sha>`), so the owner's uncommitted
files are neither stashed nor read. "Deliverables" means the developer guide, the two
how-to pages, the four contracts, `main-spec-edit.md` and the `changelog.d` fragment.

- [ ] 1.1 Links and anchors: `uv run --locked --group docs mkdocs build --strict 2>&1 | tee
  build.log` in the worktree; expect exit 0, no `WARNING` line, and
  `grep -nE 'INFO .*(anchor|not found|unrecognized|absolute)' build.log` naming none of the
  three edited pages. The contracts and `main-spec-edit.md` are not built; 1.6 covers them.
- [ ] 1.2 Commands and examples: every `tests/…py::…` id in the deliverables, extracted
  across wrapped lines with abbreviated `::test_…` forms expanded and file paths separated,
  through `uv run pytest --collect-only -q <ids>`; expect exit 0 and no `not found` line,
  the id list in the evidence. `uv run pytest --help --color=no | grep -oE --
  '--(schema|jvd|regen-schema)\b' | sort -u | wc -l`; expect 3. `--regen-schema` is never
  passed to a dry run (conftest regenerates before collection).
- [ ] 1.3 Referenced paths: every repository path in the added lines of the deliverables,
  backticked or a link target, path part before `::`, through
  `git ls-files --error-unmatch`; expect every one tracked, a `private_test_data/` path
  allowed only beside the word "gitignored".
- [ ] 1.4 Terminology: "evidence hierarchy", "kept whole", "UNPLACED", "entry keys", "key
  choice", "nokeyword", "red zone" spelled as in `ARCHITECTURE.md`, `openspec/specs/`, the
  contracts, `docs/how-to/solo-review.md` and `pyproject.toml`; and the deny-list
  `git diff -U0 eb369dd -- <deliverables> | grep '^+' | grep -niE 'kept intact|left
  whole|unplaceable|keyword choice|choice keyword|danger zone|evidence (ranking|order)|source
  of truth'`; expect no hit.
- [ ] 1.5 Diátaxis placement: `git diff --name-only eb369dd..HEAD` outside the change
  folder lists only the deliverables; `git diff --name-only 01efe85..HEAD -- .agents/` is
  empty; `ARCHITECTURE.md` untouched; `git diff -U0 eb369dd --
  docs/architecture/developer-guide.md | grep '^+' | grep -nE 'outrank|device wins|must
  mean|correctness|evidence hierarchy|fallback|ranks'`: every hit is a pointer to
  `ARCHITECTURE.md`, none a restatement.
- [ ] 1.6 Rendered output: `uv run --locked --group dev agent-ready caps` exit 0 with every
  contract at or under 30 lines; ``awk 'length>84 && $0 !~ /`tests\//'`` over the four
  contracts prints nothing; `pre-commit run markdownlint --files <deliverables>` prints
  Passed, not Skipped, for the files the hook covers; `git diff --check eb369dd..HEAD` is
  silent; in the built site the tier section has `li` ≥ 6 plus the new entries and
  `grep -cE '<p>(- |\|)'` is 0 on the three pages.
- [ ] 1.7 Lane: `uv run --locked --group dev agent-ready lane --base master` in the
  worktree; expect exit 0 and `git status --short` in the main checkout unchanged.
- [ ] 1.8 Spec edit: `diff <(sed -n '5,$p' main-spec-edit.md) <(the sibling delta's
  requirement block)` shows only the five ids appended to the `Tests:` line; the 24 ids
  collect; the clause claims only what the five tests assert (1.16).
- [ ] 1.9 Full checkpoint, once, after the last change task is committed, in the worktree
  of that commit: `uv run --locked --group dev --with griffe --with tach --with towncrier
  --with vulture agent-ready check --set full --base master`; expected result: exit
  non-zero with exactly one failing check, `fields`, naming only `identifier-key-fields`
  (missing `assurance`), every other check passing. Any other failure blocks review.
- [ ] 1.10 Telemetry: base = full SHA of `2a3e025` (master tip and merge base; the range
  holds the owner's garden commit 01efe85, disclosed in `metrics.md`), head = the code
  commit; `uv run --locked --group dev agent-ready metrics
  agent-guidance-gates-and-contracts --base-sha <base> --head-sha <head>
  --workflow-telemetry openspec/changes/agent-guidance-gates-and-contracts/workflow-telemetry.json`;
  expect the import accepted, `grep -ciE 'estimat|approx' workflow-telemetry.json` = 0, every
  command entry carrying an observed duration, every other unavailable row `UNMEASURED`.
- [ ] 1.11 Tier bullets survive verbatim: split the old "When to use each tier" section
  (`git show eb369dd:docs/architecture/developer-guide.md`) into its 6 blocks,
  whitespace-normalised; expect each a substring of the new section: `6 old blocks; 0
  missing`.
- [ ] 1.12 Contracts keep everything: for each contract
  ``comm -23 <(git show eb369dd:$f | grep -oE '`[^`]+`' | sort -u) <(grep -oE '`[^`]+`' $f
  | sort -u)`` empty; every `## ` heading and the `Interface:` line survive; exactly one
  added `- ` bullet under `## Invariants` per contract; `## Precedent` bullet count unchanged.
- [ ] 1.13 Each new invariant's cited test asserts it: quote the assertion lines in the
  evidence (display: `test_the_helper_answers_the_key_tuple`,
  `test_statement_children_drop_the_key_fields`, `test_no_module_keeps_its_own_key`;
  validate: `test_a_numeric_max_occurs_is_list`; convert: `test_each_door_reports_it`,
  `test_each_structured_door_reports_it`, `test_a_partial_or_surplus_key_is_kept_whole`;
  anonymize: `test_an_enum_key_passes_unchanged`, `test_a_key_choice_keyword_passes_unchanged`).
- [ ] 1.14 Device-evidence form: on the added lines of `settle-a-schema-question.md`, every
  IPv4 address and AS number in the `AGENTS.md` ranges; prompts generic
  (`grep -nE '[A-Za-z0-9_-]+@[A-Za-z0-9_-]+[>#]'` at most `admin@router1`); no pathless
  capture (`grep -nE 'show configuration *(\||$)|show \| compare *($|\|)'` none), the
  preflight step naming a path; set, JSON and XML all required; raw output stays in
  gitignored `private_test_data/` and only the sanitised form enters `evidence-freeze.md`;
  no timing figure (`grep -nE '\b[0-9.]+ ?(ms|s|seconds|minutes)\b'` none); the "Four
  rules" opening line updated (`grep -n '^Four rules'` none).
- [ ] 1.15 No operator identifiers leak: `git diff eb369dd..HEAD -- docs src | grep '^+' |
  grep -F -f <(ls private_test_data/captures; grep -oE '[A-Za-z0-9_.-]+\.conf'
  openspec/changes/identifier-key-fields/tasks.md)` prints nothing.
- [ ] 1.16 The spec clause matches the five tests' assertions: the clause is the sibling's
  (S1, S2); re-run the challenger's read-only behaviour probes (test-challenge.md,
  Evidence 9) and record them unchanged.
- [ ] 1.17 Sibling delta reconciled: 1.8's diff, plus a delta-log entry naming the shared
  wording and the unapplied sibling text (S3).
- [ ] 1.18 After phase 7: `diff <(sed -n '5,$p' main-spec-edit.md) <(the applied block of
  openspec/specs/conversion/entry-keys/spec.md)` empty; `agent-ready reconcile` exit 0; in a
  throwaway worktree, one misspelled new id makes `reconcile` exit 1 naming it.
- [ ] 1.19 The guide states no contradicting policy: `git diff -U0 eb369dd --
  docs/architecture/developer-guide.md | grep '^+' | grep -nE 'determin|revert|baseline|
  latency|rerun|full check'`; every hit says "same salt" for deterministic, "with the
  mapping" for revert, "measure and explain" for timing, and points at `AGENTS.md`
  Verification rather than restating it.
- [ ] 1.20 The solo-review rule triggers on behaviour-bearing paths, names the corpus, the
  commands and the report's contents, and says "fresh agent" (S7).
- [ ] 1.21 `.openspec.yaml` declares every domain whose paths the deliverables touch.

Baseline probes (phase 4, before any edit, at eb369dd): `mkdocs build --strict` exit 0 in
2,024 ms; `pre-commit run markdownlint` on the seven target files Passed in 529 ms;
`pytest --help` lists the three tier flags; `agent-ready caps` exit 0; `agent-ready
reconcile` exit 0 (vacuous for this change until phase 7, per the challenge); the 24
`main-spec-edit.md` ids collected as 60 nodes in 844 ms; `agent-ready fields` exit 1 on the
sibling change only; `agent-ready lane` refuses to run beside the owner's uncommitted files.
Challenge executed at eb369dd: tier section renders `li=6 ul=1 ol=1`; contract widths
84/83/102/108 with only test-id lines over 84; 0 tokens and 0 headings lost against master.

## 2. Change

- [ ] 2.1 `docs/architecture/developer-guide.md`: extend "When to use each tier" with the
  complete path-to-risk mapping and exact commands; keep every existing bullet and the
  grammar pre-review list; add the workflow-economy rule as a pointer to `AGENTS.md`.
- [ ] 2.2 `docs/how-to/solo-review.md`: the cross-domain independent adversarial corpus
  review rule, triggered by behaviour-bearing paths, naming corpus, commands and report.
- [ ] 2.3 `src/junoscfg/display/CONTRACT.md`, `validate/CONTRACT.md`, `convert/CONTRACT.md`,
  `anonymize/CONTRACT.md`: one invariant each, narrowed to its cited tests (S6), at or
  under 30 lines and 84 columns outside test ids, nothing dropped.
- [ ] 2.4 `docs/how-to/settle-a-schema-question.md`: rule 5, the sanitised device-evidence
  form, carried by `evidence-freeze.md`; opening line updated.
- [ ] 2.5 `main-spec-edit.md`: the sibling delta's wording plus the five ids (S1 to S3);
  applied in phase 7.
- [ ] 2.6 `changelog.d/+agent-guidance-gates-and-contracts.misc.md`: the release note the
  full checkpoint's towncrier gate requires.

## 3. Review and evidence

- [ ] 3.1 Independent Test/Challenge (high floor): phase-4 challenge delivered
  (`test-challenge.md`, seven challenges S1 to S7 in `review.md`); the post-implementation
  half re-executes 1.1 to 1.21 independently and samples claims against sources.
- [ ] 3.2 Complete the risk-required fresh isolated review (`review.md`), correct the
  findings, return them to the same isolated Reviewer.
- [ ] 3.3 Capture `metrics.md` and `metrics.json` for the immutable base and code head, with
  the workflow telemetry.
- [ ] 3.4 Finalizer applies `main-spec-edit.md` to the main spec, runs 1.18, reruns the lane
  gate, ticks metrics; no archive, no merge.
