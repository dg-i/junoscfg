# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

`Error: Invalid XML: ...`, exit 2, for an undeclared prefix, an unclosed tag
and non-XML input; the same element inside its `<rpc-reply>` still converts to
`set system host-name router1`. The mutation dies.

## Findings

1. **The consistency claim was half true.** `checklist.md` says the fix makes
   XML do "what the other input paths already do". True of JSON and
   structured, false of YAML: `cli.py` converts only `NotImplementedError` and
   `ValueError`, and JSON works *by accident* because `JSONDecodeError`
   subclasses `ValueError`. `yaml.parser.ParserError` does not, so a malformed
   YAML document printed a parser traceback — the identical bug, one module
   over, in the same input package. **Fixed in v0.7.0.**
2. The proposal's Why is internally inconsistent: it says malformed XML
   "reports a usage error and exits 2" immediately before saying XML raised
   straight through. "Structured" was presumably meant.

## Resolution

Does exactly what it says. Finding 1 is the overreach — claiming parity it had
not checked — and is fixed, which makes the claim true as of v0.7.0.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.
