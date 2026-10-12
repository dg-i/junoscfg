# Fresh review: streamline-schema-qualification

## Verdict
APPROVE source/harness at immutable clean commit 0f6d65eb493bc72c1a93cea7dce95f72cfe1fd5d against baseline 9bdd15dac7fd6997474c1979c92bb1c001c7e362. Both initial P2 findings are resolved; no surviving source finding or specification challenge. This approval authorizes the scheduled expensive qualification; it does not claim its result in advance.

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
Shared blind spot: controlled challenge builds do not prove real-schema parity or speed; scheduled 25.2 qualification must supply that evidence.
Second answer: no competing cache or generator was added. Native wrapper remains identity, locking, stability and reuse owner; adapter owns application assertions and comparisons.
Figures/non-goals: three 12-ID required manifests and unchanged schema corpus verified. Historical 31.6 minutes is context, not an asserted improvement. Actual current timings remain pending.

## Carry-forward
Inspect canonical full-check/25.2 native receipts for all 12 passed assertions, two real public builds, hash-bound outputs and accurate timings. Inspect exact reviewed main-spec delta synchronization. These are scheduled remaining evidence checks, not source findings. No final release-completion verdict until they are supplied.

Context expansions: installed agent_ready_checks/verification.py and readiness.py (native identity/stability/capacity semantics); tests/corpus/test_schema_data.py and validate/CONTRACT.md (retained generation paths). No applicable decision record is changed; existing release-count oracle remains untouched.
