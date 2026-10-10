# Test/Challenge report

## Phase-4 challenge (before implementation)

Challenger: fresh, context-isolated agent; read the committed artefacts at `eb369dd`
plus the untracked `tasks.md`, and the sources they cite. No file other than this
report was created or changed. The commands I ran are listed under "Evidence executed".

### Verdict on the QA tasks

- **1.1 tighten.** MkDocs 1.6.1 with no `validation:` block in `mkdocs.yml` logs a broken
  anchor at INFO level, so `--strict` never fails on one. "anchors" cannot fail as written.
  Five of the seven deliverables are never built: the four contracts and `main-spec-edit.md`.
  Add: `grep -nE 'INFO .*(anchor|not found|unrecognized|absolute)' <build log>`, expect no
  line naming one of the three edited pages. Run the build on a clean checkout of the
  checked SHA (`git worktree add <tmp> <sha>`), or record the stash state, because the
  owner's dirty `mkdocs.yml` changes `not_in_nav`.
- **1.2 tighten.** Executed: the plan's own ids do **not** all collect.
  `tests/test_anonymize/test_integration.py::TestPipelineIntegration::test_revert_map_restores_originals`
  gives `ERROR: not found` and exit 4. The test lives in `TestPipelineDumpMapIntegration`
  (line 199). The "60" baseline counts only the 24 `main-spec-edit.md` ids; I reproduced
  60 nodes for exactly those. A count is the wrong expected result. Expect exit 0 and no
  `not found` line. A misquoted argument list prints `no tests collected` (exit 4/5),
  which a count-reader can mistake for success. Extraction must:
  (a) cover all seven deliverables plus `main-spec-edit.md`;
  (b) be multi-line, because inline code can wrap;
  (c) expand abbreviated `::test_…` forms (the docs plan already uses one, row 25);
  (d) separate file paths (`tests/conftest.py`) from node ids.
  For the flags, use
  `uv run pytest --help --color=no | grep -oE -- '--(schema|jvd|regen-schema)\b' | sort -u | wc -l`
  and expect 3. Never dry-run `--regen-schema` with `--collect-only`:
  `pytest_sessionstart` (conftest.py:135–152) regenerates the artifacts before collection.
- **1.3 tighten.** `grep -o` of backticked paths misses Markdown link targets and keeps the
  `::` suffixes. `test -f` passes for gitignored local files (`private_test_data/…`, which
  the guide already names). Use `git ls-files --error-unmatch <path>` on the path part
  before `::`. A `private_test_data/` path is allowed only where the sentence says it is
  gitignored. `agent-ready reconcile` is **vacuous** here: `reconcile.py` reads main specs
  and a live change's `specs/` deltas only, and this change has no `specs/` (skip_specs).
  It does not read docs, contracts or `main-spec-edit.md`. Move it to after phase 7 (see
  missing check 8).
- **1.4 tighten.** The expected result can only fail by chance. "red zone" occurs 0 times
  in `ARCHITECTURE.md`, 0 in `openspec/specs/`, 0 in the contracts (executed). Its homes
  are `pyproject.toml` `tier = "red"` and `docs/how-to/solo-review.md`. Grepping canonical
  terms never finds a synonym. Add a deny-list over the added lines,
  `git diff -U0 <base> -- <deliverables> | grep '^+' | grep -niE 'kept intact|left whole|unplaceable|keyword choice|choice keyword|danger zone|evidence (ranking|order)|source of truth'`,
  and expect no hit. Add `solo-review.md` and `pyproject.toml` to the reference set.
- **1.5 tighten.** Executed: as written it **fails today**.
  `git diff --name-only master...HEAD` already lists
  `.agents/skills/agent-ready-garden/SKILL.md` and `…/jobs/5-instructions.md` (commit
  `01efe85`, on this branch, template-managed). Use base `eb369dd` for the deliverable
  whitelist, and check `git diff --name-only 01efe85..HEAD -- .agents/` (expect empty).
  The "policy sentence" inspection needs a probe: grep the added guide lines for
  `outrank|device wins|must mean|correctness|evidence hierarchy|fallback|ranks`. Each hit
  must be a pointer to `ARCHITECTURE.md`, not a restatement.
