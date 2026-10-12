## Resolved instructions

instruction-integrity.md C1-C3 and root admission govern this preparation-only snapshot. Intent and precise SC1 correction are approved after independent Test/Challenge/root ruling; test-challenge.md is the verbatim report and sc1-ruling.json the exact accepted scope. Phase-2 correction is closed. Implementation waits for root-preserved rebase and phase-5 admission after the preceding release.

## Requirements

Draft full deltas: conversion/structured-input deprecated writer requirement; validation/structured-validation deprecated doors requirement. Full migration treatment applies because of the declared consumer break. Main specs and source are frozen unchanged in baseline/.

## Evidence

- Immutable base 5187ac92734dce8c9ebd4e8404a98f76871fd399; preflight 79c475d, intent 2dbc2cb.
- Held synthetic device examples/junoscfg-oracle.conf lines 806/814 and .set lines 269/272-273; strict-xfail exact route/autonomous-system fixtures in frozen tests.
- Four passing legacy fixtures freeze valid accepted schema-free compatibility behavior. Independent execution found equal IR for those legacy and supported outputs; the conservative admitted boundary intentionally refuses these safe shapes too. SC1 lists semantic preservation and the accepted quoted-foo canonical spelling migration explicitly.
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

No unresolved SC1 compatibility decision: root accepts the independently assessed four-fixture correction and precise ASCII-space guard. Scheduling gate remains: no runtime, existing-test, contract or main-spec edits until root-preserved rebase after the preceding repair release and explicit phase-5 admission.

## Execution and checkpoint

- Assurance preference: economy.
- Risk floor: high, declared consumer break and conversion/validation domains.
- Roles required: Builder, independent Test/Challenge, fresh isolated Reviewer, bounded Finalizer.
- Resume point: records-only handoff after accepted STOP-T; next incomplete phase is 5 after root-preserved rebase and admission.

## Delta log

- Freeze established from immutable base and baseline copies; source, contracts and existing assertions remain unchanged.

- Phase-4 preparation: new file executed on unchanged runtime, 11 meaningful failures and 10 preservation controls pass; no criterion changed. Lexical quote-only edge documented in preparation-red.md. STOP-T, SC1 pending.

- 2026-10-12 accepted Test/Challenge/root delta: verbatim report and exact ruling incorporated. The four old assertions are valid prior compatibility, not independently demonstrated metadata loss; quoted foo canonical unquoting preserves value/IR. Precision added to guard wording (ASCII space), source message/docstring truthfulness and standing deprecation timeline. These qualifications invalidate misleading Builder descriptions of four defective assertions; no product or baseline bytes changed. Reruns required after rebase: focused implementation evidence and risk-required fresh review, then admitted canonical verification. No preparation tests repeated for this records-only delta.

- 2026-10-12 phase-5 admission/rebase delta: root admits implementation on stable release base dd626c13bd0bdd3877d848072b31ba7b62df6699 (v0.27.0). Preservation ref refs/codex-preserved/reject-deprecated-tagged-statements and full private pre-rebase.bundle retain head 45a92b3. Rebase preserves all owned record/test bytes and five frozen originals byte-for-byte. Incoming runtime is only preceding scalar metadata-selector refusal in convert/input/set_input.py plus package version bookkeeping. SC1 Test/Challenge equality of legacy and supported IR remains historical evidence bound to 5187ac9; preceding scalar repair now refuses some old schema-free scalar-value metadata on SET reread. Migration tests compare supported modern roundtrip to direct supported STRUCTURED IR, never require unsafe old SET output to be accepted. No SC1 criterion is widened.
- Verification owner instruction overrides canonical full adapter for this change: native readiness, one offline ordinary `uv run --locked --group dev pytest tests/ -q --cov --cov-report=term:skip-covered` with unchanged 91.47 floor, then canonical four-extra fast `agent-ready check --set fast --base dd626c13bd0bdd3877d848072b31ba7b62df6699` sequentially on the same runtime HEAD. No schema/regen flags or schema execution. Ignored fixtures are provisioned by root; preserve directory symlink and original physical schema inputs. A changelog fragment is declared before creation. Standing deprecated-door retirement is deferred policy outside this bounded safety repair; retain warning/replacement and next-minor wording, without automatically retiring the doors after release version increments.
