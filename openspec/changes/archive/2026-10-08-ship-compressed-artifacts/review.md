# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

Artifacts 36,200,722 B to 2,210,567 B; the two JSON schemas 19.8 MiB to 1.0
MiB, 5.02%; `du src/junoscfg` 5.2 MB as claimed, with the wheel at 2.26 MB, so
the claim is conservative. Every bundled artifact is gzipped. A directory of
*plain* artifacts still works, byte-identically, and costs nothing measurable.
Both claimed mutations die. Critically: **no artifact read or write anywhere
in `src/` bypasses the kernel helpers** — every remaining direct open is a
user file.

## Findings

1. **There was an eighth read site, in `tests/`.** The record says seven read
   sites and six write sites go through the helpers.
   `tests/test_jvd_corpus.py` built `data/junos-set.lark` by hand, so this
   commit turned the `--jvd` tier red — invisibly, because the tier is opt-in
   and nobody re-ran it. It was the only test covering two of
   `field-validator-unions`' fixes. **Fixed in v0.7.0.**
2. **Three error messages now printed `None`.** `find_artifact` returns
   `None`, and the raise sites still formatted the variable:
   `XSD not found: None`, `Lark grammar not found: None` twice. Pre-change the
   message named the path searched. Mentioned in no record.
   **Fixed in v0.7.0** — they name the directory now.
3. **`uv build` shipped `private_test_data/` in the sdist.** Pre-existing, not
   introduced here, but it sits directly under the claim of the change whose
   subject is package size, and that change never built a package. Git ignores
   the directory through a nested `.gitignore` hatchling does not read:
   **98 MB sdist, 2,627 files, real device XSD dumps among them**. CI was
   never at risk (fresh checkout, untracked data); a local `uv build &&
   uv publish` was. **Fixed in v0.7.0** — 2.3 MB, zero such files.
4. A dead duplicate import of `Path` in `set_validator.py`; ruff does not
   catch it. Site counts in the record do not reconcile (I count ~11 read and
   4 write sites, and 9 `load_schema_tree` calls against "ten").
5. `ARCHITECTURE.md` §8's measured kernel figures are now wrong:
   `constants.py` was exactly 194 lines when that sentence was written and is
   306 now, having acquired artifact resolution *and* a compression layer.
   Neither record touches it. Still open, and v0.7.0 added to it again.
6. `codemap.md` contains zero mentions of `junoscfg.display` or of
   `find_artifact`/`read_artifact_text`/`open_artifact_write` — the entire
   content of the change.

## Resolution

The strongest of the kernel three: every number accurate to the byte or
conservative, and the "no site bypasses the helpers" claim survived a grep of
every open in `src/`. The defects were at the edges — a missed site in tests
that went red unnoticed (1), messages that lost their path (2) — plus a
packaging hazard this change's framing invited scrutiny of and found (3). All
three fixed. 4, 5 and 6 recorded.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.

## Measurements superseded

Any real-device rejection figure above was taken against the bundled 24.4R0
artifacts, found defective on 2026-10-08 and replaced in v0.8.0. The numbers
that stand are in `ship-25-2r2-artifacts`; see
`docs/decisions/2026-10-08-superseded-device-measurements.md`.
