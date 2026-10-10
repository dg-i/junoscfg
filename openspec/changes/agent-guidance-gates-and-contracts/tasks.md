## 1. Verification

Every check runs against a named commit, in a detached worktree of that commit where the
check reads the tree (`git worktree add --detach <dir> <sha>`), so the owner's uncommitted
files are neither stashed nor read. "Deliverables" means the developer guide, the two
how-to pages, the four contracts, `main-spec-edit.md` and the `changelog.d` fragment.
Checked commit for 1.1 to 1.9: 19d05de. Working-tree checks ran at the same content before
the commit (`qa_tree.py`, gitignored beside the telemetry) and are quoted below.

- [x] 1.1 Links and anchors: `uv run --locked --group docs mkdocs build --strict 2>&1 | tee
  build.log` in the worktree; expect exit 0, no `WARNING` line, and
  `grep -nE 'INFO .*(anchor|not found|unrecognized|absolute)' build.log` naming none of the
  three edited pages. The contracts and `main-spec-edit.md` are not built; 1.6 covers them.
  Evidence (worktree 19d05de): exit 0 in 3,346 ms; 0 `WARNING` lines; no INFO anchor line
  names an edited page; the guide's HTML carries `id="when-to-use-each-tier"`, the anchor
  `solo-review.md` links to.
- [x] 1.2 Commands and examples: every `tests/…py::…` id in the deliverables, extracted
  across wrapped lines with abbreviated `::test_…` forms expanded and file paths separated,
  through `uv run pytest --collect-only -q <ids>`; expect exit 0 and no `not found` line,
  the id list in the evidence. `uv run pytest --help --color=no | grep -oE --
  '--(schema|jvd|regen-schema)\b' | sort -u | wc -l`; expect 3. `--regen-schema` is never
  passed to a dry run (conftest regenerates before collection).
  Evidence: 46 distinct ids (every `tests/…::…` token in the eight deliverables), 154 nodes
  collected, exit 0, no `not found`; 0 abbreviated forms; every bare `test_*.py` name the
  guide lists exists under `tests/`; flag count 3.
- [x] 1.3 Referenced paths: every repository path in the added lines of the deliverables,
  backticked or a link target, path part before `::`, through
  `git ls-files --error-unmatch`; expect every one tracked, a `private_test_data/` path
  allowed only beside the word "gitignored".
  Evidence: 0 untracked paths; both link targets resolve; the three `private_test_data/`
  mentions each sit beside "gitignored".
- [x] 1.4 Terminology: "evidence hierarchy", "kept whole", "UNPLACED", "entry keys", "key
  choice", "nokeyword", "red zone" spelled as in `ARCHITECTURE.md`, `openspec/specs/`, the
  contracts, `docs/how-to/solo-review.md` and `pyproject.toml`; and the deny-list
  `git diff -U0 eb369dd -- <deliverables> | grep '^+' | grep -niE 'kept intact|left
  whole|unplaceable|keyword choice|choice keyword|danger zone|evidence (ranking|order)|source
  of truth'`; expect no hit.
  Evidence: first run hit "key-choice keyword" in the anonymize contract; reworded to "the
  keyword of a key choice" (the specs' term is "key choice"); rerun 0 hits.
- [x] 1.5 Diátaxis placement: `git diff --name-only eb369dd..HEAD` outside the change
  folder lists only the deliverables; `git diff --name-only 01efe85..HEAD -- .agents/` is
  empty; `ARCHITECTURE.md` untouched; `git diff -U0 eb369dd --
  docs/architecture/developer-guide.md | grep '^+' | grep -nE 'outrank|device wins|must
  mean|correctness|evidence hierarchy|fallback|ranks'`: every hit is a pointer to
  `ARCHITECTURE.md`, none a restatement.
  Evidence (19d05de): exactly the eight deliverable paths; `.agents/` diff empty;
  `ARCHITECTURE.md` untouched; two policy hits, both "`ARCHITECTURE.md` … ranks latency
  last" pointers.
