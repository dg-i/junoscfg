## Findings

A fresh session reviewed this as a RED-tier change. It confirmed the fix itself
is correct and the tests bite — it reintroduced the leak in a scratch copy and
got 8 failures — but overturned the reasoning around it. Both high findings
were verified here before acting.

1. **The declined change was declined on a wrong premise.** The first draft
   claimed `anonymize()` always auto-generates a salt, so requiring one would
   "break callers to fix nothing". That tested one of three routes to
   `config.salt`. `load_config_file` did `str(data["salt"])`, so a config file
   with `salt:` gave the literal string `"None"` and `salt: ""` gave `""`;
   neither is `None`, so auto-generation never fired. Reproduced through the
   shipped CLI: both give byte-identical output across runs, making the mapping
   reproducible by anyone. **Fixed**: a blank, whitespace or null salt now
   falls through to auto-generation, with five tests covering the forms.
2. **The fix covered the weakest member of the class and left the strongest.**
   bcrypt carries a 22-character salt — a stronger handle than the 8-character
   `$6$` salt being fixed — and `$8$` carries a salt, an IV and a GCM
   authentication tag, a MAC over the real plaintext. `$8$` was not even in the
   declared non-goals. **Fixed**: every format that carried a salt now replaces
   it, and `$8$` replaces its IV and tag too, keeping only the algorithm and
   iteration parameters.
3. **`anonymize()` mutates the caller's config**, writing the generated salt
   back, so a reused config silently keeps one salt across calls. Pre-existing
   and undocumented. **Open**: carried forward for the contract.
4. **The replacement salt was recomputable from the body** — both were prefixes
   of one stream. No data leaked, but it fingerprinted the output. **Fixed**:
   the streams are domain-separated and a test pins it.
5. `_pseudo_field` is otherwise sound: the suspected modulo bias is not there
   (256 % 64 == 0, measured uniform over 320,000 characters), no character
   escapes crypt64, length 0 is handled, and determinism holds across
   processes.
6. The patch version is right, but for a reason the checklist did not give:
   `CONTRACT.md`'s determinism invariant is worded per-run, and cross-version
   stability was never promised. **Fixed** in the checklist.

## Already provided

`anonymize()`'s existing auto-generation does the work once a blank salt
reaches it as `None`; no new generation logic was needed.

## Specification challenges

No challenge. `skip_specs: true`.

## Verdict

Accepted after correction. Six findings, five fixed and one carried forward.
Two of them reversed decisions recorded in the first draft of this change — the
dismissal of the empty-salt concern, and the scoping that called `$8$` out of
scope without naming it. The reviewer could not confirm the real-world `$8$`
field layout against a device, or the prevalence of each format in practice.
