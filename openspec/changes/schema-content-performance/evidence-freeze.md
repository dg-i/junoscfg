## Resolved instructions
See instruction-integrity.md; owner authorized required records after research approval.
## Requirements
schema-pipeline/verification-evidence retains all existing obligations and adds
exact-content pure-check proof reuse with explicit lineage.
## Evidence
Research executed existing Draft202012 check (193 seconds), Lark compile (11 seconds),
12 corpus cases, two serial builds, exact artifact comparisons and failure probes.
## Non-goals
No acceptance/dialect/CLI changes, cross-machine reuse, or global identity weakening.
## Acceptance criteria
Fresh inputs and unchanged protected products; failed/changed/corrupt evidence refuses reuse.
Independent template tests cover bytecode, dependency, mutation, lock and corruption cases.
Existing schema adapter tooling tests and all three available device releases pass.
## Performance expectations
Three warm complete native shipped-release qualifications <=180 seconds; cold runs measured
separately. Approximately 201 MiB additional serialization memory accepted by owner.
## Outstanding decisions
None, because the owner approved the design, memory tradeoff and required records.
## Execution and checkpoint
- Assurance preference: economy.
- Risk floor: high, verification trust boundary.
- Roles required: Builder, independent Test/Challenge, fresh Reviewer.
- Resume point: Phase 7 metrics capture and final record commit; implementation,
  native qualification and fresh integrated review are complete. Last full evidence:
  e8ff3cfcf7d92fc1aab6862305add4f36bb06e90, 10,448 passed, native checks exit zero.
## Delta log
- Independent challenge required isolated source imports without stale bytecode or startup hooks;
  this implements the approved engine-identity promise. No requirement was weakened.
## Scope and completion
Implement the approved design; native timings include guards, process start, receipts and builds.
