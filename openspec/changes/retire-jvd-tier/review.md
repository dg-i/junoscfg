# Review

No fresh isolated Reviewer and no Test/Challenge role ran: the assurance policy does not require
them. Standing preference `economy` (`pyproject.toml#tool.template.assurance`, record
`docs/how-to/run-a-batch-of-changes.md#assurance`, key `default`); risk floor normal (freeze,
Execution and checkpoint): yellow zone `schema`, no product code, no security or trust-boundary
work, no migration, no declared break, no named public surface (`--jvd` was a pytest option of
the test suite, neither `consumer` nor `cli`), one domain. Omission approved under the owner's
unattended-run instruction of 2026-10-11. The notes below are the Builder's own and are not an
independent review.

## Builder's checks against the phase-6 prompts

- Trust-boundary input: none; no runtime code changes.
- Incompatible-but-valid input: none; the default suite never ran the removed tests (8 skipped
  without `--jvd`), and no product input path changes.
- Shared blind spot: the removal is proved by observations independent of the tests that remain:
  collection 7,621 to 7,613, `pytest --jvd` refused (exit 4), no `jvd` marker, `git grep` hits
  limited to device evidence and history.
- Second answer: none added; the device-evidence checks named by decision
  `2026-10-11-retire-jvd-from-per-change-verification` are the one remaining corpus answer.
- Stated figures: 7,621 and 7,613 rerun with `pytest --collect-only -q` on base 284715b and head;
  coverage 92.95 % against the floor 91.47 (`coverage report --format=total` after the full check).
- Left alone and noted: `tools/import_device_captures.py` still reads unmodified JVD sources from
  a manual clone at `private_test_data/jvd/` when refreshing the committed device evidence; it is
  device-evidence tooling (non-goal), and without `jvd_data.py` that clone is made by hand.

## Specification challenges

None.