- **1.6 tighten.** `agent-ready caps` counts lines and markdownlint runs with `MD013`
  disabled (`.pre-commit-config.yaml:48`), so the 30-line cap can be met by unwrapping. Add
  ``awk 'length>84 && $0 !~ /`tests\//' src/junoscfg/{display,validate,convert,anonymize}/CONTRACT.md``
  and expect no output. Today the only lines over 84 characters are test-id lines (102 and
  108). The markdownlint hook excludes `openspec/(schemas|changes|specs)/`: expect `Passed`
  per file, and treat `Skipped` as not checked. `git diff --check` with no range only
  compares the working tree with the index, so it is silent after commit. Use
  `git diff --check eb369dd..HEAD`. For the HTML, the baseline tier section renders
  `li=6 ul=1 ol=1` (executed). Expect `li ≥ 6 +` the number of new mapping entries, and
  `grep -cE '<p>(- |\|)'` = 0 in the three pages (that pattern means a broken list or table).
- **1.7 tighten.** "the owner's two uncommitted files" is already stale: `git status` now
  shows three owner files, including a new untracked
  `docs/reviews/2026-10-10-instruction-audit.md`, plus this change's untracked `tasks.md`.
  `git stash -u` would also hide the change's own uncommitted deliverables. Stash only
  named paths:
  `git stash push --include-untracked -- mkdocs.yml docs/reviews/<each file>`.
  Afterwards expect `git stash list` empty and `git status --short` identical to before.
- **1.8 keep, then add.** Executed: the retained text is verbatim. The heading, body and
  first scenario are unchanged. The old `Tests:` line is an exact prefix of the new one.
  The diff adds only the clause, two scenarios and five ids. The 24 ids give 60 nodes,
  exit 0. The check misses that the new clause claims more than the five tests assert
  (Specification challenges S1, S2), and it misses the sibling delta collision (S3).
  Add missing checks 6 to 8.
- **1.9 tighten.** The expected result ("every check passed") cannot happen, and the escape
  clause lets any failure be "recorded". The acceptance criterion only says to run the
  check once. State the result exactly: exit non-zero with exactly one failing check,
  `fields`, whose message names only `identifier-key-fields` (missing `assurance`); every
  other check passes. Any other failure blocks review. Commit the deliverables, including
  the `changelog.d` fragment, before running it.
- **1.10 tighten.** `<base>` is unnamed. The master tip and merge-base is `2a3e025…`, so
  the range includes the garden commit `01efe85`. Name the full SHA and disclose `01efe85`
  in `metrics.md`. "no estimated value" needs a test:
  `grep -ciE 'estimat|approx' workflow-telemetry.json` = 0, and every entry carries an
  observed duration or is absent (C9 commands stay untimed, not invented).
- **add.** 1.11 to 1.21: missing checks 1 to 11 below.

### Verdict on the acceptance criteria

- **AC1** ("every QA check has a passing task … against the checked HEAD"): tighten.
  `tasks.md` is untracked. "checked HEAD" is not a SHA. A HEAD check on a dirty tree is not
  a HEAD check. Commit `tasks.md`, name the SHA, and run on a clean worktree.
- **AC2** (`reconcile` "with the delta live"): vacuous. No `specs/` delta exists. Replace
  it with missing check 8.
- **AC2** (`caps`): can be gamed by unwrapping. Add the width check from 1.6.
- **AC2** (strict MkDocs): misses anchors and the unbuilt files (1.1).
- **AC2** (markdownlint): openspec files are excluded (1.6).
- **AC2** (`git diff --check`): range missing (1.6).
- **AC2** (full checkpoint): no pass criterion (1.9).
- **AC3** (Test/Challenge): this report is the pre-implementation half. The post half must
  re-run 1.1 to 1.21 independently.
