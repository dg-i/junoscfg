## Context

One private stdlib script already performs the mandated comparison. T4 makes that same answer reusable under tools without changing the public conversion result or device-law classifier. Runtime implementation remains parked.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| Existing private compare-template.py and public convert_config_result | Entire record/diff workflow | Untracked copy, no tooling acceptance tests | Inspected source SHA256 in freeze, 2026-10-12 | Promote directly; first reuse rung holds |
| Standard library gzip/json/difflib/pathlib | Existing compression, deterministic records and unified diff | No new gap | Already used by template, 2026-10-12 | Retain current building blocks; no dependency search needed |

## Decisions

Preserve record(out, anonymize) and diff(base, head), positional script commands, current-working-tree manifest selection, exception-class-only records and sorted field evidence. No new root override, package door or CLI subcommand. Synthetic test fixtures supply six four-format compressed captures, independently computed matrix keys and fake conversion results; they never invoke actual schema conversions. The command test drives the script with runpy and public conversion monkeypatching, so the same arguments are checked without subprocesses.

The guide's comparison subsection points to the shared script and drops the private-copy step. The private source is retained read-only as historical evidence, superseded in documented usage. tools/device_differences.py remains the sole classifier of device-law differences.

## Risks

This record contains output and field messages by design and is a private evidence artifact, not an anonymization safety certificate. Comparisons explain textual changes; semantic/device accountability remains with the existing laws. Missing rendering files retain current template skip behavior; completeness tests count the supplied available inputs, including one explicit absent rendering. No cache or evidence activation is added.
