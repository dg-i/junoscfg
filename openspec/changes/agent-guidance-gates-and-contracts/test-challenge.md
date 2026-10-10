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

## Post-implementation challenge (after 19d05de)

Challenger: the same context-isolated role. I read the committed artefacts at `b20ca29`
(deliverables at `19d05de`) and the sources they cite. I did not read the Builder's
`qa_tree.py` or telemetry, and wrote my own extraction scripts under `/tmp`.

- Every check that reads the tree ran in my own detached worktree
  (`junoscfg-wt-challenge`, at `19d05de`, after `agent-ready skills --regenerate`). I
  moved it to `b20ca29` for one lane run, then removed it.
- Negative probes that need an edited file ran in throwaway copies under `/tmp`, removed
  afterwards.
- The main checkout's `git status` was identical before and after. No file other than
  this report was changed. No `--schema`, `--jvd` or `--regen-schema` run.

### Re-execution of tasks 1.1 to 1.21

1.10 and 1.18 are phase 7 and were not run. Results: 19 re-executed, 19 match the
recorded evidence, 0 mismatches. Three recorded notes are incomplete; see 1.7, 1.12 and
1.13.

- **1.1**
  - Command: `mkdocs build --strict -d /tmp/chal_site` (mkdocs 1.6.1, no `validation:`
    block), then `grep -nE 'INFO .*(anchor|not found|unrecognized|absolute)'`.
  - Result: exit 0; 0 `WARNING`; 0 INFO anchor lines; the only INFO note is the
    not-in-nav list. The built guide carries `id="when-to-use-each-tier"` once. The
    solo-review link resolves to `../../architecture/developer-guide/#when-to-use-each-tier`.
  - Negative probe: in a `/tmp` copy, `#when-to-use-each-tierX` still exits 0, but the
    INFO grep catches it ("does not contain an anchor").
  - Matches: yes. Precise: yes, because of the INFO grep; exit 0 alone would not fail.
- **1.2**
  - Command: my own extraction over the eight files plus `main-spec-edit.md`. It unwraps
    lines, rejoins `::` breaks, scans for abbreviated forms, and separates bare paths.
    Then `pytest --collect-only -q <ids>`, and
    `pytest --help --color=no | grep -oE -- '--(schema|jvd|regen-schema)\b' | sort -u | wc -l`.
  - Result: 46 distinct ids, 154 nodes, exit 0, 0 `not found`. Added lines only: 17 ids,
    93 nodes. 0 abbreviated forms. All 8 bare `test_*.py` names exist. Flags: 3.
  - Negative probe: one id with a trailing `X` gives exit 4 and `ERROR: not found`.
  - Matches: yes. Precise: yes.
- **1.3**
  - Command: every backticked token or link target in the added lines with a `/` or a
    file extension. I took the part before `::` or `#`, resolved short forms against
    the root, `src/junoscfg/`, `src/junoscfg/validate/`, `tests/` and the page's own
    directory, and matched globs against `git ls-files`.
  - Result: every path resolves to tracked files, `validate/xsd_*.py` to 3 and
    `validate/*_validator.py` to 4. Unresolved: `private_test_data/schemas/`, which is
    gitignored, and the generic `evidence-freeze.md`. All three `private_test_data/`
    mentions sit beside "gitignored".
  - Matches: yes.
  - Precise: yes for full paths. The task does not say how the short relative names in
    the guide's table are resolved (`xsd_fixes.py`, `audit/walker.py`). I resolved them
    all.
- **1.4**
  - Command: the deny-list over the added lines of the nine files, plus counts of the
    seven canonical terms in the added lines and in the reference set (main specs via
    `find`).
  - Result: deny-list 0 hits; every canonical term is spelt as in the sources.
    - At 3c97a30, "key-choice keyword" would have hit; it is gone.
    - Outside the fixed list, the new solo-review section says "every metadata verb
      (`deactivate`, …)". The sibling requirement and `tests/test_set_input.py` say "meta
      command(s)", and so does the convert contract. "metadata verb" occurs nowhere else
      in the repository.
  - Matches: yes. Precise: yes for its list; a fixed list cannot catch a new synonym.
