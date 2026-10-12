## Why
Root-version-only uv.lock edits currently select the full real-schema qualification. The owner requests substantially fewer unnecessary runs while retaining generator and dependency safety.

## What Changes
- Add a deterministic fingerprint of the entire parsed lockfile, excluding only the version of the unique editable-root junoscfg package.
- Replace the expensive tiers' uv.lock trigger with the fingerprint path; retain every other generator/schema trigger.
- Add a first cheap native guard tier for lock/fingerprint/helper changes, with its own truthful consistency obligation and no schema-test completion claim.
- Fail stale, missing or invalid fingerprints in ordinary tests and direct qualification adapters before expensive work.
- Document regeneration and retain explicit fresh qualification unchanged.
- Search: uv.lock, expensive-tiers, _preflight, qualify and observe_versions locate the installed wrapper selector, application declarations, ordinary test selector and schema adapter; no resource override is added.

## Capabilities
### Modified Capabilities
- `schema-pipeline/verification-evidence`: dependency-aware selection and fail-closed fingerprint consistency.

## Non-goals
No dependency subset is ignored. No shared-fixture or package-door splitting, template changes, scoped evidence cache, schema assertion changes or public runtime API changes.

## Impact
Application tooling, small-fixture tests, pyproject declarations and guides change. The root package version is nonsemantic for schema generation; all other parsed lock fields remain relevant. Native identity remains conservative and unchanged. No measured speed or historical execution count is claimed.
