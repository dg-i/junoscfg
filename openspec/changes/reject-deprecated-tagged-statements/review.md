## Specification challenges

### SC1: Preserve correctness by refusing ambiguous terminal metadata

- Artifact: baseline/structured-input-spec.md requirement "The schema-free set writer of the lexer is deprecated": "It keeps its schema-free route, which places a one-line statement's tag on its last node"; baseline/display-CONTRACT.md "deprecated SetConverter.to_set() tags a last node"; four frozen passing legacy tests listed below.
- Counterexample: held synthetic device route `inactive: route 10.98.0.0/16 reject;` is emitted as `deactivate routing-options static route 10.98.0.0/16 reject`; current reread attaches inactive to @reject and loses route entry inactivity. Device .set marks the route path. Protected autonomous-system likewise targets its value. This is executed evidence from current 69f0726, with matching unchanged owning source on base 5187ac9; no device-loaded consequence claimed.
- User impact: deprecated callers receive changed metadata without a visible error (DeprecationWarning is normally hidden). The correction deliberately rejects a bounded accepted legacy shape; deprecation alone does not waive compatibility.
- Proposed correction: standard bug, declared consumer migration to supported convert_config / validate_structured, explicit path-free ValueError for terminal multiword emitted tags only. Freeze and independently assess all original fixtures and assertions. Keep positive content and correct metadata through supported conversion; separately assert deprecated refusal. No schema knowledge/table/parser is added. Finalizer updates main specs after review.
- Decision: Pending owner decision after independent Test/Challenge. Root admission 2026-10-12 approves bounded direction and preparation, but does not permit product/contract/existing-assertion edits before precise independent assessment.

| Frozen existing test | Retained positive set content | Proposed supported metadata assertion |
|---|---|---|
| TestSetConverter.test_groups_transform_to_set | Every foo/bar/baz location line | deactivate groups baz snmp location |
| TestSetConverter.test_inactive_apply_groups_to_set | Every root/snmp foo/bar apply-groups line | deactivate apply-groups and deactivate snmp apply-groups |
| TestSetConverter.test_protect_leaf_emits_command | set system host-name router1 | protect system host-name |
| TestSetConverterWritesADeletePrefix.test_delete_prefix_leaf | set system host-name router1 (strengthen original content coverage) | delete system host-name |

None of these tests may simply be deleted, marked xfail or changed to accept the bad old target. Retain correct block-opening tags, one-token flag tags, replace-only and untagged assertions unchanged. Existing device-meaning xfails remain failures under explicit refusal; any reason update requires accurate follow-up context, never relaxed meaning.