- [x] 1.6 Rendered output: `uv run --locked --group dev agent-ready caps` exit 0 with every
  contract at or under 30 lines; ``awk 'length>84 && $0 !~ /`tests\//'`` over the four
  contracts prints nothing; `pre-commit run markdownlint --files <deliverables>` prints
  Passed, not Skipped, for the files the hook covers; `git diff --check eb369dd..HEAD` is
  silent; in the built site the tier section has `li` ≥ 6 plus the new entries and
  `grep -cE '<p>(- |\|)'` is 0 on the three pages.
  Evidence: caps exit 0; contracts 30/26/30/30 lines, 0 lines over 84 bytes outside test-id
  lines; markdownlint Passed on the eight files (629 ms) and again in the commit hook;
  `git diff --check` silent; built pages: guide tables 15 (was 14), solo-review ul 6 (was
  5), settle ul 7 (was 6), broken-list markers 0/0/0; tier section `li=6 ul=1 ol=1`
  unchanged plus one new table of five rows (the new entries are rows, not list items).
- [x] 1.7 Lane: `uv run --locked --group dev agent-ready lane --base master` in the
  worktree; expect exit 0 and `git status --short` in the main checkout unchanged.
  Evidence: exit 1, not because of this change: "documentation-only changes may not alter
  non-documentation files: .agents/skills/agent-ready-garden/SKILL.md,
  …/jobs/5-instructions.md", the owner's commit 01efe85 that sits on this branch; at
  b20ca29 the owner's 306233b adds `mkdocs.yml` to the refusal (challenge re-run). The
  deliverables themselves are all Markdown: at 19d05de with base 01efe85 the gate passes
  (challenge re-run). Owner decision recorded in `checkpoint.md`; the gate reruns once
  both commits leave the branch range. Main checkout untouched.
- [x] 1.8 Spec edit: `diff <(sed -n '5,$p' main-spec-edit.md) <(the sibling delta's
  requirement block)` shows only the five ids appended to the `Tests:` line; the 24 ids
  collect; the clause claims only what the five tests assert (1.16).
  Evidence: at 19d05de the diff had one changed line pair, the `Tests:` line, old an exact
  prefix of new; 24 ids collect as 60 nodes; wording is the sibling's (1.16). After the fix
  pass (S8) the diff is two line pairs: the `Tests:` line and the clause line, which gains
  "A meta attribute on a positional value the reader placed is written back and reports
  nothing." for the fifth id.
- [ ] 1.9 Full checkpoint, once, after the last change task is committed, in the worktree
  of that commit: `uv run --locked --group dev --with griffe --with tach --with towncrier
  --with vulture agent-ready check --set full --base master`; expected result: exit
  non-zero with exactly one failing check, `fields`, naming only `identifier-key-fields`
  (missing `assurance`), every other check passing. Any other failure blocks review.
  Evidence (worktree 19d05de, after `agent-ready skills --regenerate` wrote the gitignored
  mirror a fresh worktree lacks): exit 1 in 7,583 ms, `failing: fields, lane`. `fields`:
  "openspec/changes/identifier-key-fields/.openspec.yaml: assurance is not answered" (the
  expected sibling failure). `lane`: the 01efe85 files above. Every other check passed:
  codemap build, pre-commit, tach, OpenSpec specs, live and archive, interfaces, gates,
  toolbox, specs, reconcile, the four renders, decisions, stage griffe, towncrier and
  vulture, budget, skills, codemap check, retired. The task stays open until the owner
  resolves the two external failures and the check reruns on the resulting head.
