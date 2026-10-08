## 1. Tests

- [x] 1.1 The gzip header's MTIME field is zero and the artifact reads back.
  Seen to fail against the merge-base writer, which stamps the current time;
  the read-back is what the review asked for, so a lost trailer is visible.

## 2. Implementation

- [x] 2.1 `open_artifact_write` opens `gzip.GzipFile(path, "wb", mtime=0)`
  through a text wrapper; the decompressed text is unchanged.
- [x] 2.2 Version 0.7.1 in `pyproject.toml`, `src/junoscfg/__init__.py`,
  `tests/test_cli.py` and `uv.lock`.

## 3. Verification

- [x] 3.1 The full suite passes: 1518 passed, 71 skipped, 1 xfailed.
- [x] 3.2 Every bundled artifact decompresses to the same text as at `v0.7.0`:
  nothing shipped is rewritten here.