- **1.5**
  - Command: `git diff --name-only eb369dd 19d05de` outside the folder;
    `git diff --name-only 01efe85 19d05de -- .agents/`; `ARCHITECTURE.md` and
    `AGENTS.md` diff; the policy probe on the guide and, wider, on `docs/how-to` and
    `src`.
  - Result: exactly the eight deliverable paths; `.agents/` empty; `ARCHITECTURE.md`
    and `AGENTS.md` untouched; 2 policy hits (both "`ARCHITECTURE.md` … ranks latency
    last"), 0 in the how-tos and contracts.
  - Matches: yes. Precise: yes for paths. The policy probe is a word list (see claim 5).
- **1.6**
  - Commands and results:
    - `agent-ready caps`: exit 0. Contracts 30/26/30/30.
    - Width `awk` (as in the task): no output. Lines carrying test ids have prose parts
      of 14–77 characters.
    - Per-file `pre-commit run markdownlint`: Passed on the eight files the hook covers.
      `main-spec-edit.md` is Skipped (excluded `openspec/changes/`).
    - `git diff --check eb369dd 19d05de`: silent, exit 0.
    - Built HTML, whole page: guide tables 15, solo-review ul 6, settle ul 7; broken
      `<p>- ` or `<p>|` markers 0/0/0. Tier section: `li=6 ul=1 ol=1`, plus one table
      of 5 rows × 4 cells.
  - Negative probe: a 31-line display contract in a `/tmp` clone makes `caps` exit 1
    ("31, limit 30").
  - Matches: yes.
  - Precise: yes. The test-id exemption is used to pack three ids onto one line (display
    330 characters, convert 348). That is how three contracts reach exactly 30.
- **1.7**
  - Command: `agent-ready lane --base master` in my worktree, at `19d05de` and again at
    `b20ca29`.
  - Result at `19d05de`: exit 1, the two `.agents/skills/agent-ready-garden/` files from
    01efe85. With `--base 01efe85`: exit 0. So the deliverables alone pass lane (not
    recorded by the Builder).
  - Result at `b20ca29`: exit 1, now also naming `mkdocs.yml` (owner commit 306233b).
    It fails even with `--base 01efe85`.
  - Main checkout untouched.
  - Matches: yes at `19d05de`.
  - The recorded note "the gate reruns once 01efe85 leaves the branch range" is
    incomplete: 306233b must leave too. `checkpoint.md` item 1 says so correctly.
  - Precise: yes.
- **1.8**
  - Command: `diff` of `main-spec-edit.md` from line 5 against the sibling block (line 73
    of the sibling `spec.md`, last changed in 211a165).
  - Result: one hunk, `5c5`, the `Tests:` line; old is an exact prefix of new. The
    appended part is exactly the five `TestAMetaCommandIsNeverPartiallyApplied` ids. 24
    ids, 24 distinct; they collect as part of 1.2.
  - Matches: yes. Precise: yes.
- **1.9**
  - Command: `agent-ready check --set full --base master` with the four `--with` tools,
    in my worktree at `19d05de`.
  - Result: exit 1 in 8 s, `failing: fields, lane`.
    - `fields`: only `identifier-key-fields/.openspec.yaml: assurance is not answered`.
    - `lane`: the two 01efe85 files.
    - Every other step passed: codemap build, pre-commit (markdownlint), tach, OpenSpec
      specs/live/archive, interfaces, gates, toolbox, specs, reconcile, five
      `render … --check`, decisions, stage griffe/towncrier/vulture, budget, skills,
      codemap check, retired.
    - No pytest step: `check.py` appends the test command only when the change is not
      docs-only.
  - Matches: yes. Precise: yes.
  - The task stays open correctly. Its rerun must be on a head without 306233b as well
    as 01efe85.
- **1.11**
  - Command: my own block split (bullets, numbered items, paragraphs) of the `eb369dd`
    section, which is identical to `master`'s. Each whitespace-normalised block checked
    as a substring of the new section.
  - Result: 8 blocks, 0 missing.
  - Negative probe: deleting one word from the new section gives 1 missing.
  - Matches: yes. Precise: yes.
- **1.12**
  - Command: for each contract, the set difference of backticked tokens against
    `eb369dd` (identical to `master`); heading and `Interface:` survival; bullet counts
    under `## Invariants` and `## Precedent`. I added a sentence-level prose survival
    check.
  - Result:
    - Token loss: 0/0/0/0.
    - Headings and `Interface:` lines: kept.
    - Invariants: display 2→3, validate 2→3, convert 3→4, anonymize 3→4. Precedent
      unchanged.
    - The prose check finds convert's existing text reworded to fit the cap. "Not for"
      lost "direct", "that already has one" and the pointer "section 1". Invariant 2's
      "retains" became "keeps".
  - Matches: yes.
  - Precise: only for tokens and counts. The rewording is not recorded, and task 2.3
    says "nothing dropped". Meaning survives (`ARCHITECTURE.md` §1 item 2,
    "Simplicity"), but the section pointer is lost.
- **1.13**
  - Command: read the cited tests in full (AST extraction).
  - Result: the Builder's quoted assertions are accurate. Per invariant:
    - Display: holds as narrowed. `test_no_module_keeps_its_own_key` pins single
      ownership only by a deny-list of retired spellings and two banned imports. A new
      module computing keys some other way would pass.
    - Validate: holds. "However the dump bounds it" also covers `unbounded`, which only
      the uncited `TestCardinality::test_unbounded_is_list` pins.
    - Convert: holds. Set door UNPLACED plus strict raise; JSON/YAML/XML door
      kept-as-written message plus strict raise; meta partial or surplus key kept whole
      and 1 unplaced.
    - Anonymize: "passes every rule unchanged" is not literally asserted.
      `AnonymizeConfig` has nine rules. `test_a_key_choice_keyword_passes_unchanged`
      turns on eight (no `sensitive_words`); `test_an_enum_key_passes_unchanged` turns
      on eight (no `ssh_keys`). The walker assertion that no rule is offered
      `exact`/`accept` covers every rule only for those two route-filter keywords.
  - Probe (read-only, all nine rules on, `sensitive_words` and `sensitive_patterns`
    aimed at `exact`, `accept`, `add`, `as-list`, `as-list-group`): all pass unchanged.
    The behaviour holds; the test pins it only partly.
  - Correction to my phase-4 report, item 3: I wrote "with all rules on". That was
    wrong for both walker tests.
  - Matches: yes. Precise: partly; quoting assertions does not test the claim's scope.
- **1.14**
  - Command: greps over the 27 added lines of `settle-a-schema-question.md`: IPv4, IPv6,
    numbers of three or more digits, prompts, pathless captures, `display set|json|xml`,
    `private_test_data`, timing, opening line, release and hostname tokens.
  - Result: 0 addresses, 0 numbers, 0 prompts, 0 pathless captures, 0 timing figures,
    no device names. All three views named. "gitignored `private_test_data/`" present.
    The opening says "Five rules"; rule 5 is numbered.
  - Matches: yes.
  - Precise: yes, but the address and AS sub-checks are vacuous today because the form
    carries no example values.
- **1.15**
  - Command: the Builder's needle set (capture names plus `.conf` names in the sibling
    `tasks.md`), and a wider set (all top-level `private_test_data` names and stems).
    Matched against added lines in `docs`, `src`, `changelog.d` and the change folder,
    counting without printing the needles.
  - Result: Builder set 8 needles, 0 hits. The wider set hits only generic names
    (`captures`, `jvd`, `schemas`, "deactivate"). 0 identifiers.
  - Matches: yes. Precise: yes for file-name identifiers; content identifiers are out of
    reach (see Could not check).
