## 1. Verification

- [x] 1.1 Acceptance tests: `tests/test_meta_tags.py` (reader, writer, round trips, `family` refusal), three `TestXmlAndStructuredInputAgreeOnTheIr` methods (one-line route, `family inet`, protected route), `tests/test_artifact_builder.py::TestHomogeneousFlag`; 25 fail before the change, each on its defect; the passing ones are guards (set input's last-node rule, set output repeating the `family` tag, four round trips the block writer already keeps).
- [x] 1.2 Independent Test/Challenge on these tests, with change A's at the end (owner answer 3): `test-challenge.md`; findings and interim actions in `review.md`.

## 2. Change

- [x] 2.1 Schema: `h` for `homogeneous` in `artifact_builder._BOOL_FLAG_KEYS`; one `--regen-schema`.
- [x] 2.2 Curly reader: `SetConverter` hands out statements with per-level tags; `set_input` applies them in `_merge_tokens`; `structured_input` uses it; `replace` pseudo command and `emit_replace` removed.
- [x] 2.3 Curly writer: a tag leads its line, no join past a tagged node, `homogeneous` replaces `COMPOUND_KEYWORDS`, a tag on an unkeyed `homogeneous` container dropped with a note.
- [x] 2.4 Validation: `UNPLACED` for a tag on an unkeyed `homogeneous` container; XML reads `protect`.
- [x] 2.5 `display/CONTRACT.md` (the `to_set()` limit), developer guide mentions of `emit_replace`, patch bump to 0.15.2, changelog fragment.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: fresh Reviewer (`review.md`), two re-reviews; verdict mergeable at 6f2f058.

Pre-review checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full --base change/xml-inactive-leaf` at 6f2f058: every check passed, 2,009 passed / 45 skipped / 1 xfailed. Without `--base`, a branch whose diff touches two live change folders (this one stacks on change A) has its diff-reading gates read the last commit alone (`agent_ready_checks.stage.change_base`); the explicit base reads the whole of this change. The rebase onto change A's evidence-only commits that followed leaves this change's runtime content unchanged.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
