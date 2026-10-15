# Review

Lightweight fresh review (maintenance lane) of change `qfx-null-probes`.

- Base: 2d4904be9f01adca8e2ab472a4f457ef5ce0c403
- Head: a1b75baa35c1c8ff90d3477fba71f09f214c62c6

Verdict: approve with corrections

## What was checked

- Criterion 1: the committed `tests/data/device/synthetic/sources/json-null-probes.json.gz`
  decompresses to bytes identical to `private_test_data/json-null-probes.json` (`cmp`); its
  gzip header is `1f8b 08 00 00000000 02 ff` (no file name, mtime 0). Re-running the head
  importer with `PRIVATE=private_test_data` and `TARGET` a scratch copy of the base's
  `tests/data/device` printed `awaiting capture, skipped` and `6 captures from 2 devices`, rc 0;
  `diff -r` against the base shows only the new source, and against the head tree only the
  README, which the importer does not write. Every existing rendering, source and the
  manifest re-import byte-identical.
- Criterion 2: against a scratch PRIVATE (real folders symlinked, a fresh
  `qfx-null-probe/`): awaiting keeps the source, rc 0; one rendering undated and four
  renderings undated stop with `set its date in CAPTURED`, rc 1; dated with one rendering
  stops `missing ['conf', 'json', 'xml']`, rc 1; dated with four imports them and the manifest
  entry carries that date, rc 0. `SYNTHETIC` is name -> suffix and sources keep their suffix;
  the `SELECTION` entry, the `CAPTURED` map with its `None` and the docstring sentence are as
  asked. The capture tests ignore `sources/` (`tests/corpus/test_device_renderings.py:209`),
  so the new `.json.gz` source affects no test.
- Criteria 3 and 4 are present; finding 1 corrects one count.
- `ruff check` and `ruff format --check` on the importer pass; no Python line exceeds 100.
  The only README lines over 100 are the existing table rows. The changelog fragment is one
  line, like the others in `changelog.d/`.
- The product runtime is untouched: the diff has no `src/` change. Nothing in the diff is
  unnecessary: `.agent-ready/activation.json` is the lane's admission record.

## Findings

1. `tests/data/device/README.md:31-33`, low (prose accuracy). The text reads "15 statements
   the device prints as `{}`, written as junoscfg's `[null]`, and an inactive leaf ...", which
   says 15 `[null]` values plus one more statement. The source holds 14 `[null]` values. The
   inactive `l3vpn` is the 15th of the statements the QFX prints as `{}`: the QFX
   `junoscfg-oracle.json.gz` has exactly 15 `{}` leaves, `l3vpn` among them, and
   `probe.set` has 15 `set` lines plus one `deactivate` line. Proposed: "15 statements the
   device prints as `{}`: 14 written as junoscfg's `[null]`, and the inactive leaf `l3vpn`
   written `{"@": {"inactive": true}}` where the device prints `"l3vpn": {}` beside
   `"@l3vpn"`." The same miscount appears in
   `openspec/changes/qfx-null-probes/instruction-integrity.md:21-22` ("15 statements ... plus
   the inactive `l3vpn`"); correct it there too. The "all 16 lines" on line 23 is right.
2. `openspec/changes/qfx-null-probes/tasks.md:19-20`, low (process). Here the canonical full
   check (3.3) comes after the fresh review (3.2). `short-lanes.md` (fix route step 4, which
   maintenance follows) runs the full check before the reviewer is dispatched. This does not
   block: run the full check on the head that is merged, after the corrections above, and
   record that command and HEAD in 3.3.

Nit, no change required: when only some renderings exist and no date is set, the importer's
message is "captured; set its date in CAPTURED". Once the date is set, the next run reports
the missing formats. The criterion asks for exactly this.

## Specification challenges

None.

## Builder disposition

1. Accepted: README and instruction-integrity now read 15 statements, 14 as `[null]`
   and the inactive `l3vpn`.
2. Accepted as ordering: the lane route (SKILL.md, step 5) runs the canonical full
   check after the review is recorded; it runs on the corrected head and 3.3 records it.