- **1.16**
  - Command: my probes A to H (`convert_config_result`, set to set) at `19d05de`.
  - Result: A 0 unplaced, `set apply-groups G1` + `deactivate apply-groups`; B 0,
    `deactivate apply-groups`; C 1; D 1, the meta line not reproduced; E 0,
    `set system ntp` synthesised; F 0, reproduced; G 1, reproduced; H 1, reproduced.
  - Matches: yes, identical to the phase-4 run and the recorded evidence. Precise: yes.
- **1.17**
  - Command: 1.8's diff; read the `evidence-freeze.md` Requirements and Delta log and
    `review.md` S3.
  - Result: Requirements names the sibling wording (211a165) and "never applied to the
    main spec". The phase-4 delta-log entry names the replaced clause.
  - Neither says what the sibling's live delta, which still `ADDED`s the same
    requirement without the ids, drops or becomes.
  - Matches: yes. Precise: low; the "entry names the owner" half is inspection only.
- **1.19**
  - Command: the task's grep on the guide's added lines, then each hit read.
  - Result: 9 hit lines. "Stable for the same input and the same salt", "revert with
    the mapping restores the original", "Measure and explain … never a gate over
    correctness", and the `AGENTS.md` Verification pointer are all present and
    qualified.
  - Matches: yes.
  - Precise: for contradictions with `ARCHITECTURE.md` and the contract, yes. It cannot
    catch a factual error in a hit line: hit 1 is claim 5 below, which fails.
