## Why

`tests/conftest.py::find_xsd_source` took whichever dump sorted newest under
`private_test_data/schemas/`, so step 2 of the pre-commit checklist, "rerun
with `--regen-schema`", would have replaced the shipped 25.2R2 artifacts with
whatever a developer had synced last, as a side effect of a file name. And
with no dump at all it warned and ran the suite against the committed set, so
the flag reported success having regenerated nothing. Step 5 of the owner's
plan of 2026-10-08, with the decision to update the docs and help text.

## What Changes

- The release is an explicit choice. `--regen-schema` rebuilds from the one
  dump whose release train matches the bundled metadata's, `25.2` today,
  read from each dump's own header where it lies, renaming nothing;
  `JUNOSCFG_XSD_SOURCE` names another, which is how the release moves on
  purpose.
- No dump of that train, two of them, or an override that is empty, not a
  file or without a release in its header stops the run before collection,
  with every dump and its release named and exit code 7, pytest's own codes
  being 0 to 5. A run that selects no test can no longer skip the check.
- The flag's help text, `AGENTS.md` step 2 within its cap, the tier table
  and usage list in the developer guide, and `private_test_data/README.md`
  say so.

## Capabilities

### New Capabilities

None; the test harness, with no runtime behaviour.

### Modified Capabilities

None at spec level; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Recording the source dump's full release in the metadata. The namespace
  release the builder records already names the train, and the train is
  what the dump's header shares with it.
- The `--schema` tier, which runs against every dump present and should.
- The CLI's `--artifacts` option, which selects a set to use, not to build.

## Impact

Sixteen tests, hermetic over temporary dumps plus one real run that stops
before collection; the old rule would have rebuilt from the 22.4R0 dump that
sorts last, the new one resolves to the 25.2R2 QFX5120 dump. A full run with
the flag rebuilt byte-identical artifacts but the metadata's timestamp. Full
suite 1,562 passed. Patch bump to 0.10.1.
