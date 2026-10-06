## Findings

From a fresh session with no knowledge of the change, reviewed as a RED-tier
`anonymize` change. It reproduced the premise independently — macOS returning
13-character DES hashes for all three prefixes, and `git show v0.5.8` confirming
the floor predated onboarding — and returned thirteen findings.

1. **The replacement was not a structurally valid crypt hash.** The body was
   always 64 hex characters, where md5crypt needs 22, sha256crypt 43 and
   sha512crypt 86. Every *other* format in `password.py` (`$8$`, `$sha1$`,
   `$2*$`, `$3$`) already slices to the original body length; only this branch
   did not. On glibc with Python ≤3.12 the released 0.5.x line produced
   correctly sized hashes, so the change as first written was a regression for
   those users. **Fixed**: `_make_crypt_hash` takes the original body length,
   and `_extend_hex` folds the digest forward for bodies longer than 64. A new
   test pins 22/43/86.
2. **The original crypt salt is copied verbatim into the output**, and
   `AnonymizeConfig.salt` defaults to empty, making the mapping a public
   function. Pre-existing and not introduced here, but this change makes the
   path universal in the red zone. **Open**: carried forward for a decision
   record, not silently.
3. **The impact claim was factually wrong.** It said no caller on 3.10–3.12
   could observe the old behaviour because 0.6.0 refuses to install there —
   true and irrelevant, since v0.5.0–v0.5.11 shipped `>=3.10` *with* the crypt
   branch and the collection pins `>=0.5.8`. **Fixed** in `proposal.md` and
   `checklist.md`.
4. **`ARCHITECTURE.md` section 2 still declared "Python 3.13 or later"**,
   contradicting `pyproject.toml` in a required section. **Fixed.**
5. **A new mypy error** in the red-zone test file, from `_make_rule() -> object`.
   **Fixed**; the helper is typed.
6. **The AST guard passed vacuously** from any other working directory: a
   CWD-relative glob that found zero files and asserted only on an empty list.
   For the sole guard on a red-zone invariant, failing open is backwards.
   **Fixed**: the path is resolved from `__file__` and the test asserts it
   scanned more than 50 files.
7. **Nothing guards the restored floor.** CI is a single `ubuntu-latest` job
   with no Python matrix, so 3.10–3.12 are never exercised again. **Open** —
   this is the drift that produced the defect in the first place.
8. The new tests bite, but on 3.14 only the AST test does; the other passes
   either way because `crypt` is already gone there.
9. **Recorded counts were the pre-change number** (1394 rather than 1397).
   **Fixed** in `tasks.md` and `metrics.md`.
10. `hex_digest[:64]` was a no-op slice. **Fixed** by finding 1.
11. `$5$rounds=N$` treats the rounds field as the salt and drops the real one.
    Pre-existing, format-wrong, privacy-harmless. **Open.**
12. `crypt` survives transitively through `netutils.password`, so the AST
    test's name is broader than its scope. Noted in the test's docstring.
13. The branch fails `lane` and `stage griffe` because it carries two live
    changes. Belongs to the sibling commit. **Open**, see below.

## Already provided

`netutils` supplies the Juniper `$9$` constants; nothing new was needed. The
length-preserving mechanism finding 1 asks for already existed in the `$sha1$`
branch and was copied rather than invented.

## Specification challenges

No challenge. `skip_specs: true`; no requirement describes the hash body.

## Verdict

Accepted after correction. Thirteen findings: eight fixed in place, five left
open with reasons. Finding 1 is the one that mattered — the change as first
written traded a platform-dependent hash for a wrongly-sized one, and only an
independent read caught it. Re-verified afterwards on five interpreters:
**1397 passed** on each, and the anonymizer's output hashes identically on
3.10, 3.12 and 3.14.

The reviewer could not test glibc (macOS-only host), a real Junos device, or
3.11 and 3.13 directly, and said so.
