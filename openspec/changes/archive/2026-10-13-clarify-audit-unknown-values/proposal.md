## Why
The unknown-subtree walker docstring says every string is collected, obscuring numeric references and excluded metadata for audit maintainers.
## What Changes
Clarify only `_walk_unknown`'s private docstring to describe the existing scalar and attribute handling.
Preserved behaviour: identical executable AST; occurrence values, paths, kinds, order and all public surfaces unchanged.
Verification: compare ASTs after removing docstrings; run existing audit walker tests, normal hooks and canonical full checkpoint with native schema selection.
Changelog: changelog.d/+clarify-audit-unknown-values.misc.md, required by the stage gate; no user-visible behavior change.
Acceptance: wording matches `_emit` and recursive traversal; focused tests and required gates pass; fresh reviewer approves.
Exclusions: no runtime repair, new feature, test rewrite, dependency change or schema-policy change.
Approved under the owner's explicit delegation to select and locally integrate harmless maintenance; no unresolved decision.
