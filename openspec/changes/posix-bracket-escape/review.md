# Review: posix-bracket-escape (ledger #20: DEV-V5 = NEW-A4, PROC-F1)

Reviewer: a new isolated agent (Claude Opus 5.5) that did not see the Builder's reasoning. This is the lightweight review the orchestrator requires (preflight C2).
Branch `change/posix-bracket-escape`, base 50b0a10, head f4062eb. I read the
preflight/freeze (`instruction-integrity.md`), the proposal and `.openspec.yaml`
(`skip_specs: true`, so there is no delta), `src/junoscfg/convert/CONTRACT.md`
(it says nothing about pattern dialect), the new test and the diff. There is no
challenge evidence for this change, because the fix lane has no phase-4 role.

## Verdict

**APPROVE.** The findings below are low severity. All of them concern spellings
the shipped schema does not contain, so none blocks the change. F1 and F2 are
record-only corrections to the proposal's "Remaining failure mode" line, and the
Builder may fold them in with no confirmation round.

## What I reran (scripts and outputs in this folder)

| Claim | My result | Evidence |
|---|---|---|
| The regression test fails on the base for the right reason | It fails at 50b0a10 on its warning assertion: `['Possible nested set at position 3'] == []`. The verdict assertions agree at base and head, so the failure is the warning alone, as intended. | throwaway detached worktree at 50b0a10 with the head test file, now removed |
| The regression test passes at head | `test_field_validator.py`: 161 passed, 1 xfailed (pre-existing) | head worktree |
| All 263 shipped patterns compile to the same `re` program; only #49 and #83 are spelled differently | Text differs for 2 of 263 (#49, #83). The compiled `re._compiler._code` program differs for **0 of 263**. Under the old spelling #49 and #83 warn; under the new spelling none of the 263 warns (cache purged before each compile). There are no compile errors. 55 of the patterns are negated. | `scan263.py` plus an inline program comparison |
| Before/after comparison | **0 of 96 conversions differ** (`compare.py`, identical to `compare-template.py`). The base stderr carries `field_validator.py:206: FutureWarning: Possible nested set at position 4` once; the head stderr is empty. So PROC-F1 has the same root cause and closes here. | `base.json`, `head.json`, `base.err`, `head.err` |
| Device-evidence checks | 3,664 passed, 5 xfailed, run with `-W error::FutureWarning` | head worktree |
| Fix-lane caps | 2 substantive files, +26/-4 = 30 changed lines, exactly at the cap. The proposal has 9 lines. `agent-ready caps` exits 0. `agent-ready lane --base 50b0a10` exits 0. | `lane.log` |
| Other callers | `_posix_to_python_re` has one caller, `FieldValidator._get_pattern` (`field_validator.py:214`). No second POSIX-to-`re` translator exists in `src/` (the `validate/` package carries patterns through and compiles none). | grep |

## Adversarial probe (`probe.py`: old and new translator, Python `re`, and a libc POSIX ERE oracle via `regcomp`/`regexec` with `REG_EXTENDED`)

These cases match the same strings before and after the change, and agree with POSIX:
`[]abc]`, `[^]]`, `[a-]`, `[[:alpha:][:digit:]_-]`, `[[]`, `[][]`, `[^[]`,
`[[-a]`, `[[[[:digit:]]`, `\[[[:digit:]]\]`, `[[:alpha:]]x]`, anchors,
alternation, `[[:punct:]]`, `[^[:space:]]+`, `[[:xdigit:]]{2}`, and the shapes of
#49 and #83. The old spelling warned on every `[[`-led case; the new spelling
warns on none of them.

## Findings (ranked)

**F1 (low; documented claim).** The proposal says "Match semantics are unchanged". That holds for all 263 shipped patterns, but not for every input. The rewrite also changes matching for two unshipped spellings:
- (a) `^[:alpha:]$`. The old translator replaced the class text outside any bracket and produced `^a-zA-Z$`, a literal string. The new translator leaves a top-level bracket `[:alpha:]` that matches one of `:alph`, which is what POSIX does. This is an improvement, but it is a change.
- (b) Unterminated `^[[:alpha:]$` and `^[a[:alpha:]$`. The old spelling, `[a-zA-Z$`, raised `re.error`, so `_get_pattern` stored the never-match fallback. The new spelling, `[\[:alpha:]$`, compiles and accepts `[ : a l p h`, but POSIX `regcomp` rejects the pattern (REG_EBRACK). The cause is that `_BRACKET` can backtrack out of a class and use the class's closing `:]` as the end of the bracket.

The diff lines responsible are `field_validator.py:126` (`_BRACKET`) and the docstring at line 132. Proposed correction (records only): state "unchanged for every shipped pattern (0 of 263 programs differ)", and add (b) to the remaining failure mode.

**F2 (low; remaining failure mode incomplete).** Python dialect warnings still reach `re` for spellings the translator passes through:
- `[a&&b]`: "Possible set intersection"
- `[[:alpha:]--]`: "Possible set difference". POSIX rejects this pattern; Python accepts it.
- `[[:foo:]]`: "Possible nested set" for an unknown class. POSIX rejects it.