- [x] 1.10 Telemetry: base = full SHA of `2a3e025` (master tip and merge base; the range
  holds the owner's garden commit 01efe85, disclosed in `metrics.md`), head = the code
  commit; `uv run --locked --group dev agent-ready metrics
  agent-guidance-gates-and-contracts --base-sha <base> --head-sha <head>
  --workflow-telemetry openspec/changes/agent-guidance-gates-and-contracts/workflow-telemetry.json`;
  expect the import accepted, `grep -ciE 'estimat|approx' workflow-telemetry.json` = 0, every
  command entry carrying an observed duration, every other unavailable row `UNMEASURED`.
  Evidence (Finalizer): base 2a3e025fedb1bb6bce0a87fb8a5ef546b7fa0a87, head
  f31949b9be83597afe1c3450b411db4d41b29056; `workflow-telemetry.json` bound to both, 10
  observed entries plus the finalizer's; `agent-ready metrics` exit 0 wrote `metrics.md`
  and `metrics.json`; `grep -ciE 'estimat|approx'` prints 0; token usage stays null
  (UNMEASURED); the six context-expansion rows survived capture.
- [x] 1.11 Tier bullets survive verbatim: split the old "When to use each tier" section
  (`git show eb369dd:docs/architecture/developer-guide.md`) into its blocks,
  whitespace-normalised; expect each a substring of the new section.
  Evidence: 8 old blocks (bullets, numbered items and paragraphs), 0 missing.
- [x] 1.12 Contracts keep everything: for each contract
  ``comm -23 <(git show eb369dd:$f | grep -oE '`[^`]+`' | sort -u) <(grep -oE '`[^`]+`' $f
  | sort -u)`` empty; every `## ` heading and the `Interface:` line survive; exactly one
  added `- ` bullet under `## Invariants` per contract; `## Precedent` bullet count unchanged.
  Evidence: display lost 0, invariants 2→3, precedent 3→3; validate 0, 2→3, 2→2; convert
  0, 3→4, 3→3; anonymize 0, 3→4, 2→2; every heading and Interface line kept. Recorded
  loss outside the token check (challenge): the convert "Not for" paragraph was reworded
  to fit 84 columns and no longer says "section 1" after `ARCHITECTURE.md`; the pointer
  to the file stays. Re-run after the fix pass: unchanged counts, display still 30 lines.
- [x] 1.13 Each new invariant's cited test asserts it: quote the assertion lines.
  Evidence. display: `assert entry_keys({"L": True, "k": ["list-type", "list-name"]}) ==
  ("list-type", "list-name")`, `assert list(statement_children(keyed)) == ["accept"]`, and
  `test_no_module_keeps_its_own_key` walks every module's syntax tree for a retired key
  spelling with `assert len(files) > 60`. validate: `assert root.children["class"].is_list
  is True` (maxOccurs 16), `["source-port"].is_list is True` (32), `["host-name"].is_list
  is False` (1). convert: `assert any(e.expected == UNPLACED for e in result.errors)` and
  `pytest.raises(FieldValidationError)` on the strict door (set input); `assert messages ==
  [...]` and `pytest.raises(FieldValidationError)` per structured door (JSON, YAML, XML);
  `assert from_[suffix]["@"] == self._ATTRS[command]`, `assert "@" not in from_`, one
  unplaced, round trip (meta on a partial or surplus key). anonymize: `assert
  entry["list-type"] == "as-list-group"` with `sensitive_words=["as-list"]`; `assert
  anonymized["exact"] == [None] and anonymized["accept"] == [None]`, `term["then"]
  ["community"][0]["add"] == [None]`, and no rule saw `exact` or `accept`. The two tests
  enable the rules they need, not all nine, so the contract says "passes the rules
  unchanged" (fix pass; the challenge's all-nine probe held). Validate also cites
  `test_unbounded_is_list`: `assert ifaces.is_list is True` for `maxOccurs="unbounded"`.
- [x] 1.14 Device-evidence form: on the added lines of `settle-a-schema-question.md`, every
  IPv4 address and AS number in the `AGENTS.md` ranges; prompts generic
  (`grep -nE '[A-Za-z0-9_-]+@[A-Za-z0-9_-]+[>#]'` at most `admin@router1`); no pathless
  capture (`grep -nE 'show configuration *(\||$)|show \| compare *($|\|)'` none), the
  preflight step naming a path; set, JSON and XML all required; raw output stays in
  gitignored `private_test_data/` and only the sanitized form enters `evidence-freeze.md`;
  no timing figure (`grep -nE '\b[0-9.]+ ?(ms|s|seconds|minutes)\b'` none); the "Four
  rules" opening line updated (`grep -n '^Four rules'` none).
  Evidence: 0 addresses, 0 prompts, 0 pathless captures, the three views named, the
  gitignored sentence present, 0 timing figures, "Five rules".
- [x] 1.15 No operator identifiers leak: `git diff eb369dd..HEAD -- docs src | grep '^+' |
  grep -F -f <(ls private_test_data/captures; grep -oE '[A-Za-z0-9_.-]+\.conf'
  openspec/changes/identifier-key-fields/tasks.md)` prints nothing.
  Evidence: 8 needles, 0 leaks.
- [x] 1.16 The spec clause matches the five tests' assertions: the clause is the sibling's
  (S1, S2); re-run the challenger's read-only behaviour probes (test-challenge.md,
  Evidence 9) and record them unchanged.
  Evidence (`convert_config_result`, set to set, 19d05de): A `set apply-groups G1` +
  `deactivate apply-groups G1 G2` → 0 unplaced, output `deactivate apply-groups`; B alone →
  same; C after `set apply-groups G1 G2` → 1 unplaced (the set line's); D nokeyword second
  value → 1 unplaced, meta line not reproduced; E `deactivate system ntp` alone → 0
  unplaced, `set system ntp` synthesised; F whole list → reproduced, 0 unplaced; G partial
  key → reproduced, 1 unplaced; H `protect system bogus-thing` → reproduced, 1 unplaced.
  Identical to the challenger's run; A, D and E stay open defects in `review.md`.
- [x] 1.17 Sibling delta reconciled: 1.8's diff, plus a delta-log entry naming the shared
  wording and the unapplied sibling text (S3).
  Evidence: `evidence-freeze.md` Requirements and delta log, `review.md` S3. After the
  fix pass (S8) the diff against the sibling block is the five ids on the `Tests:` line
  plus one sentence for the placed positional value; 1.8's wording updated accordingly.
- [ ] 1.18 After phase 7: `diff <(sed -n '5,$p' main-spec-edit.md) <(the applied block of
  openspec/specs/conversion/entry-keys/spec.md)` empty; `agent-ready reconcile` exit 0; in a
  throwaway worktree, one misspelled new id makes `reconcile` exit 1 naming it.
- [x] 1.19 The guide states no contradicting policy: `git diff -U0 eb369dd --
  docs/architecture/developer-guide.md | grep '^+' | grep -nE 'determin|revert|baseline|
  latency|rerun|full check'`; every hit says "same salt" for deterministic, "with the
  mapping" for revert, "measure and explain" for timing, and points at `AGENTS.md`
  Verification rather than restating it.
  Evidence: 9 hits; "the mapping is stable for the same input and the same salt"; "revert
  with the mapping restores the original"; "Measure and explain … never a gate over
  correctness"; "How many full checkpoints run and where they sit is `AGENTS.md`'s
  Verification rule, not this page's".
- [x] 1.20 The solo-review rule triggers on behaviour-bearing paths, names the corpus, the
  commands and the report's contents, and says "fresh agent" (S7).
  Evidence: the new section opens on "behaviour-bearing paths, code under `src/junoscfg/`
  or the generated data … and never a `CONTRACT.md` or a page under `docs/`", lists the
  JVD, baseline and device-truth commands, the three report items, and closes "a second
  read by a fresh agent, never a second human". This change touches no such path.
- [x] 1.21 `.openspec.yaml` declares every domain whose paths the deliverables touch.
  Evidence: `conversion` (`src/junoscfg/convert/**`) and `anonymization`
  (`src/junoscfg/anonymize/**`); `display/` and `validate/CONTRACT.md` lie under no domain's
  declared paths (`validation` and `schema-pipeline` list single files).

Baseline probes (phase 4, before any edit, at eb369dd): `mkdocs build --strict` exit 0 in
2,024 ms; `pre-commit run markdownlint` on the seven target files Passed in 529 ms;
`pytest --help` lists the three tier flags; `agent-ready caps` exit 0; `agent-ready
reconcile` exit 0 (vacuous for this change until phase 7, per the challenge); the 24
`main-spec-edit.md` ids collected as 60 nodes in 844 ms; `agent-ready fields` exit 1 on the
sibling change only; `agent-ready lane` refuses to run beside the owner's uncommitted files.
Challenge executed at eb369dd: tier section renders `li=6 ul=1 ol=1`; contract widths
84/83/102/108 with only test-id lines over 84; 0 tokens and 0 headings lost against master.

## 2. Change

- [x] 2.1 `docs/architecture/developer-guide.md`: extend "When to use each tier" with the
  complete path-to-risk mapping and exact commands; keep every existing bullet and the
  grammar pre-review list; add the workflow-economy rule as a pointer to `AGENTS.md`.
- [x] 2.2 `docs/how-to/solo-review.md`: the cross-domain independent adversarial corpus
  review rule, triggered by behaviour-bearing paths, naming corpus, commands and report.
- [x] 2.3 `src/junoscfg/display/CONTRACT.md`, `validate/CONTRACT.md`, `convert/CONTRACT.md`,
  `anonymize/CONTRACT.md`: one invariant each, narrowed to its cited tests (S6), at or
  under 30 lines and 84 columns outside test ids, nothing dropped.
- [x] 2.4 `docs/how-to/settle-a-schema-question.md`: rule 5, the sanitized device-evidence
  form, carried by `evidence-freeze.md`; opening line updated.
- [x] 2.5 `main-spec-edit.md`: the sibling delta's wording plus the five ids (S1 to S3);
  applied in phase 7.
- [x] 2.6 `changelog.d/+agent-guidance-gates-and-contracts.misc.md`: the release note the
  full checkpoint's towncrier gate requires.

Change commit: 19d05de. Nothing else outside the change folder is touched.

## 3. Review and evidence

- [x] 3.1 Independent Test/Challenge (high floor): phase-4 challenge delivered
  (`test-challenge.md`, seven challenges S1 to S7 in `review.md`); the post-implementation
  half re-executed 1.1 to 1.21 independently (0 mismatches against the recorded evidence;
  four checks shown to fail on broken input) and sampled 20 claims (14 hold, 4 partly, 2
  failed; every failure and partial corrected in the fix pass).
- [x] 3.2 Complete the risk-required fresh isolated review (`review.md`), correct the
  findings, return them to the same isolated Reviewer.
- [x] 3.3 Capture `metrics.md` and `metrics.json` for the immutable base and code head, with
  the workflow telemetry.
- [x] 3.4 Finalizer applies `main-spec-edit.md` to the main spec, runs 1.18, reruns the lane
  gate, ticks metrics; no archive, no merge.
  Evidence (Finalizer): main spec applied at a3dc03d; 1.18 done; metrics ticked (3.3,
  1.10). `uv run --locked --group dev agent-ready lane --base master` in a detached
  worktree of a3dc03d, exit 1, output verbatim (the known external refusal, the owner's
  commits 01efe85 and 306233b, not this change's to fix; 1.9 stays open):

  ```text
  agent-guidance-gates-and-contracts: documentation-only changes may not alter non-documentation files: .agents/skills/agent-ready-garden/SKILL.md, .agents/skills/agent-ready-garden/jobs/5-instructions.md, mkdocs.yml; retype the change for code or executable configuration
  ```
