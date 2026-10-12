# Current-base implementation evidence

- Stable base: dd626c13bd0bdd3877d848072b31ba7b62df6699 (v0.27.0).
- Code commit: 9dc98a38435b7e265df3ee2b8f4034120af3a672.
- Immutable checked HEAD: 7c1b5a3f31d4279f09d3cb4ab31914f102b2031a. Later handoff edits are change records only.
- Original SC1 independent report remains verbatim, SHA256 5f2c855f8535ba4b01935f4b9e720a4a5f6becc604fd150439e7b7bbfc9591c9; historical base 5187ac9. Its four-fixture legacy-IR equality is not asserted on the rebased runtime.

## Behavior and bounded compatibility

Only deprecated to_set checks already stripped terminal lexer text for ASCII space and emitted inactive/protect/delete tags, before any rendering. It raises a fixed value-free ValueError naming supported conversion. The conservative predicate includes quoted-only ASCII-space text and can reject safe shapes; this is the accepted compatibility migration. Block tags, flags without ASCII space, replace-only, untagged output and statements() stay unchanged. Docstring/warning and contract state this precisely. No schema, higher-layer import, name/signature change or new parser.

Four complete original fixtures retain source strings; modern supported SET output rereads to the direct supported STRUCTURED IR, with exact parent metadata and all original positive content meaning. Root explicitly accepted canonical unquoting of foo with equal value/IR; root bar and delete-host-name positive coverage are strengthened. Each full fixture separately asserts deprecated refusal. AST proof confirms every other original test body unchanged. Strict device-meaning xfails remain strict and unsupported under the safer refusal; their reasons now describe the actual failure.

## Executed checks

| Evidence | Actual result |
|---|---|
| Rebased new 21 nodes before implementation | 11 failed, 10 passed, exit 1; failures are missing refusal and unsafe validation fall-through |
| Focused new + existing display/delete/deprecated validation | 82 passed, 4 strict xfailed, exit 0 |
| Prospective independent controls on implemented source | All quote/comment normalization, privacy/no-partial-return, fake validator and block/flag/replace controls pass, exit 0 |
| Four complete fixture/source-body proof | All four modern IR roundtrips, public validation and refusal pass; other original test bodies unchanged, exit 0 |
| Native readiness | Corrected archived-relative dependency declaration; exit 0, permission only |
| Owner ordinary suite, one run | 10290 passed, 37 skipped, 20 strict xfailed, exit 0; 187.25s pytest, 198.866s command |
| Coverage | 92.95%; unchanged required floor 91.47% reached |
| Four-extra fast after ignored mirror generation | Every check passed, exit 0; 59.501s |

Ordinary command: `UV_OFFLINE=1 UV_PYTHON=3.13.15 uv run --locked --group dev pytest tests/ -q --cov --cov-report=term:skip-covered`.
Fast command: `UV_OFFLINE=1 UV_PYTHON=3.13.15 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set fast --base dd626c13bd0bdd3877d848072b31ba7b62df6699`.
These owner-directed commands replace the skill's full adapter as explicitly recorded in instruction-integrity/evidence-freeze. No schema/regen flags or execution. Root-provisioned captures are available; the external schemas directory symlink and physical dumps remain preserved.

## Failure qualifications

- Contract paragraph initially exceeded its 30-line cap; complete accepted content was retained in the original paragraph budget without removing invariants/checks. No runtime/test change.
- First readiness failed on a dependency slug, since the gate requires a full relative archive directory. Corrected metadata before ordinary; preserved raw failure and successful retry.
- A misspelled evidence-wrapper path failed before fast launch, exit 2. Corrected path; no checkpoint/source change or ordinary rerun. Ancillary UTC/duration were not captured and remain UNMEASURED.
- First actual fast failed solely because ignored .claude/skills mirror did not exist. Native `agent-ready skills --regenerate` exit 0 created it; all tracked hashes unchanged. Fast retry passes on the same checked HEAD, and ordinary was not repeated.
- Normal commit hooks passed with no skip. The earlier intentionally RED preparation commit's qualified affected-tests skip does not apply to implementation or final verification.

## Evidence identity and next action

Private evidence root: /Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/phase5. Command JSON holds exact argv/cwd/HEAD, UTC start/end, monotonic duration, actual exit and raw-output SHA256; tracked-before/after manifests confirm inputs unchanged. Ordinary tracked-after equals fast-retry tracked-before exactly. The preserved ref and full pre-rebase bundle retain the original branch.

STOP-R: fresh isolated standard Reviewer required; review.md currently contains SC1 and accepted Test/Challenge, not a source-review verdict. Main spec deltas await reviewed Finalizer application. Builder performs no merge, version bump, archive, tag or publication.