- **1.20**
  - Command: read the new section; matched its path lists against `git ls-files` and
    `[tool.template.domains]`.
  - Result: triggers on behaviour-bearing paths and excludes `CONTRACT.md` and
    `docs/`. Names `--jvd`, the baseline comparison and `test_device_truth.py`. Three
    report items. "a second read by a fresh agent, never a second human". This change
    touches no such path.
  - Matches: yes.
  - Precise: no for trigger coverage (claim 13 below). Wording inspection does not test
    the area lists against the tree.
- **1.21**
  - Command: `.openspec.yaml` against `fnmatch` of each deliverable over
    `[tool.template.domains.*].paths`.
  - Result: convert → `conversion`, anonymize → `anonymization`; display, validate
    contract, docs and changelog → none. Declared `[conversion, anonymization]`.
  - Matches: yes. Precise: yes.

### Sampled claims

1. Guide tier table, cross-format row:
   `uv run pytest tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr tests/test_convert_consistency.py tests/test_device_truth.py -q`.
   - Source: `--collect-only` gives "101 tests collected", exit 0.
   - Holds: yes.
2. Guide tier table, anonymization row: `uv run pytest tests/test_anonymize -q` plus the
   three probes by name.
   - Source: "369 tests collected", and "6 tests collected" for the three ids
     (`TestPipelineDumpMapIntegration`, the S4 fix).
   - Holds: yes.
3. Guide tier table, schema row: `uv run pytest --schema tests/test_schema_data.py -q`.
   - Source: `--help`: "--schema  run tests that need a device XSD dump in
     private_test_data/schemas/"; `tests/test_schema_data.py:20`
     `pytestmark = pytest.mark.schema`; `conftest.py:367` skips `schema` items without
     the flag; 12 collected.
   - Holds: yes (collection only).
4. Solo-review item 1: `uv run pytest --jvd tests/test_jvd_corpus.py -q`.
   - Source: `--help` lists `--jvd`; `tests/test_jvd_corpus.py:35`
     `pytestmark = pytest.mark.jvd`; 8 collected, and
     `TestFieldWarningBudget` 1.
   - Holds: yes (collection only).
5. Guide, new paragraph: "The one full checkpoint before review is `AGENTS.md`'s
   Verification rule; it runs neither the schema, the corpus nor the device tier".
   - Source, the same page's tier table: "| **Full** | `uv run pytest tests/ -q` | … |
     … run through the full checkpoint rather than beside it |" and "| **Device truth**
     | Automatic | seconds | Runs against capture pairs under `tests/data/captures/` and
     `private_test_data/captures/` |".
   - Source, `pyproject.toml`: `test-command = ["uv", "run", "pytest", "tests/", "-q"]`
     ("The full set runs this complete committed suite").
   - Source, `agent_ready_checks/check.py`:
     `if selected_set == "full" and not docs_only:` appends that command.
   - `test_device_truth.py` is default-tier: 23 collected with and without
     `-m "not schema and not jvd"`.
   - Holds: **no.** For every change this rule is about (code), the full checkpoint runs
     the device-truth tier. True for schema and corpus only. The row commands that add
     `tests/test_device_truth.py` beside the checkpoint repeat it.
6. Guide, entry-lookup row: "`src/junoscfg/display/constants.py` (`entry_keys`)".
   - Source: `constants.py:138 def entry_keys(schema_node: Any)`; exported in
     `display/__init__.py` `__all__`.
   - Holds: yes.
