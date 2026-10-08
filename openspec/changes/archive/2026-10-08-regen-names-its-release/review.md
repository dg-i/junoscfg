# Review

Fresh agent session, read-only, against commit `f2d9fea` before it was
amended and tagged `v0.10.1`. The reviewer listed every dump and the release
its header declares, ran the error path for real, and probed the lookup with
temporary dumps.

## Confirmed exact

The regression is concrete: the old rule, newest by sorted name, would have
rebuilt the shipped 25.2 artifacts from `new2.xsd`, a 22.4R0 dump four
trains older; the new rule resolves to the 25.2R2 QFX5120 dump, and a dump
named by hostname is matched by its header. The error path exits with the
message and no tests run. `AGENTS.md` is at exactly 100 lines. Full suite
green.

## Findings

1. **The documented staging workflow tripped the two-dumps stop**: a
   `new.xsd` of the shipped train beside the shipped dump, the commonest
   reason to capture one, stopped the run. **Applied**: the README's staging
   paragraph states the rule and the way through; the stop stands, since two
   dumps of one train, QFX and EX say, is a choice nobody should make for
   the developer.
2. **The lookup renamed a staged dump even when it only raised.**
   **Applied**: the lookup reads headers where the files lie and renames
   nothing; promotion stays with the `--schema` tier. Tested.
3. **Legacy dumps were reported under the wrong directory, by basename,
   and the "other dumps" were a bare count.** **Applied**: every dump is
   named with its path and release.
4. **A dump with no release in its header could be regenerated from, and
   the metadata it left would match nothing afterwards**, with the one
   message that named no way out. **Applied**: such an override is refused;
   the metadata message names `JUNOSCFG_XSD_SOURCE`.
5. **Exit code 4 is pytest's own usage error.** **Applied**: 7, named in the
   help text and the README.
6. **A run that selected no test skipped the check and reported success.**
   **Applied**: the check and the rebuild moved to `pytest_sessionstart`,
   before collection; tested with a real `--collect-only` run.
7. **A set-but-empty override fell back silently.** **Applied**: an error.
8. **Service and EVO trains** such as `25.2X75-D10` did not match.
   **Applied**: the train followed by any non-digit. Tested.
9. **A directory named like a dump escaped the error contract.**
   **Applied**: files only. Tested.
10. **Three doc sentences still described the forgiving behaviour.**
    **Applied**.
11. **No test touched the fixture path, the environment, or the exit code.**
    **Applied**: one real run in a subprocess, and the cases above.

## Already provided

`schema_data.read_version` for the header, reused; `pytest.exit` with its
own return code, rather than a `UsageError`.

## Specification challenges

None.

## Verdict

The core fix is right and the regression it removes is demonstrable; the
review's eleven findings are all applied in the amended commit, and the full
run with the flag was repeated through the new hook.

## Owner acceptance

Accepted by the owner on 2026-10-08, in one pass over the eight live reviews,
on the summary that each review's findings were resolved or recorded as
accepted-as-is. The owner did not sign off per finding.