None of these is shipped. The proposal names only `\`, `[.x.]` and `[=x=]`. Proposed correction: add `--`, `&&`, `||`, `~~` and unknown class names to the remaining-failure-mode line. I confirmed the named ones too: `[[.a.]]` and `[[=a=]]` match `a]` rather than `a`, and `[\]]` matches `]` where POSIX expects `\]`.

**F3 (low; test strength).** The regression test pins the #49/#83 shape on a synthetic schema. It does not sweep the shipped `_patterns`, so the next shipped pattern that triggers a different Python `FutureWarning` (F2) would go unseen. That matters because no pytest `filterwarnings = error` is configured and the full-example validation test is an xfail. Proposed added test, which is not required for this lane: compile every `load_schema_tree()["_patterns"]` entry through `_posix_to_python_re` with warnings recorded, and assert that none warns. It runs in milliseconds. One weakness to note: an implementation that silenced warnings inside the product code would also pass the current test.

## The five prompts

1. **Trust boundary.** Patterns come from the schema artefact: the shipped one, or one `validate/artifact_builder.py` builds from a Junos XSD. They do not come from configuration input. The configuration values matched against them are untrusted, but the change does not touch how matching happens (`compiled.search`, `field_validator.py:662`). I found no new boundary exposure. The only fail-open shift is F1(b), and it needs a malformed schema pattern.
2. **Incompatible-but-valid input.** Within valid POSIX ERE, the backslash, collating and equivalence spellings (F2) and the top-level class spelling (F1a) differ from POSIX. All of them are outside the shipped schema. I did not invent a compatibility promise.
3. **Shared blind spot.** The test and the implementation both treat "no warning for the #49/#83 shape" as the criterion. The user-visible outcome is "no FutureWarning on any validated conversion". I checked that outcome independently: head stderr is empty across all 96 conversions, and the program is the same for all 263 patterns. F3 proposes making this a standing criterion.
4. **Second answer.** None. The translator is the one place the schema's POSIX dialect meets `re`, and the global `str.replace` it replaces is gone.
5. **Figures and non-goals.** I reran all of them: 263 patterns, 2 respelled, 0 programs differ, 0 of 96 conversions differ, 3,664 device-evidence tests pass, caps 2 files and 30 lines. The non-goals contain no claim that something "cannot" be done.

## Specification challenges

| Artifact | Counterexample | User impact | Proposed correction | Decision |
|---|---|---|---|---|
| `proposal.md` "Match semantics are unchanged" | `^[[:alpha:]$`: before, never-match; after, accepts `[`. `^[:alpha:]$`: before, a literal `a-zA-Z`; after, one of `:alph` | None today: 0 of 263 shipped patterns are affected. A schema built from another XSD with such a pattern would validate differently | Scope the claim to the shipped patterns, and list the unterminated-bracket case as a remaining failure mode | Pending owner decision. Interim action: merged with the narrowed claim (owner intake 2026-10-11: merge with recorded interim action) |

## Definition of done (DEV-V5, NEW-A4, PROC-F1)

- Reproduction: yes; the base stderr carries the warning.
- Regression test: fails at base, passes at head.
- Doors and formats: covered, because every door reaches the one call site and the before/after comparison runs 4 inputs by 4 outputs over every capture.
- Negative cases: verdicts of `1` and `a b` are False.
- Device citations: n/a (this is a dialect fix, not a device claim).
- Changelog: the fragment is present.
- Counts and docs: none are affected; no doc mentions the translator.
- Version: the orchestrator bumps it at merge.

## What I could not check

- Junos's own regex engine. The oracle was macOS libc POSIX ERE, not the device. Every comparison except the F1 and F2 counterexamples agrees with it, so the next failure would be a Junos-specific dialect extension appearing in a future XSD. Carry this forward with F2.
- Python versions other than the worktree's interpreter. The pattern syntax used is valid on 3.10 or later, and `FutureWarning` texts vary by version. I did not test this.
- The full check. I did not rerun it, as the brief directs; the Builder records it passing at a2edf23.

## Resolution (orchestrator rulings, applied by the Builder)

- F1, accepted and record-only: `proposal.md` now says every shipped pattern keeps its `re` program (0 of 263 differ). It names the two unshipped shapes that change: an unterminated `^[[:alpha:]$` now compiles instead of never matching, and a bare `[:alpha:]` outside brackets is now a set, as in POSIX. Its specification challenge is recorded above, pending the owner.
- F2, accepted and record-only: the proposal's remaining failure mode now lists an unterminated bracket, the set-operation pairs `&&`, `--`, `||`, `~~`, and unknown class names.
- F3, deferred: a sweep asserting that no shipped pattern warns would break the fix-lane caps (this change already uses all 30 lines). It is in the ledger as follow-up T5 `pattern-sweep-no-warning`.
- None of these edits touches code or tests, so no re-review was needed and the full check at a2edf23 still stands.