7. Guide, entry-lookup row: "the only committed bound … times the grammar".
   - Source: `tests/test_set_validator.py:299 result = bundled_set_validator.validate(source)`,
     `:302 assert elapsed < 5.0`. `git grep` for `perf_counter|time.time()|monotonic(|elapsed <|benchmark`
     in `tests/` finds no other.
   - Holds: yes.
8. Guide: "the identifier-key-fields change record (its tasks 4.4 and 5.6) shows the
   shape".
   - Source: 4.4 records a base-vs-after timing of one large private input on one
     machine; 5.6 is "the 30,000-entry plus … benchmarks".
   - Holds: yes. The guide does not name the file; the sibling's 4.4 does, in a
     committed file, which is pre-existing and not this change's.
9. Validate contract: "Any `maxOccurs` other than 1 makes a list, however the dump
   bounds it".
   - Source: `assert root.children["class"].is_list is True` (maxOccurs 16),
     `["source-port"].is_list is True` (32), `["host-name"].is_list is False` (1).
   - Holds: yes for numeric bounds. `unbounded` is pinned by the uncited
     `test_unbounded_is_list` (`assert ifaces.is_list is True`).
10. Anonymize contract: "A schema enum value or the keyword of a key choice is syntax and
    passes every rule unchanged".
    - Source: `test_a_key_choice_keyword_passes_unchanged` builds `AnonymizeConfig(ips=True,
      passwords=True, communities=True, ssh_keys=True, identities=True, groups=True,
      descriptions=True, as_numbers=[64496], salt="s")`, with no `sensitive_words`.
      `test_an_enum_key_passes_unchanged` has `sensitive_words=["as-list"]` and no
      `ssh_keys`. `config.py` declares nine rule switches.
    - Holds: **partly.** The product holds (my all-rules probe). "Every rule" is
      asserted by neither cited test.
11. Convert contract: an incomplete set statement, a keyed entry without its key from
    JSON, YAML or XML, and a meta command on a partial or surplus key "are kept whole
    and reported `UNPLACED`".
    - Source: `assert any(e.expected == UNPLACED for e in result.errors)`; `assert
      messages == ["'as-path-neighbors' entry without its key field 'list-type' could
      not be placed in the schema: kept as written, not validated"]` per door;
      `assert from_[suffix]["@"] == self._ATTRS[command]`, `assert len(_unplaced(...)) == 1`,
      `assert meta_line in dict_to_set(ir).splitlines()`.
    - Holds: yes.
12. Display contract: "`entry_keys()` and `statement_children()` are the one answer …
    and no module keeps a key spelling of its own".
    - Source: `assert entry_keys({"L": True, "k": ["list-type", "list-name"]}) == (…)`,
      `assert list(statement_children(keyed)) == ["accept"]`, and
      `retired_strings = {"fe", "values-only", "community-name"}` … `assert found == []`.
    - Holds: yes as worded, with the deny-list limit noted in 1.13.
13. Solo-review trigger: "validation (`validate/*_validator.py`,
    `convert/field_validator.py`)", "conversion (`convert/`)", "the grammar", "the
    schema pipeline (… `grammar_generator.py`)".
    - Source: `git ls-files 'src/junoscfg/validate/*_validator.py'` gives four files
      and not `validate/validator.py`. `pyproject.toml` `[tool.template.domains.validation]`
      lists `src/junoscfg/validate/validator.py`.
    - Holds: **partly.**
      - A change to `validate/validator.py` falls in no area.
      - `convert/field_validator.py` is both conversion and validation, so a one-file
        change "crosses more than one" area.
      - "the grammar" has no path of its own; its generator is listed under the schema
        pipeline and its output under the generated artifacts.
14. Solo-review: "the identifier-key-fields review found three High findings after the
    full check was green".
    - Source: sibling `review.md:236` "9. **Full check** at fc22c57: exit 0, "every
      check passed"" and `:252`, `:284`, `:307` "**1. High.**", "**2. High.**",
      "**3. High.**".
    - Holds: yes.
15. Settle rule 5: "The identifier-key-fields pilot took five probe rounds relayed
    through chat".
    - Source: sibling `tasks.md:34` "(device probe round 5)"; sibling `metrics.md:73`
      "relayed mid fix pass, device probe round 5".
    - Holds: yes.
