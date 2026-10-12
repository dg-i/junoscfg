# Lightweight maintenance review

## Verdict

Approved. No actionable findings or specification challenges.

Reviewer independently reviewed immutable candidate `7b61b23e60096c752d1923d845bbdcd632126bd9` against `630a5c9`, the committed proposal/preflight, maintenance route, test and validate contracts, existing owning-module tests, and relevant artifact serialization semantics. No Builder private reasoning was supplied.

## Evidence

- The added test calls public `ArtifactBuilder.build` twice on a synthetic NETCONF reply without mocking extraction, parsing, fixes, or generation. Existing focused tests remain intact, and the diff changes neither runtime nor qualification policy.
- All five outputs are read using public artifact readers. Both schema definitions pass Draft-07 checking and accept a known configuration; malformed containers and unknown paths are rejected. YAML metadata acceptance is checked separately from JSON.
- Saved structure-tree semantics cover containers, leaves, childless presence, annotated keyed entries, and a keyless leaf-list. A shared named complex type and nested sequence/choice declarations are exercised. The documentation correctly avoids claiming exclusive-choice enforcement or exhaustive annotations/shapes.
- Generated grammar is compiled and exercised on accepted and rejected statements, and agrees with grammar rebuilt from the saved tree. Metadata records namespace-derived version, fixes and representative statistics.
- Two builds compare every artifact's content, excluding only metadata `generated_at`. This is a reproducibility check, not an unwarranted format-equivalence claim.
- Independent focused run: `.venv/bin/python -m pytest tests/unit/validate/test_artifact_builder.py::test_public_build_produces_usable_reproducible_artifacts --durations=1` passed in 0.09s, with 0.03s test call and tool-reported command wall time 0.143s. This supports the approximately five-second target on this machine without a timing assertion.
- The initial `uv run --locked --group dev pytest ...` could not access the sandbox-protected uv cache. The independent run used the existing worktree environment and produced only a harmless pytest cache-write warning. No full or real-schema run was attempted by Reviewer; the root-coordinated canonical full checkpoint remains outstanding.

## Specification challenges

None.

## Final receipt confirmation

Approval remains valid for `d431134`. The diff from reviewed `7b61b23` contains only workflow records/admission and the required misc changelog fragment; test source, runtime source and developer-guide coverage text are unchanged.

Independently inspected receipt `.agent-ready/verification/1e4657a989e2466f962b427235fe1293.json`: complete `true`, exit status `0`, duration `266007.8606249881` ms. The log SHA-256 matches its recorded digest `401b7ec04086210d5e778f40cdc5b160c850306b96904ac8a4e99fef4390ed41`; both changed product-file hashes match the receipt. Its log reports 10,427 passed, 13 skipped and 20 xfailed in 236.68 seconds. This supersedes the outstanding-full-check note above.

The prior unsuccessful full checkpoint is retained as failed evidence; the added fragment fixes its reported towncrier requirement without changing product behavior. No test rerun was performed during this bounded confirmation. This receipt is the ordinary full checkpoint: no real-schema qualification tier is selected or claimed qualified, and synthetic coverage is not a substitute for those tiers.
