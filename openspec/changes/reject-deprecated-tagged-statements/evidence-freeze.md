## Resolved instructions

instruction-integrity.md C1-C3 and root admission govern this preparation-only snapshot. Intent is approved; precise SC1 correction, existing assertions and contract require independent challenge/root ruling before implementation. No material intent question is open; phase-2 implementation authorization remains conditional on that ruling.

## Requirements

Draft full deltas: conversion/structured-input deprecated writer requirement; validation/structured-validation deprecated doors requirement. Full migration treatment applies because of the declared consumer break. Main specs and source are frozen unchanged in baseline/.

## Evidence

- Immutable base 5187ac92734dce8c9ebd4e8404a98f76871fd399; preflight 79c475d, intent 2dbc2cb.
- Held synthetic device examples/junoscfg-oracle.conf lines 806/814 and .set lines 269/272-273; strict-xfail exact route/autonomous-system fixtures in frozen tests.
- Four passing legacy fixtures freeze existing accepted schema-free behavior, even though their metadata target contradicts supported conversion. SC1 lists semantic preservation explicitly.
- Source _Lexer._end_statement joins pending tokens with one space; bracket expansion appends one item with a space; _strip_prefixes removes normalized leading tags. A hypothetical quoted-only terminal `inactive: "a b";` is also conservatively refused, although it is one lexical token. A quoted single token may itself contain spaces, but valid terminal statements have an unquoted statement keyword before a value; the bounded refusal treats whitespace in stripped terminal text conservatively. No extra tokenizer is needed.
- Exact direct caller StructuredValidator._validate catches exceptions and returns invalid; JunosValidator.validate_structured delegates to it. Existing public validate_structured uses the schema-aware reader.
- Intent-only OpenSpec validate reported missing deltas; phase 2 supplies them. fields reported a bare None in new capabilities; corrected with the explicit reason. These are preparation diagnostics, not passing evidence.

## Non-goals

Proposal non-goals apply: no schema, higher-layer import, parser, tag table, broader conversion migration, device-loading claim, removal or schedule change.

## Acceptance criteria

- New regression file test_terminal_tag_refusal.py drives all three emitted tags, route and four legacy fixtures, normalized whitespace/quoted values, path-free errors and supported migration.
- Existing block tags, one-token flags, replace-only, untagged output and statements() retain exact behavior.
- Deprecated validator returns invalid and does not invoke the supplied set validator; public replacement is exercised with the held route/leaf fixtures by supported conversion.
- Independent challenge must assess precise compatibility correction and every frozen legacy assertion before those files change.

## Performance expectations

No throughput promise: one bounded examination of already lexed terminal text, no additional lexer/schema load, no I/O or dependency.

## Outstanding decisions

SC1 precise compatibility/test/contract correction is pending independent Test/Challenge and root ruling. This freeze authorizes preparation/new regression only, not source implementation or phase-2 closure for implementation.

## Execution and checkpoint

- Assurance preference: economy.
- Risk floor: high, declared consumer break and conversion/validation domains.
- Roles required: Builder, independent Test/Challenge, fresh isolated Reviewer, bounded Finalizer.
- Resume point: phase 4 new regression then STOP-T; phase 2 closes for implementation only after SC1 ruling.

## Delta log

- Freeze established from immutable base and baseline copies; source, contracts and existing assertions remain unchanged.
