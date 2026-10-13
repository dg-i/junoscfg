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
