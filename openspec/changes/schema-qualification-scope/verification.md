# Verification observations

Environment: isolated physical worktree, Python 3.14.7; installed dependencies.
Initial focused acceptance: 10 failed, 6 passed in 0.34s, reproducing both excessive
qualification and validator-body exemption. First repaired focused set: 138 passed,
4 fixture failures because synthetic locks had no execution dependencies (37.03s).
Fixtures now declare their synthetic lxml record. Corrected focused set: 142 passed
in 25.12s. Native-receipt/configuration/helper tests: 25 passed in 2.18s.
These are pytest elapsed observations, not complete workflow timings.

The shared dependency is developed/reviewed/released separately before adoption.
Full checkpoint, final focused/fast commands and native selection demonstrations
remain pending. No evidence is copied from another physical root.

Broader affected schema tooling: 260 passed, one receipt-identity failure in
172.23s. Source edits during execution changed native identity; holding the tree
stable, the exact semantic-schema-21.4 test passed (1 passed in 8.33s).
Final selector-focused set: 118 passed in 17.79s.
Initial commit hook: 10600 passed, 37 skipped, 20 xfailed, five new fixture errors
in 223.61s. The new module lacked the existing autouse Git-environment isolation;
added that fixture so synthetic native receipts cannot inherit hook Git paths.
Actual boundary preparation also caught binary artifacts in Python-source seeds;
restrict source traversal to .py and add a real-tree regression.

Shared release: checks-v0.17.3 (`eb4677957235c0ec77c6c1d014fb03c9dbe51d3e`)
and template v0.13.3 (`4b5d22ace12f2d779153373ec108069b0626ea7a`) were independently
reviewed, merged and tagged locally upstream. Adopted by exact updater commit
`1aef9ef`; normal full affected-test hook passed. Post-adoption scaffold and cap
homes checks needed no changes; skill mirrors regenerated. Accepted hook policy
remains current. Native scoped runtime probes succeeded in 2.554/4.926 seconds
(cumulative for the two tiers). Final selection regressions: 34 passed in 2.47s.
The direct transitive-selector fixture initially lacked its dependency projection;
initialized through the normal writer, then passed. No production workaround.

Instruction delta: reviewed upstream adoption changes shared identity wording
and ownership notices; local classification and executable checks remain here.
No ordinary test, integrity, coverage or independent review requirement changed.

Canonical full at `f401245cec541c02de7ab91ec0d20ffb810f3215`, base
`b20aa2b116fac222a2cf46306632b2dcb4ea442b`: **failed workflow gates**, 363.81s
(`/usr/bin/time -p`, private log `schema-scope-full.log`). Ordinary suite passed:
10612 passed, 37 skipped, 20 xfailed in 70.923s; both real-schema tiers passed,
12 required assertions in 261.11s and both generation stability passes.
Content checks executed fresh. Qualification selected due to changed pyproject
execution settings. OpenSpec rejected missing inherited scenario headings;
restored with the newly authorized semantics. Lane rejected the combined history
containing an exact updater commit and normal application changes. This is being
resolved upstream rather than weakening the gate. Native successful tier receipts
remain valid evidence even though the overall checkpoint failed.

Real evidence reuse demonstration: after documentation/evidence-only commit
`9155303`, the selector against qualified head `f401245` returned exactly
`{"selected": false}` in 3.57s. The canonical full command with that base then
**passed every check in 83.88s**, selecting neither schema tier. Ordinary suite:
10612 passed, 37 skipped, 20 xfailed in 68.821s; branch-enabled coverage
92.967863894%, unchanged floor 91.47%. Log: `schema-scope-no-schema-full.log`.
This is one real observation below the accepted 95-second no-schema target,
not a general performance trend. No cache/evidence bytes were copied or relabelled.
The combined original-baseline lane obligation remains open until shared updater
checkpoint handling is adopted and that full command passes.

Phase-7 spec preparation: OpenSpec 1.13.0 archive applied the reviewed delta in
`/private/tmp/junoscfg-schema-scope-spec-sync`, a disposable `git archive` snapshot.
Only the resulting main specification was copied to the live branch. The live
change remains open; the disposable archive is not completion evidence. Result
matches the two reviewed MODIFIED requirements and preserves inherited scenarios.
