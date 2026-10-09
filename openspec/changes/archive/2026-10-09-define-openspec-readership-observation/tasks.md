## 1. Baseline evidence

- [x] 1.1 Run `git tag --sort=-version:refname | head -1`; confirm the latest
  release tag is `v0.11.1`, so the planned `v0.14.0` baseline does not yet
  exist.
- [x] 1.2 Inspect every archived `metrics.json` with `jq`; confirm all 16
  existing files report `metrics.files_read.status` as `unmeasured` and cannot
  establish a zero-reader artifact type.

## 2. Documentation

- [x] 2.1 Add the release boundaries, cohort selection, evidence limitations,
  coverage gate, aggregation commands, and deletion decision rule to the
  metrics how-to.
- [x] 2.2 Update the simplification roadmap with completed task status and the
  explicit release-long hold point.

## 3. Documentation QA

- [x] 3.1 Execute the documented tag and `jq` commands; confirm both run and
  the pre-observation state is reported as not ready.
- [x] 3.2 Verify every static path named by the protocol exists and terminology
  never equates `unmeasured` with `unread`.
- [x] 3.3 Run `uv run --locked --group docs mkdocs build --strict`; confirm the
  how-to renders under Working with Agents without warnings or broken links.
- [x] 3.4 Run the locked documentation-lane full checkpoint and record its
  checked commit and result.
  Checkpoint: `444fb77` — every documentation-lane check passed.

## 4. Review and evidence

- [x] 4.1 Complete the documentation review and write `review.md`.
- [x] 4.2 Capture `metrics.md` and `metrics.json` for the reviewed documentation
  commit.
