## Why

`_replace_hashed()` copied every per-password field except the body straight
into the output. The body is one-way and safe; the salt, and for `$8$` the IV
and authentication tag, are entropy lifted from the customer's configuration.
Re-emitting them leaves a correlation handle: anyone holding the original hash
string can match it to the exact account.

The same review raised a second concern: an empty salt makes the whole mapping
reproducible by anyone. A first draft of this proposal dismissed it, having
checked only that `anonymize()` auto-generates a salt when `config.salt is
None`. That check was too narrow and the dismissal was wrong.

`load_config_file` did `cfg.salt = str(data["salt"])`, so a `--anonymize-config`
file containing `salt:` produced the literal string `"None"` and one containing
`salt: ""` produced `""`. Neither is `None`, so auto-generation never fired and
the HMAC key became publicly known. Verified through the shipped CLI: both
forms give byte-identical output across separate runs. That is a confirmation
oracle — compute `HMAC("None", candidate)` and compare.

While in this code: `$5$rounds=N$` was parsed as though `rounds=N` were the
salt, so the real salt was dropped and `rounds=5000` appeared in its place.

## What Changes

- Derive every replaced field from the HMAC, in the crypt64 alphabet and at the
  original's length, so output still looks like a hash and stays deterministic.
  Streams are domain-separated, so no field is recomputable from another.
- Replace the salt in every format that carried one: `$1$`, `$5$`, `$6$`,
  bcrypt, `$sha1$`, `$3$`, and for `$8$` the salt, the IV and the tag.
- Treat a blank or null `salt:` in a config file as unset, so `anonymize()`
  generates a random one as the documentation already promised.
- Parse `$5$rounds=N$` correctly: rounds is a parameter and survives; the salt
  after it is replaced. It was previously read as the salt.
- Update the tests that asserted a salt was preserved. They asserted the leak.

## Capabilities

### New Capabilities

None; this removes an information leak from an existing capability.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Requiring an explicit config salt. See above: the hole is already closed.
- Nothing. A first draft covered only the three crypt formats and listed
  bcrypt, `$sha1$` and `$3$` as non-goals, omitting `$8$` entirely. That was
  the wrong cut: bcrypt's salt is 22 characters, a stronger handle than the one
  being fixed, and `$8$` carries a GCM tag — a MAC over the real plaintext.

## Impact

`anonymize/rules/password.py` and `anonymize/config.py` (red zone), plus tests
and `docs/guide/cli.md`. Output changes for every hashed password: the salt
differs. The revert mapping is unaffected — it maps original to replacement and
is written at anonymization time.