16. Settle rule 5, the form, against `AGENTS.md` and rules 1 and 2.
    - Source: `AGENTS.md:41` "**Ask for a device artefact before inferring**, in set,
      JSON and XML" and "**Never request a whole configuration** — name a path"; settle
      rule 2 "Every capture request names a path"; `AGENTS.md` "Real configurations go
      in `private_test_data/`, which is gitignored".
    - Holds: yes. The form names the path (rule 2), all three views (rule 1), a pathed
      preflight, and the gitignored raw capture.
    - Small overstatement: "every operator value replaced by the synthetic ranges in
      `AGENTS.md`". The table covers addresses, AS numbers, passwords and user or host
      names, not policy names or descriptions.
17. `main-spec-edit.md` against the sibling delta and the main spec.
    - Source: `diff` gives only `5c5`, the `Tests:` line, old a prefix of new. The main
      spec's block (line 83 of `openspec/specs/conversion/entry-keys/spec.md`,
      wrapped), whitespace-normalised, equals the edit minus the meta sentences, the five
      ids and the two scenarios.
    - Holds: yes. `## MODIFIED` is right for the main spec, which holds the requirement
      since a920fab.
18. `docs-plan.md` source row: reproducibility from "`openspec/changes/identifier-key-fields/tasks.md`
    items 4.15 and 5.4".
    - Source: 4.15 reads "Re-review finding 11 … `is_keyword_field()` in
      `junoscfg.display` replaces the three local spellings"; 5.4 reads "Regenerate
      affected artifacts twice and prove reproducibility."
    - Holds: **partly.** 4.15 is the wrong item. The plan only, not a deliverable.
19. Convert contract rewording against task 2.3 "nothing dropped".
    - Source, old: "a second path for a pair that already has one is the duplicate
      `ARCHITECTURE.md` section 1 calls a defect". New: "a second path for a pair is the
      duplicate `ARCHITECTURE.md` calls a defect".
    - Holds: **partly.** The meaning survives; the section pointer is dropped, and the
      change is unrecorded.
20. Solo-review terminology: "every metadata verb (`deactivate`, `activate`, `protect`,
    `delete`)".
    - Source: sibling requirement "Meta commands never fall back to a valid prefix";
      `tests/test_set_input.py:175` "# ── Meta commands"; convert contract "a meta
      command".
    - Holds: **no.** A new synonym.

Summary: 20 sampled; 14 hold, 4 partly (10, 13, 18, 19), 2 fail (5, 20). Of the
failures, only claim 5 is substantive.

### Interim actions on S1 to S7

