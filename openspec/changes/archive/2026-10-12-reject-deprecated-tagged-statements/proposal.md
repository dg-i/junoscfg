## Why
Deprecated `SetConverter.to_set()` silently moves a terminal statement's metadata onto its value or child; the held device route example loses entry inactivity when its output is read back.
## What Changes
**BREAKING:** refuse terminal lexer text containing ASCII space tagged inactive/protect/delete through this schema-free writer, with a path-free error naming the supported schema-aware replacement.
Retain block-opening tags, one-token terminal tags, replace-only stripping, untagged legacy output, `statements()` and supported conversion.
Preserve four legacy fixtures' positive set lines and exact correct parent targets through supported conversion, adding explicit deprecated refusal after independent challenge/root admission.
Search `to_set`, `SetConverter`, and structured validator callers found only deprecated `StructuredValidator._validate` as the production caller; its exception boundary returns invalid. No override, fallback, environment read, dependency or public signature is added.
## Capabilities
### New Capabilities
None, because both behaviors already have owning capabilities.
### Modified Capabilities
- `conversion/structured-input`: bounded explicit refusal replaces the deprecated terminal last-node rendering guarantee.
- `validation/structured-validation`: deprecated schema-free validator reports refusal; public validation remains the migration.
## Non-goals
No schema changes, higher-layer imports, statement-name tables, new parser or broader converter repair.
No claim that every Junos operational verb or single-token tag is invalid; no device-loaded side effects inferred.
No removal of deprecated doors or change to their removal schedule.
## Impact
Decision 2026-10-09-scope-compatibility-to-production-consumer defines secondary doors; root nevertheless explicitly declares this bounded consumer migration.
Kernel runtime, display contract and bounded display tests; reviewed main-spec application belongs to Finalizer.
Consumer compatibility break, with migration to existing `convert_config` and `validate_structured`; beta minor bump belongs to root at merge.
Evidence: held synthetic device `examples/junoscfg-oracle.conf` route/autonomous-system and matching `.set`; existing strict-xfail metadata tests; SC1 freezes the original guarantee and assertions.
Approval: root admission of 2026-10-12 approves intent direction; SC1 and precise assertion/contract correction await independent Test/Challenge and root ruling.
The four old tests are valid retired compatibility assertions; independent equal-IR evidence and accepted quoted-foo unquoting qualify the correction.
