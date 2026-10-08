---
status: accepted
scope: [".github/workflows/ci.yml", "tool.mypy", "src/junoscfg/**/__init__.py", "src/junoscfg/anonymize/config.py", "src/junoscfg/audit/model.py"]
enforced-by: ci
review-by: 2027-04-08
---

# Enforce type checking at stable interfaces

## Context

The repository-wide strict command adopted by
`2026-10-06-adopt-mypy-strict` grew from 102 errors in 25 files to 374 errors
in 63 of 143 checked files. Because CI ignored its exit status, it detected
some real defects but prevented none and mixed public-interface risks with
dynamic configuration-tree and untyped-test noise.

## Decision

CI runs strict mypy as a blocking check over eight explicit files: the
top-level, conversion, display, validation, anonymization and audit package
doors plus the anonymization configuration and audit result models. Imports are followed
silently so dependencies remain understood without recursively reporting the
dynamic implementation backlog. Tests and CLI internals are outside this
check until they can join without ignored errors.

`py.typed` remains because exported annotations are checked and useful to
callers. The marker means the distribution supplies inline type information;
it does not claim that every internal module passes repository-wide strict
mypy. Behavioral and cross-format tests—not Python typing—protect the rule
that configuration IR leaf values remain strings.

## Consequences

New invalid calls, missing imports or symbols, incompatible returns and unsafe
optional use at the selected boundary now block CI. Dynamic Junos dictionaries
keep broad types, and widening the checked scope requires measuring that the
new command stays clean. This supersedes the permanently non-blocking
whole-repository report in `2026-10-06-adopt-mypy-strict`.