- **S1: partly resolved.**
  - `main-spec-edit.md` now carries the sibling's narrower sentence. Under its colon
    reading ("The same applies to `deactivate` …: a partial or surplus keyed-list key
    and an unknown path SHALL …") it no longer contradicts probes A, D and E.
  - The convert contract and the docs-plan row drop "every door" and "unmodelled path".
  - Remains for the owner:
    - "The same applies" can be read as carrying the whole first sentence (two
      `apply-groups` names, a second nokeyword value) to the meta commands. A and D
      would then contradict it. Wording such as "For `deactivate`, `activate`, `protect`
      and `delete`, a partial or surplus keyed-list key and an unknown path SHALL …"
      removes the reading. It is the sibling's text, so it is the owner's call.
    - The three defects need a `bug`-lane change with a device artefact (named path)
      first.
- **S2: resolved.**
  - The adopted text claims only that a whole-list meta attribute survives set output,
    which `test_a_meta_attribute_on_a_whole_list_is_written` asserts.
  - Remains (optional): the clause no longer mentions the placed positional value, so
    `…_positional_value_is_kept_whole` traces to no sentence or scenario. Its name still
    disagrees with its assertion (`_unplaced(...) == []`).
- **S3: partly resolved.**
  - One wording is adopted, and the overlap is logged in this change's
    `evidence-freeze.md` and `review.md`.
  - Archiving with `--skip-specs` (the change skill's rule) keeps the sibling delta from
    colliding.
  - Remains for the owner: the sibling's live `## ADDED` block still says nothing about
    being superseded. Record in the sibling's change record that this change owns the
    applied wording, or delete the sibling's block.
- **S4: resolved.**
  - `docs-plan.md` cites `TestPipelineDumpMapIntegration`.
  - The `evidence-freeze.md` Evidence line no longer claims all ids from a count.
  - 1.2 expects exit 0 and no `not found`, and fails on a bad id (my probe).
- **S5: resolved.**
  - The guide row says no committed timing guard covers entry lookup, and that the only
    bound times the grammar (claim 7 holds).
  - It prescribes measure-and-explain at base and head on one machine, "never a gate
    over correctness".
  - It names no private file and no path that moves on archive.
- **S6: resolved for display, mostly for validate.**
  - Display cites `test_no_module_keeps_its_own_key` and no longer claims
    `key_is_positional`.
  - Validate dropped "declared keys drive the generated artifacts". Its new tail
    "however the dump bounds it" reaches `unbounded`, which the cited test does not
    assert.
  - Remains: cite `TestCardinality::test_unbounded_is_list` too, or drop the tail.
- **S7: resolved for this change's self-application, partly for the rule's trigger.**
  - The rule triggers on behaviour-bearing paths, excludes contracts and docs, names
    corpus, commands and report, and says "fresh agent".
  - Remains for the owner: the area lists (claim 13). `validate/validator.py` is in no
    area. `convert/field_validator.py` and `grammar_generator.py` each sit in two, so
    one file triggers the rule. Reusing `[tool.template.domains]` as the areas would
    make the trigger mechanical.
- **New, not raised in phase 4:** claim 5 (the full checkpoint does run device truth).
  The fix is one sentence: "it runs neither the schema nor the corpus tier".

### Could not check

- 1.10 and 1.18: phase 7, by instruction. The telemetry file and the applied main spec
  do not exist yet.
- Whether the schema-tier, corpus-tier and regeneration commands pass. I may not run
  `--schema`, `--jvd` or `--regen-schema`; claims 3 and 4 are verified by `--help`,
  markers and collection only. The reproducibility recipe (a second `--regen-schema`
  leaves `git diff --stat -- src/junoscfg/validate/data` empty) is unexecuted.
- Device behaviour for defects A, D and E. This needs a device artefact for the named
  paths (`apply-groups`, `access securid-server`, `system ntp`).
- markdownlint on `main-spec-edit.md`: the hook excludes `openspec/changes/` (Skipped).
  Neither the Builder nor I linted it.
- Content-level identifiers. 1.15 matches file names only. Checking hostnames or values
  from private configurations would mean opening them, which I did not do.
- The Builder's working-tree runs before the commit (`qa_tree.py`, the recorded
  durations). They are not reproducible as such; I re-derived every result at
  `19d05de` instead.
- The Builder's worktree `junoscfg-wt-19d05de` is still registered, although
  `checkpoint.md` says "removed at the end". Possibly intentional for phases 6 and 7; I
  did not touch it.

### Verdict on the QA evidence

The recorded evidence is trustworthy. Every one of the 19 checks I re-executed
independently gives the Builder's result. The counts that can be compared match exactly:
46 ids and 154 nodes, 8 blocks with 0 missing, 9 hit lines, 8 needles with 0 leaks,
30/26/30/30 lines, and the HTML counts. Probes A to H reproduce. The full checkpoint
fails on exactly `fields` and `lane` with the stated causes.

The negative probes show that 1.1, 1.2, 1.6 (`caps`) and 1.11 can fail. The evidence is
not complete in four places:

- 1.7 names only 01efe85, while the current head also carries 306233b's `mkdocs.yml`,
  which keeps lane red from either base.
- 1.12 does not record that convert's existing prose was reworded to fit the cap.
- 1.13 quotes assertions accurately, but they do not carry the anonymize invariant's
  "every rule".
- No check compared the guide's new opening sentence with its own tier table. That
  sentence is the one false deliverable claim found (claim 5).

None of this is a behaviour change. Claim 5 should be fixed before the fresh review
closes. S1, S3 and S7 carry owner wording decisions, and the rerun of 1.9 must wait
until both 01efe85 and 306233b leave the range.
