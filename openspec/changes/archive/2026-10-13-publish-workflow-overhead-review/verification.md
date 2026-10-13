# Publication evidence

Report arithmetic matches the preserved baseline interval-union data: 1729.287095 minus 948.074804 equals 781.212291 seconds; half 390.6061455. Four suggestions occur in each requested section. Local links and anchors resolve, and the generated HTML contains both sections and the timing table.

MkDocs strict build failed on 44 warnings; comparison against an extracted immutable 901ddc0 baseline produced the identical 44 warning lines, with zero new warnings. Normal rendering passed. These pre-existing warnings are not repaired by a report publication. Logs and document-qa.json are in private_test_data/workflow-overhead-2026-10-13/publication in the primary checkout. Raw private evidence is described as local-only rather than linked as if shipped.

No runtime or verification-policy change. The pending verification cadence invitation is retained (60 first-parent commits at entry). Independent maintenance review and canonical full remain pending. Required inventory includes concurrent schema-qualification-scope as parked because its observed 0d232a2 metadata had no readiness declaration; its files are untouched.

Owner-directed cancellation: the canonical full run started at 2026-10-13T21:48:12.848900+00:00 (native owner record) and was terminated on the owner's explicit instruction. Its result is incomplete, not passing. The retained native lock belonged to terminated PID 40042 in this worktree; after checking that process was gone, only that abandoned lock was removed. Document QA and the independent review remain the publication evidence. No new runtime implementation is part of the report.

Separate metrics are omitted under the maintenance short-lane rule: this is publication of an existing report, not a new performance experiment. The original measurement and its limitations remain the report's sources. No after-sample or speedup is claimed.

Final closure at 2026-10-13T21:56:01.553342+00:00: independent review is approved in review.md. The earlier release commit selected the application suite because version files changed; that commit and its test process were terminated on owner instruction, so the hook has no passing result. Retry the commit with SKIP=affected-tests, retaining other hooks. Version strings in pyproject.toml, src/junoscfg/__init__.py and uv.lock are all 0.28.13 by direct diff inspection. No further tests are run; the owner explicitly authorizes the patch bump, tag and local integration.
