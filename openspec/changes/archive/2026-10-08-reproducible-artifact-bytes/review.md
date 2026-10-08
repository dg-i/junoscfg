# Review

Fresh agent session, read-only, against commit `4d2c884` before it was
amended and tagged `v0.7.1`. Every claim was probed in a scratch directory
against the project interpreter, not reasoned.

## Confirmed exact

Old and new writer agree byte for byte once MTIME is masked: same CRC and
ISIZE, same XFL and OS, same compression level, same text through `gzip.open`
and `read_artifact_text`, non-ASCII round-trips. An exception inside the body
leaves a valid gzip of the partial text in both forms. The handle is still an
`io.TextIOWrapper` with `.name` and `.encoding` as before, for all four
callers. No new trust-boundary behaviour on `path`. `CONTRACT.md` untouched:
`io` is stdlib and nothing lazy became eager. The test fails without the fix.

## Findings

1. **`gzip.GzipFile` already opens the file.** Three context managers where
   two suffice: `GzipFile(path, "wb", mtime=0)` owns and closes its handle,
   as `gzip.open` did. Bytes identical. **Applied** before tagging.
2. **The test could not see a lost trailer.** A writer that closed the raw
   file before flushing the wrapper passed both assertions while `gzip.open`
   raised `EOFError` on the result. **Applied**: the test reads the artifact
   back through `read_artifact_text`.
3. **The second assertion was near-vacuous.** Two writes in one second agree
   under the old writer too; only the header check is evidence. **Applied**:
   dropped in favour of the read-back.
4. **Reproducibility is name-bound and platform-bound.** FNAME is still
   stamped, so the same content under another basename differs; the text
   wrapper translates newlines, so Windows bytes differ. Both identical to
   `gzip.open(path, "wt")`, nothing regressed. **Accepted as-is**; the
   proposal now says "written to the same path".

## Already provided

`gzip.GzipFile`'s `filename` parameter (finding 1); `read_artifact_text` for
the read-back (finding 2).

## Specification challenges

None.

## Verdict

Correct and behaviour-preserving; ship. Findings 1 to 3 applied in the
amended commit, 4 recorded.

## Owner acceptance

Accepted by the owner on 2026-10-08, in one pass over the eight live reviews,
on the summary that each review's findings were resolved or recorded as
accepted-as-is. The owner did not sign off per finding.
