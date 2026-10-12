## Specification challenges

### SC1: Preserve correctness by refusing ambiguous terminal metadata

- Artifact: baseline/structured-input-spec.md requirement "The schema-free set writer of the lexer is deprecated": "It keeps its schema-free route, which places a one-line statement's tag on its last node"; baseline/display-CONTRACT.md "deprecated SetConverter.to_set() tags a last node"; four frozen passing legacy tests listed below.
- Counterexample: held synthetic device route `inactive: route 10.98.0.0/16 reject;` is emitted as `deactivate routing-options static route 10.98.0.0/16 reject`; current reread attaches inactive to @reject and loses route entry inactivity. Device .set marks the route path. Protected autonomous-system likewise targets its value. This is executed evidence from current 69f0726, with matching unchanged owning source on base 5187ac9; no device-loaded consequence claimed.
- User impact: deprecated callers receive changed metadata without a visible error (DeprecationWarning is normally hidden). The correction deliberately rejects a bounded accepted legacy shape; deprecation alone does not waive compatibility.
- Proposed correction: standard bug, declared consumer migration to supported convert_config / validate_structured, explicit path-free ValueError for terminal multiword emitted tags only. Freeze and independently assess all original fixtures and assertions. Keep positive content and correct metadata through supported conversion; separately assert deprecated refusal. No schema knowledge/table/parser is added. Finalizer updates main specs after review.
- Decision: Accepted by root on 2026-10-12 after independently executed Test/Challenge, report SHA256 `5f2c855f8535ba4b01935f4b9e720a4a5f6becc604fd150439e7b7bbfc9591c9`. Verbatim report in test-challenge.md; exact ruling in sc1-ruling.json. Implementation remains gated on root-preserved rebase after the preceding safety release.

| Frozen existing test | Retained positive set content | Proposed supported metadata assertion |
|---|---|---|
| TestSetConverter.test_groups_transform_to_set | Every foo/bar/baz location line | deactivate groups baz snmp location |
| TestSetConverter.test_inactive_apply_groups_to_set | Every root/snmp foo/bar apply-groups line | deactivate apply-groups and deactivate snmp apply-groups |
| TestSetConverter.test_protect_leaf_emits_command | set system host-name router1 | protect system host-name |
| TestSetConverterWritesADeletePrefix.test_delete_prefix_leaf | set system host-name router1 (strengthen original content coverage) | delete system host-name |

None of these tests may simply be deleted, marked xfail or changed to retain a compatibility promise superseded by SC1 without recording the admitted break. Retain correct block-opening tags, one-token flag tags, replace-only and untagged assertions unchanged. Existing device-meaning xfails remain failures under explicit refusal; any reason update requires accurate follow-up context, never relaxed meaning.

## Accepted compatibility qualification

The four original passing tests are valid assertions of the old explicit schema-free compatibility promise. Independent execution found their legacy and supported outputs reread to equal IR on the frozen runtime; they do not establish four additional instances of metadata loss. The held route independently establishes entry metadata loss. Their correction is justified by the admitted conservative toolkit boundary, not a claim that every refused Junos shape or command is invalid.

The complete original group fixture contains `location "foo";`. Supported conversion canonically writes `location foo`; root explicitly accepts that spelling change with unchanged value and IR. Preserve all original positive content meaning, strengthen root apply-groups bar and delete-host-name content coverage, assert exact owning-node metadata targets, and separately assert deprecated refusal on each unchanged full fixture. Frozen baseline bytes remain unchanged.

The accepted predicate is emitted operational tag inactive/protect/delete on stripped terminal lexer text containing ASCII space. It conservatively includes quoted-only text containing ASCII space; quoted-only text with a tab and no ASCII space stays outside. Block tags, one-word terminal flags, replace-only, untagged output and statements() remain unchanged. No schema boundary is guessed.

Implementation comments, docstring and warning must state this refusal truthfully instead of claiming these unsafe terminal cases still return last-node output. Retain the established warning category, replacement and existing valid warning assertions. The standing "next minor release" deprecation timeline remains a policy promise requiring an explicit owner decision when retirement occurs; advancing release versions does not authorize removing these doors in this bounded change.
