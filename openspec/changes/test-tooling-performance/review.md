# Independent maintenance review

Verdict: APPROVE the reviewed implementation; canonical full checkpoint remains outstanding before merge.

Reviewed candidate: `996dc27cdb4fec30f19e71d211ab17bb004af945`.
Base: `a7da186460b5d5991c27a7301fb61e421bd22ece`.
Reviewer operated in a fresh isolated agent context without Builder private reasoning. Read the repository rules, maintenance route, committed proposal/preflight/verification, review-scope policy, test and schema-verification contracts, complete diff, containing test module, production runtime preparation/preflight, and shared-helper consumers. Graphify graph is absent in this worktree; source and contracts supplied the review evidence.

## Findings

No actionable defects or specification challenges identified.

- `tests/tooling/test_schema_verification.py:91–106` caches only immutable bytes returned by genuine `prepare_runtime`. The temporary preparation policy chooses the output path; runtime contents are independent of candidate root and shard. Its directory is resolved to avoid the existing symlink rejection on macOS temporary paths.
- `tests/tooling/test_schema_verification.py:206–209` writes those bytes into each freshly committed synthetic repository. There is no shared file, dictionary, assertion result, generation result, or verification success manifest. JSON mutation tests decode fresh dictionaries. Inspection found no existing callers that monkeypatch runtime observation/preparation before initializing the cache.
- Fresh verification remains genuine: `tools/schema_verification.py:163–167` compares the supplied bytes against a new `observe_versions()` result, and preflight calls it at line 261. An installed runtime change therefore causes refusal rather than reuse of successful evidence. Child pytest and public generation execution paths are unchanged.
- The new isolation test corrupts one repository's copy, verifies another against the real runtime, checks both roots contain only the runtime input under `.agent-ready`, and checks clean Git status. Existing runtime refusal, mutation, completion, sentinel, metadata stability and generation obligations are retained. No assertions, parameter cases or existing tests were removed.

## Executed evidence

Reviewer command (focused only, using the candidate's installed environment):

`.venv/bin/python -B -m pytest tests/tooling/test_schema_verification.py -o addopts='' -p no:cacheprovider --basetemp=/tmp/test-tooling-performance-review-tests -q`

Result: **39 passed in 10.54s**. No full suite or full check was run by Reviewer. No candidate source was edited.

During review HEAD advanced to `349386d` with metrics documents only. `git diff 996dc27 HEAD -- tests tools` was empty; executed test/helper/runtime code is the reviewed candidate's code. Worktree status remained clean.

Reviewer parsed the recorded `/tmp/tooling-before.xml` and `/tmp/tooling-after.xml` independently: 192 versus 193 unique classname/name identities, no removed identities, no changed outcomes, exactly the added isolation test. XML times are 102.615s and 83.102s, consistent with log summaries 102.62s and 83.10s. This supports the recorded single-pair 19.0% tooling improvement. The command and environment versions are recorded; the claim appropriately does not establish a repeated-run performance distribution or a full-suite speedup. Raw timing artifacts are local diagnostics, not durable repository evidence; no stronger timing claim is approved.

## Remaining gate

Parent must run the canonical full checkpoint on the integrated candidate after any merge-base refresh and resolve failures before merge. This approval does not substitute for full-suite coverage or the repository's other policy gates.
