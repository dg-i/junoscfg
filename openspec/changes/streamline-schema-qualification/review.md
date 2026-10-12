# Fresh review: streamline-schema-qualification

## Verdict
APPROVE source/harness at immutable clean commit 0f6d65eb493bc72c1a93cea7dce95f72cfe1fd5d against baseline 9bdd15dac7fd6997474c1979c92bb1c001c7e362. Both initial P2 findings are resolved; no surviving source finding or specification challenge. Final evidence review also APPROVES the completed canonical full checkpoint, reviewed main-spec synchronization and real 25.2 qualification. No surviving findings or unresolved review carry-forward items.

## Review scope and evidence
Fresh isolated review read freeze, delta, contracts, independent challenge and tests before implementation. Root explicitly requested harness review before costly real-schema qualification. Compared committed source with previously reviewed corrections; working tree clean. Reviewer executed two bounded tiny-fixture counterexamples, never a real XSD or full suite. Builder reports meaningful red/green regression evidence, focused qualification/challenge/config tests, and passing normal commit hooks including ordinary suite. These are reported evidence, not misrepresented as reviewer reruns.

Exact existing 12 assertion IDs per release and schema corpus remain unchanged. Assertions execute once; public generation executes twice under installed template stability ownership. Both public build_from_xsd and direct grammar-generation checks remain. Generation requires exact assertion completion and immutable exports, compares four raw products and all metadata except generated_at, and compares shipped products against committed artifacts. Template output hashes govern reuse; independent corruption probe forces fresh builds. Missing completion, public build failure, semantic drift, source mutation and input mutation retain no successful generation completion.

Old releases remain explicitly available through qualify and retain exact approved skips. Automatic declaration order is shipped assertions then generation; workflow-only files do not match generator/schema paths. Pytest phase durations and perf_counter build time are diagnostic only. No new runtime generator, schema acceptance rule, dependency, or application cache was introduced. Three builds rather than speculative two are accurately documented; no measured speed threshold is claimed.

## Resolved findings
P2 Git context: qualify now scopes all installed admission/capacity/execution calls inside sanitized Git context and restores caller selectors in finally while preserving protocol authorization. Regression retains polluted environment through entry and verifies actual Git repository selection and caller restoration.
P2 explicit generation input admission: generation prerequisites now enter the same centralized normalized _read_inputs set for dirty admission and mutation snapshot. Required/stability paths using both ordinary and ./ evidence-record spelling are tested to refuse before build.

## Required review prompts
Trust boundary: physical dumps/runtime identity, local prerequisite exports, dirty tracked inputs and inherited Git selectors. Existing early refusal and two corrected cases protect this boundary.
Incompatible valid input: inherited hook environment and explicit generation manifest at evidence-record spelling were executed counterexamples and are corrected.
Shared blind spot: controlled challenge builds alone do not prove real-schema parity or speed. The completed real 25.2 qualification supplies parity and measured elapsed evidence; the historical comparison remains uncontrolled.
Second answer: no competing cache or generator was added. Native wrapper remains identity, locking, stability and reuse owner; adapter owns application assertions and comparisons.
Figures/non-goals: three 12-ID required manifests and unchanged schema corpus verified. Historical 31.6 minutes is context, not an asserted causal improvement. Current measured timings are recorded below.

## Carry-forward
None remaining for this review. Main-spec synchronization was independently compared requirement by requirement: exact approved delta (two modified, one added, five untouched). Final qualification evidence is independently verified below. Merge/archive decisions remain outside this review verdict.

Context expansions: installed agent_ready_checks/verification.py and readiness.py (native identity/stability/capacity semantics); tests/corpus/test_schema_data.py and validate/CONTRACT.md (retained generation paths). No applicable decision record is changed; existing release-count oracle remains untouched.

## Final executed-evidence review
Reviewer read retained receipts and logs without rerunning expensive work. Canonical full receipt `f4feb69465f645f89e5ee5ac288026c5.json` is complete with exit zero; its verified log reports 10,392 passed, 37 skipped, 20 xfailed and every check passed.

Assertion receipt `a5e4c3c5d6cca80a8171410d8c21223a0fdc548589144b6c8d84ae9e624d1385.json` records 12 passed, 24 deselected in 823.58 seconds. Its exact result matches all 12 required IDs, every recorded call passed, and all 36 setup/call/teardown durations are present and nonnegative.

Generation receipt `90e36b11eaa7f3c84252e0402f10f724c37f92ddc1f01f4b83aa67a8c989ad4d.json` is complete with exit zero. Its hash-verified native log contains two public builds measured at 215.74688150000293 and 215.88739716698183 seconds. The retained six result hashes cover generation completion plus four protected raw products and canonical metadata. Independently checked all four raw products against both assertion exports and committed shipped artifacts; all match. Metadata agrees across all three sources excluding only generated_at.

Both qualification receipts pass installed `verification.valid` against their recorded identities; all current declared input hashes and native log/result hashes match. No source, tests, executable policy or lockfile changes occurred after approved source commit 0f6d65e. Native command durations total 1261.679596 seconds (21.03 minutes), including wrapper overhead. Historical 1897.69 seconds used Python 3.14.7 while current evidence uses 3.13.15, so this is an observed comparison, not a controlled causal speedup measurement.
