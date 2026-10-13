# Independent review: native production verification

Reviewer: fresh GPT-6.1-sol review agent; no product write access used.
Agent-ready-python worktree: `/private/tmp/agent-ready-verification-production`.
Final reviewed range: `43433b033c0f2dc9565c071ccdda595b2d72a097` through `4e8f8faf44a77c1e59fcd351fd00dc02aa677a58`.
Verdict: APPROVED. No unresolved actionable findings. The required builder full-suite checkpoint remains a separate merge prerequisite.
Initial review at `464bdfb1b220025fb77cc25acd011cf7378685c0` requested the two corrections recorded below.

## Scope and evidence

Read the approved application freeze, upstream AGENTS, architecture and self-application boundary, shipped guide and package README, product diff, containing verification/check/readiness modules, stage/lifecycle callers, and all new challenge/runtime tests. The upstream package has no module CONTRACT files; shipped public guide is its applicable behavior contract. Template defaults remain serial and disabled; this diff introduces opt-in scheduling only. Scheduling keeps mutation-capable gates as barriers, selected tiers serial, capacity/admission wrapping and outer checkpoint behavior. Strict selector acceptance rejects duplicate keys, non-Boolean answers and failed/unavailable output.

Focused verification: `checks/.venv/bin/python -m pytest checks/tests/test_verification_runtime.py checks/tests/test_verification_challenge.py -q` => 43 passed in 3.30 seconds. No broad suite was run by this reviewer. The builder separately reported 770 passing upstream tests at the reviewed SHA; this report does not present that result as independent evidence.

## Resolved findings from initial review

### P1: symlinked package directories are omitted from executable identity

File: `checks/src/agent_ready_checks/verification_runtime.py:102`.
Requirement: shipped verification-evidence guide binds ignored importable code and says symlinks fail closed; native receipts must invalidate when executing-engine bytes change.
Executed counterexample: add untracked application/linked_package symlink pointing to an external package directory with `__init__.py` containing `VALUE = 1`. Set import path to application root, snapshot `imports(root, sources=True)`, run normal Python `import linked_package` with `-B -S`; mutate source to `VALUE = 2`, repeat. Python prints 1 then 2, while both native identities are equal and their file maps are `{}`. Path.rglob does not traverse the symlink directory. The same traversal is shared by declared-runtime `sources=False`.
Correction: reject unsupported symlink import directories before omission, or completely bind their execution input. Add an executed import control, not just a fixture fingerprint expectation.

### P1: excluded node_modules namespace can contain normal Python imports

File: `checks/src/agent_ready_checks/verification_runtime.py:104`.
Requirement: same ignored-importable-code/native execution identity invariant.
Executed counterexample: create application/node_modules/extension.py containing `VALUE = 1`. Snapshot identity with sys.path=[application], run `import node_modules.extension`; change VALUE to 2 and repeat. Python prints 1 then 2, native identity stays equal and file map stays `{}`. Python namespace imports can use this directory normally. The unconditional node_modules exclusion is therefore unsound even when external tooling conventionally owns that name.
Correction: include importable executable bytes under node_modules, or fail closed on that reachable import scope.

## Review prompts

Trust boundary: local executing-engine bytes cross into reused verification evidence; the two executed omissions above violate that boundary without importing arbitrary receipts.
Incompatible valid input: normal Python package-directory symlinks and namespace imports are executable inputs omitted by implementation assumptions; the first can conservatively refuse under existing declared policy, the second must be bound or refused.
Shared blind spot: existing fixtures cover direct ignored modules and distribution caches but omit directory symlinks and namespace paths named after other ecosystems. The two independent subprocess probes demonstrate actual imports.
Second answer: selectors remain application-owned; native code accepts only exact classification and preserves conservative unknown behavior. No duplicate application schema classifier was introduced. Runtime observation and command qualification are kept distinct.
Figures and exclusions: template defaults were inspected in both table renderers and are unchanged. The application experiment timings are outside this upstream review; this report does not certify them or a 45-second target. No product syntax/schema behavior changed in this upstream diff.

## Final correction review at 4e8f8fa

Reviewed the complete correction commit independently. Both P1 findings are resolved: import traversal now follows directory links, records link targets, fingerprints reachable code, detects physical-directory cycles, and raises traversal/access errors; node_modules and .venv are included. The public guide now distinguishes unsupported candidate/declared-input symlinks from runtime import links whose target bytes are bound. Candidate and explicit-input local_path/manifest restrictions remain intact. Git administration remains pruned; `.git` is not a normal Python import namespace.

Independent isolated recheck (no concurrent test suite): build an application root containing an external linked package, an external directory cycle, node_modules/extension.py, and `.venv/lib64 -> lib`. For BOTH `sources=True` and `sources=False`, changing linked package VALUE changed identity, changing namespace VALUE changed identity, changing library VALUE through the Linux alias changed identity, and cycle traversal terminated. Observations were:

```json
[{"cycle_terminated":true,"linux_alias_changed":true,"namespace_changed":true,"sources":true,"symlink_changed":true},{"cycle_terminated":true,"linux_alias_changed":true,"namespace_changed":true,"sources":false,"symlink_changed":true}]
```

Linux compatibility: the final implementation follows and binds ordinary lib64 directory aliases rather than rejecting all directory symlinks. This synthetic topology executed successfully for both runtime modes. Linux was not available as an execution host; this is a topology/behavior probe on macOS, not a claim of a full Linux platform run. This preserves the executing-engine identity contract while candidate and declared file symlink rejection remains unchanged.

Independent error-propagation recheck: sentinel raises OSError, second tier raises ValueError, and all three declared commands are attempted. Returned status was 1 with exact order `["sentinel", "first", "second", "third"]`. The new helper catches only native identity/execution refusal exceptions and does not short-circuit later tiers or turn their failures into success. Builder regressions additionally execute actual linked-package and namespace imports before/after mutation and include both refusal exception cases.

Builder-reported correction evidence: 55 focused tests and root fast hooks passed; final complete package suite running when this review finished. This reviewer did not duplicate that suite. The final commit was clean at independent inspection. No product files were edited by this reviewer.

Final approval applies to the exact immutable SHA above. Required CI-equivalent builder package/template evidence must pass before local merge. This upstream review does not certify the application adapter, application production timings, application checkpoint, or authorize a remote push.