- **AC4** (fresh Reviewer): keep. Give the Reviewer this report's S1 to S3.
- **AC5** (telemetry with no estimated value): tighten as in 1.10.
- **Evidence freeze, Evidence line 1** ("Every test id the documents will cite collects:
  60 nodes"): false (S4).

### Missing checks

1. **Tier bullets survive verbatim** (diff-based, tolerates reflow). Extract
   `### When to use each tier` up to `---` from `git show master:docs/architecture/developer-guide.md`
   and from the edited file. Split the old text on `\n(?=- |\d+\. )`, normalise whitespace,
   and assert each old block is a substring of the normalised new section. Expect
   `6 old blocks; 0 missing`. I ran this against the unedited tree: 6 and 0, which is
   trivially true before the edit and must be re-run after it.
2. **Contracts keep everything.** For each of the four contracts, every backticked token
   in the `master` version also appears in the new one:
   ``comm -23 <(git show master:$f | grep -oE '`[^`]+`' | sort -u) <(grep -oE '`[^`]+`' $f | sort -u)``,
   expect empty. Every `## ` heading and the `Interface:` line also survive. Baseline
   executed: 0 lost in all four. Expect exactly one added `- ` bullet under
   `## Invariants` per contract (four bullets in total), `## Precedent` bullet count
   unchanged, and `wc -l` ≤ 30.
3. **Each new invariant's cited test asserts it** (read the bodies; quoted below). Expect
   every claim backed, or narrowed to what is backed.
   - display, "one kernel answer owns entry keys, statement children and key form":
     `test_statement_children_drop_the_key_fields` asserts only `statement_children`'s
     output and `"statement_children" in display.__all__`.
     `test_reader_and_writer_share_the_grammar_rule` asserts reader and writer agree on a
     monkeypatched tree
     (`assert set_to_dict(line) == {"sample": [{"vlan-id": "100"}]}`). Neither pins
     single ownership, and `key_is_positional` is named by no test (`grep -rn key_is_positional tests/`
     is empty). The ownership guard is
     `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`.
     **Partial.**
   - validate, "any `maxOccurs` other than 1 is a list":
     `assert root.children["class"].is_list is True` (16),
     `["source-port"].is_list is True` (32), `["host-name"].is_list is False` (1).
     **Backed.**
   - validate, "declared keys drive the generated artifacts":
     `test_entry_properties_are_the_key_fields` expects route-filter properties
     `{"address", "exact", "orlonger", "accept", "reject"}`, which includes non-key
     children. `test_bundled_grammar_matches_its_structure_tree` asserts reproducibility
     (`rebuilt.strip() == shipped.strip()`), not key-driven generation. **Partial.**
   - convert, "stays whole and loud through every door": `test_each_door_reports_it`
     feeds set input only. It asserts `any(e.expected == UNPLACED …)` via `validate_ir`
     and `pytest.raises(FieldValidationError)` via strict `convert_config`. That is two
     validation doors and one reader. JSON, YAML and XML are pinned by
     `tests/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_each_structured_door_reports_it`.
     Structured (curly) is pinned by none; my probe shows it does report (1 unplaced).
     For meta commands, see S1. **Partial.**
   - anonymize, "an enum value or key-choice keyword passes unchanged":
     `test_an_enum_key_passes_unchanged` (`sensitive_words=["as-list"]`,
     `assert entry["list-type"] == "as-list-group"`) and
     `test_a_key_choice_keyword_passes_unchanged`
     (`anonymized["exact"] == [None] and anonymized["accept"] == [None]`,
     `term["then"]["community"][0]["add"] == [None]`) back it, with all rules on.
     `test_a_value_from_its_leafs_enum_passes_every_rule` turns on one rule only
     (`AnonymizeConfig(sensitive_words=[word], salt="keyed")`), so "every rule" is its
     name, not its assertion. **Backed** by the walker pair.
   - All ten contract-candidate ids are default-tier: 34 nodes with and without
     `-m "not schema and not jvd"` (executed).
4. **Device-evidence form (rule 5) privacy and consistency.** On the added lines of
   `settle-a-schema-question.md`:
   - (a) Every IPv4 address is in RFC 5737, RFC 1918 or the `AGENTS.md` table ranges, and
     every AS number is in 64496–64511 (`grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}'`, then
     inspect).
   - (b) Prompts are generic only: `grep -nE '[A-Za-z0-9_-]+@[A-Za-z0-9_-]+[>#]'`, expect
     at most `admin@router1`.
   - (c) No pathless capture: `grep -nE 'show configuration *(\||$)|show \| compare *($|\|)'`,
     expect none. This includes the "clean preflight" step, which must name the path too
     (rule 2).
   - (d) `set`, `JSON` and `XML` are all required (rule 1).
   - (e) Raw output stays in gitignored `private_test_data/`, and only the sanitised form
     enters the committed `evidence-freeze.md` (`grep -n private_test_data`, ≥ 1).
   - (f) No timing figure: `grep -nE '\b[0-9.]+ ?(ms|s|seconds|minutes)\b'`, expect none
     (owner limit).
   - (g) Line 3 "Four rules" is updated: `grep -n '^Four rules' …`, expect none.
     `AGENTS.md` is at its 100-line cap, so the how-to is the only home; state that.
5. **No operator identifiers leak.** The large-case baseline in
   `openspec/changes/identifier-key-fields/tasks.md` item 4.4 is measured on a private
   configuration whose file name identifies a device. Run
   `git diff eb369dd..HEAD -- docs src | grep '^+' | grep -F -f <(ls private_test_data/captures; grep -oE '[A-Za-z0-9_.-]+\.conf' openspec/changes/identifier-key-fields/tasks.md)`
   and expect no output. Cite "the recorded baseline in identifier-key-fields 4.4/5.6",
   never the file.
6. **The new clause matches the tests' assertions.** Quoted, `test_a_partial_or_surplus_key_is_kept_whole`:
   `assert "@" not in from_`, `assert "@" not in from_["as-path-neighbors"][0]`,
   `assert from_[suffix]["@"] == self._ATTRS[command]`,
   `assert len(_unplaced(...)) == 1`, `assert meta_line in dict_to_set(ir).splitlines()`.
   - `…unknown_path…`: `assert "@" not in ir["system"]`,
     `ir["system"]["bogus-thing"] == {"@": {"inactive": True}}`, one unplaced, exact round
     trip.
   - `…reuses_its_unplaced_report`: `ir["system"]["@bogus-thing"] == {"inactive": True}`,
     one unplaced, exact round trip.
   - `…positional_value_is_kept_whole`:
     `ir["protocols"]["isis"]["enable-disable"] == "SAMPLE-UNKNOWN"`,
     `_unplaced(...) == []`, exact round trip.
   - `…whole_list_is_written`: only `set_line in …` and `meta_line in …`.
   - These back: partial key, surplus token, unmodelled path, shared report, placed
     positional value, and a whole list written back. They do not back "such a path" in
     general, "a path the configuration does not hold", or "a whole list … reports
     nothing".
   - Expected: the clause is narrowed (S1, S2), or each extra claim gets a cited test.
   - Probe to re-run after any wording change: the `convert_config_result` snippets in
     Evidence item 9.
7. **Sibling delta reconciled.**
   `diff` the requirement block of `openspec/changes/identifier-key-fields/specs/conversion/entry-keys/spec.md`
   (lines 73–92) against `main-spec-edit.md`. Expect one agreed wording, or a delta-log
   entry naming which change owns the clause and what the other drops (S3).
8. **Post-phase-7 application is verbatim and reconcile is not vacuous.**
   - (a) `diff <(sed -n '5,$p' main-spec-edit.md) <(awk '/^### Requirement: A statement the reader cannot complete is kept whole/{f=1} f&&/^### Requirement:/&&!/kept whole/{f=0} f' openspec/specs/conversion/entry-keys/spec.md)`,
     expect empty.
   - (b) `agent-ready reconcile` exit 0.
   - (c) Negative probe in a throwaway worktree: misspell one of the five new ids, run
     `reconcile`, expect exit 1 naming that id. This proves the gate reads the edited
     requirement.
9. **The guide states no policy that contradicts `ARCHITECTURE.md` or the anonymize
   contract.**
   - (a) A timing bound for entry lookup must be "measure and explain against the
     baseline". It must not be a gate that can override a correctness fix: §1 ranks
     latency last (`4. **Latency** — last`).
   - (b) `deterministic` must be qualified by "same salt". `anonymize/CONTRACT.md` says
     "not idempotent: `anonymize()` writes a generated salt back".
   - (c) `revert…` must be qualified by "with the mapping" (contract: "Not reversible
     without the mapping").
   - (d) The workflow-economy rule points at `AGENTS.md` `## Verification` instead of
     restating it ("no second testing policy").
   - Run `git diff -U0 eb369dd -- docs/architecture/developer-guide.md | grep '^+' | grep -nE 'determin|revert|baseline|latency|rerun|full check'`
     and inspect each hit against those sentences.
10. **The solo-review rule applies to this change itself.** This change edits contracts
    under `validate`, `convert` and `anonymize`, which is three of the rule's six areas.
    Expect the rule to define its trigger by behaviour-bearing paths (S7), or this change
    to carry the corpus review it prescribes. Also expect the rule to name the corpus and
    the command, and the report's required contents (task 2.2). It must say "fresh agent"
    and never imply a second human: the file states "a second read, not a second human,
    and it never claims otherwise".
11. **Change metadata matches the edited paths.** `.openspec.yaml` declares
    `domains: [conversion]`, but the deliverables edit `src/junoscfg/anonymize/CONTRACT.md`,
    which is under `[tool.template.domains.anonymization]` `paths`. Expect `anonymization`
    to be declared, or the omission justified. `agent-ready fields` only checks that the
    keys exist (`required.py:343`), so it cannot catch this.

### Evidence executed

1. `diff` of the main-spec requirement block against `main-spec-edit.md` (from line 5):
   - `10c10,18`: the old `Tests:` line is an exact prefix of the new one (shell `[[ "$new" == "$old"* ]]` true).
   - `19a28,45`: the two new scenarios.
   - No other hunk.
   - 24 ids, no duplicate.
2. `uv run pytest --collect-only -q $(cat <docs-plan + spec-edit node ids>)`:
   `ERROR: not found: …test_integration.py::TestPipelineIntegration::test_revert_map_restores_originals`,
   then `71 tests collected`, exit 4. Without that id: `98 tests collected`, exit 0. The
   real class is `TestPipelineDumpMapIntegration` (1 test collected).
3. The 24 `main-spec-edit.md` ids: `60 tests collected`, exit 0.
   `TestAMetaCommandIsNeverPartiallyApplied`: 19 nodes.
4. `uv run pytest --help | grep -E -- '--(schema|jvd|regen-schema)'`: three lines (ANSI
   colour in the output), exit 0.
5. `uv run --locked --group docs mkdocs build --strict`: exit 0, 0 `WARNING` lines, INFO
   lists `how-to/hosting.md` not in nav. mkdocs 1.6.1, no `validation:` block. The working
   tree includes the owner's dirty `mkdocs.yml` (`+  /reviews/*.md`).
6. `agent-ready caps`: exit 0. `agent-ready reconcile`: exit 0. Read `reconcile.py`: it
   reads main specs plus `live_change/specs` only. `git diff --check`: exit 0, silent.
7. Contract baselines: lines 27/24/30/28. Max widths 84/83/102/108; the only lines over 84
   are test ids. The survival check against `master` loses 0 tokens and 0 headings.
8. Built-page counts: developer-guide `tables=14 ul=21 ol=9`; solo-review `0/5/2`;
   settle `1/6/1`. Tier section `li=6 ul=1 ol=1 table=0`.
9. Read-only behaviour probes (`convert_config_result(..., Format.SET → Format.SET)`; no
   file written):
   - `set apply-groups G1` + `deactivate apply-groups G1 G2` → output
     `deactivate apply-groups`, 0 unplaced.
   - `deactivate apply-groups G1 G2` alone → output `deactivate apply-groups`, IR
     `{"@apply-groups": {"inactive": true}}`, 0 unplaced.
   - `set apply-groups G1 G2` + same → output `set apply-groups G1 G2` /
     `deactivate apply-groups`, 1 unplaced (the set line's).
   - `set access securid-server SAMPLE-SERVER configuration-file sample-1` +
     `deactivate access securid-server SAMPLE-SERVER-2` → output
     `deactivate access securid-server SAMPLE-SERVER SAMPLE-SERVER-2`, 1 unplaced.
   - `deactivate system ntp` alone → output `set system ntp` / `deactivate system ntp`,
     0 unplaced.
   - `set system login user admin uid 2000` + `deactivate system login user` → reproduced,
     0 unplaced.
   - partial key `deactivate … as-path-neighbors as-list` → reproduced, 1 unplaced.
   - `protect system bogus-thing` → reproduced, 1 unplaced.
   - Structured `as-path-neighbors as-list;` → 1 unplaced.
10. Collection with `-m "not schema and not jvd"` over the ten contract-candidate ids:
    34 = 34 (all default-tier).
11. Repository state:
    - `git log master..HEAD`: `eb369dd f3bd902 01efe85 384acc3`.
    - `git diff --name-only master...HEAD` outside the change folder: the two
      `.agents/skills/agent-ready-garden/` files.
    - `git status --short`: `M mkdocs.yml`, three untracked (two owner reviews and
      `tasks.md`).
    - Sibling delta commit `211a165` is not an ancestor of the main-spec application
      `a920fab`.
12. Terminology counts in the reference sources (ARCH / specs files / contracts):
    - "evidence hierarchy": 1 / 0 / 0
    - "kept whole": 0 / 1 / 0
    - "UNPLACED": 0 / 2 / 0
    - "key choice": 0 / 5 / 0
    - "nokeyword": 0 / 2 / 0
    - "red zone": 0 / 0 / 0

### Could not check

- All post-edit checks. The deliverables do not exist yet; missing checks 1 to 11 are
  defined against them.
- `agent-ready lane` and `check --set full`. `lane` refuses on the dirty tree, and
  stashing would modify the working tree, which my role forbids.
- `pre-commit run markdownlint`: not on my allowed list. The Builder's baseline says Passed.
- `--schema`, `--jvd`, `--regen-schema`: forbidden. The jvd budget test only collects
  (1 node, `-m jvd`).
- Device behaviour of `deactivate apply-groups G1 G2` and of the nokeyword case. This
  needs a device artefact (`AGENTS.md`), named path only.
- Whether `openspec archive` of the sibling's `ADDED` requirement over an existing one
  fails or overwrites. Running it would mutate the repository.
- `agent-ready metrics`: there is no telemetry file yet.

## Specification challenges

**S1.**
- Artifact: `main-spec-edit.md`, the new clause, "WHEN a `deactivate`, `activate`,
  `protect` or `delete` line names such a path, or a path the configuration does not
  hold, THEN … SHALL attach the attribute to no shorter valid path … set output SHALL
  reproduce the line, and field validation SHALL report it `UNPLACED` once". The same
  overclaim sits in docs-plan row 24 ("metadata command stays whole and loud through
  every door").
- Counterexample (executed, Evidence 9):
  - "such a path" includes "`apply-groups` … with two names".
    `deactivate apply-groups G1 G2` gives IR `{"@apply-groups": {"inactive": true}}`,
    output `deactivate apply-groups`, 0 unplaced. The attribute lands on the shorter path
    and the names are dropped silently.
  - "such a path" includes the nokeyword second value. The meta line is not reproduced
    (`… SAMPLE-SERVER SAMPLE-SERVER-2`).
  - For "a path the configuration does not hold", `deactivate system ntp` is placed (with
    a `set system ntp` line added) and 0 unplaced.
  - The five tests cover only partial key, surplus token and an unmodelled path.
- User impact: the main spec would assert behaviour the product lacks. A reader trusting
  it would expect `deactivate apply-groups G1 G2` to be kept and reported. Instead, every
  apply-group is deactivated without a diagnostic, so the meaning changes. The change's
  claim "traceability only, behaviour unchanged" would be false.
- Proposed correction: narrow the clause to what the tests pin. For example: "a line that
  names an entry whose key values run out, a token after its complete key, or a path the
  schema does not model". (This is the sibling's own scope: "a partial or surplus
  keyed-list key and an unknown path".) Record the apply-groups and nokeyword meta cases
  as an open defect for a separate change, with a device artefact first.
- Decision: Pending owner decision.

**S2.**
- Artifact: `main-spec-edit.md`, "an attribute on a whole list, or on a positional value
  the reader placed, is written back and reports nothing".
- Counterexample (proposed probe; behaviour today executed):
  `test_a_meta_attribute_on_a_whole_list_is_written` asserts only
  `set_line in dict_to_set(ir).splitlines()` and `meta_line in …`. It has no `_unplaced`
  assertion, so "reports nothing" for a list is unpinned. Today it holds (0 unplaced for
  `system login user`), but a regression that reported a whole list would pass the cited
  tests. Scenario 3's THEN already limits "reports nothing" to "the placed value". Also,
  the test cited for the placed value is named `…_is_kept_whole`, while the clause calls
  the value "placed". The assertions agree with the clause, not with the name.
- User impact: an untested promise in a SHALL-adjacent sentence.
- Proposed correction: "an attribute on a whole list is written back; one on a positional
  value the reader placed is written back and reports nothing". Adding the assertion is a
  test change and is out of this lane.
- Decision: Pending owner decision.

**S3.**
- Artifact: `main-spec-edit.md` and `evidence-freeze.md` ("No other requirement changes").
  Neither names the sibling live delta.
- Counterexample (executed): `openspec/changes/identifier-key-fields/specs/conversion/entry-keys/spec.md`
  (commit `211a165`, after the main-spec application `a920fab`) carries "A statement the
  reader cannot complete is kept whole" under `## ADDED Requirements`. It has a different
  meta clause ("The same applies to `deactivate`, `activate`, `protect` and `delete`: a
  partial or surplus keyed-list key and an unknown path SHALL apply no attribute to the
  nearest valid parent or entry …") and two differently-titled scenarios.
- User impact: two live texts for one requirement. Whichever change is finalised second
  either fails to archive or overwrites the other's wording, so traceability is lost again.
- Proposed correction: adopt one wording (the sibling's is narrower and matches the tests).
  Log the overlap in both delta logs. Add missing check 7 to the finalizer's phase-7 list.
- Decision: Pending owner decision.

**S4.**
- Artifact: `evidence-freeze.md` Evidence ("Every test id the documents will cite
  collects: 60 nodes"), `tasks.md` baseline ("60 cited ids collected"), and `docs-plan.md`
  row 18.
- Counterexample (executed):
  `tests/test_anonymize/test_integration.py::TestPipelineIntegration::test_revert_map_restores_originals`
  gives `ERROR: not found`, exit 4. 60 is the node count of the 24 `main-spec-edit.md` ids
  only.
- User impact: a frozen claim is false. A deliverable copying row 18 would cite a dead id.
- Proposed correction: `…::TestPipelineDumpMapIntegration::test_revert_map_restores_originals`.
  Re-baseline as "all ids collect, exit 0", listing the ids.
- Decision: Pending owner decision.

**S5.**
- Artifact: `docs-plan.md` row 19 and proposal measure (1) ("entry lookup or a schema-wide
  walk: bounded timing against a frozen baseline").
- Counterexample (executed read): the cited guard
  `test_compact_siblings_keep_practical_parse_time` times
  `bundled_set_validator.validate(source)` (Lark grammar,
  `assert elapsed < 5.0, f"100 compact sibling commands took {elapsed:.2f}s"`). It never
  touches entry-key lookup or the reader's schema walk. The "frozen baseline" is a private
  file's timing in a live change folder, which moves on archive.
- User impact: a slow entry-lookup change passes the named guard. The guide would also
  point at a path that rots.
- Proposed correction: say there is no committed timing guard for entry lookup, and
  describe the baseline procedure without naming the private file. Phrase it as
  measure-and-explain, never as a gate over correctness (§1).
- Decision: Pending owner decision.

**S6.**
- Artifact: `docs-plan.md` rows 22 and 23 (display and validate invariants).
- Counterexample (executed read; see missing check 3): the display tests do not pin single
  ownership, and `key_is_positional` is named by no test. The validate pair pins grammar
  reproducibility and a property set that includes non-key children (`accept`, `reject`).
- User impact: contracts would say "enforced by" for a guarantee the test does not
  enforce.
- Proposed correction: display cites
  `TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`. Validate narrows to
  "any `maxOccurs` other than 1 is a list", citing `TestCardinality::test_a_numeric_max_occurs_is_list`
  alone, or names a test that asserts key-driven generation.
- Decision: Pending owner decision.

**S7.**
- Artifact: proposal measure (2) and task 2.2, the solo-review rule "a change crossing
  more than one of schema parser, artifacts, conversion, grammar, validation or
  anonymization always gets an independent adversarial corpus review, green gates
  notwithstanding".
- Counterexample (proposed probe): this docs-only change edits contracts under
  `validate/`, `convert/` and `anonymize/`, so it crosses three areas. It plans
  Test/Challenge and a fresh review but no corpus review, so it would violate the rule it
  adds. The rule also names no corpus and no command.
- User impact: a rule its own change cannot satisfy is read as optional.
- Proposed correction: trigger on behaviour-bearing paths (`src/**` code and generated
  data, not `CONTRACT.md` or docs). Name the corpus and the command (e.g. `--jvd` and the
  frozen-baseline comparison already in the guide). Define the report's contents.
- Decision: Pending owner decision.
