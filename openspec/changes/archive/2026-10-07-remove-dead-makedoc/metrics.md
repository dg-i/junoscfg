| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 356, "binary_files": 0, "files": 20, "removed": 277} |
| dependency count | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | none; the diff matches the proposal's Impact list exactly |
| requirement-to-test reconcile result | pass; no requirements exist (skip_specs) |
| pre-commit wall-clock, total and per hook | 1.51s total, all five hooks, measured on this machine |
| direct declared runtime dependencies | {"base": 6, "delta": 0, "head": 6} |
| total root-lock packages | {"base": 58, "delta": 0, "head": 58} |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |

Machine evidence and per-field provenance: [metrics.json](metrics.json).

## Notes on provenance

The `lines added and removed` figure covers the whole commit, which carries
onboarding phase 7's handover alongside the change. The removal itself is
`+24 / -95` across four files: `src/junoscfg/cli.py` (-51),
`docs/guide/cli.md` (-26), `tests/test_characterization.py` (+22/-15),
`tests/test_cli.py` (+2/-3).

Every remaining `UNMEASURED` field needs a session log this workflow does not
yet capture: per-phase tokens, per-phase files read by artefact type, human
minutes, and the runtime figures. They stay sentinels rather than estimates,
as phase 7 requires. Wall-clock from intent to merge is likewise unrecorded:
the change was proposed and implemented inside one onboarding session, so the
number would measure the session, not the change.

This is the first record, so it is descriptive and not an efficiency baseline.
Phase 7 of the onboarding skill points at a paired-task protocol in
`docs/experiments/minimum-comparative-pilot.md`; that file does not exist in
this repository or in the template, so the protocol is unavailable. No
comparable old-workflow observation exists here either, which means any
efficiency claim would have to come from prospective pairs collected later.
