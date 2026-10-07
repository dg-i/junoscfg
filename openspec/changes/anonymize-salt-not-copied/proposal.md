## Why

`_replace_hashed()` copies the original crypt salt straight into the output:
`$6$<original salt>$<safe body>`. The body is one-way and safe. The salt is
per-password entropy lifted from the customer's configuration, and re-emitting
it leaves a correlation handle — anyone holding the original hash string, from
an old backup or a prior unanonymized share, can match it to the exact account.

Found by the fresh-session review of the Python-floor change, which flagged it
as pre-existing and never written down.

The same review raised a second concern, that an empty default salt makes the
mapping globally reproducible. **That one does not hold**: `anonymize()`
already generates a random 32-character salt when none is supplied
(`anonymize/__init__.py:47`), verified — three runs with no salt give three
distinct outputs. The reviewer reached the empty-salt path by constructing a
`PasswordRule` directly, bypassing the entry point. Requiring an explicit salt
would therefore break callers to fix nothing, and is not done here.

While in this code: `$5$rounds=N$` was parsed as though `rounds=N` were the
salt, so the real salt was dropped and `rounds=5000` appeared in its place.

## What Changes

- Derive the replacement salt from the same HMAC, in the crypt64 alphabet and
  at the original's length, so the output still looks like a crypt hash and
  stays deterministic.
- Parse `$5$rounds=N$` and `$6$rounds=N$` correctly: the rounds field is a
  parameter and survives; the salt after it is replaced.
- Update the four tests that asserted the salt was preserved. They were
  asserting the leak.

## Capabilities

### New Capabilities

None; this removes an information leak from an existing capability.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Requiring an explicit config salt. See above: the hole is already closed.
- Replacing the bcrypt, `$sha1$` or `$3$` salts. They have the same shape and
  the same argument applies, but each needs its own format handling and its own
  test; this change covers the three crypt formats that share one code path.

## Impact

`src/junoscfg/anonymize/rules/password.py` (red zone) and four test files.
Anonymizer output changes for every `$1$`/`$5$`/`$6$` password: the salt differs.
A previously anonymized configuration cannot be re-anonymized to the same text,
which is the point. The revert mapping is unaffected — it maps original to
replacement and is written at anonymization time.
