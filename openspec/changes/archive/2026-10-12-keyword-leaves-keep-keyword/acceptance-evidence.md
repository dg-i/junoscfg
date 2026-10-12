## Executed base evidence

Product source/artifacts remain byte-identical to base b10ba77134fe6d36d1f2ab5859710498ab010764. Tests were added before implementation; no schema generation/full/schema tier ran.

- Unit command: `env UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest tests/unit/validate/test_xsd_fixes.py::TestFlatPositionalHints tests/unit/validate/test_xsd_fixes.py::TestTriggerFlattening tests/unit/convert/test_convert_roundtrip.py::TestAFlatHintPreservesRicherContent -q --tb=short`:17 failed,6 passed. Six genuine nokeyword variants pass; twelve keyworded/freeform variants, contextual trigger ownership and four richer-content variants fail.
- Matrix command: `env UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest tests/contract/test_format_matrix.py -k 'keyworded or optical-trigger or sonet-trigger or positional-trace or positional-maximum or event-trigger-with-its-supported-count' -q --tb=short`:210 failed,290 passed,4317 deselected. All ten rows use five reader sources/four writers and independent expected IR. Failures are keyword omission/nested truncation; two positional controls and supported event-trigger row pass.
- Schema validation command: same selection under `tests/contract/test_round_trip_validates.py`:20 passed,333 deselected. Every new row's JSON/YAML result validates against shipped schemas; this is ordinary runtime validation, not the deferred real-schema tier.
- Public `validate_config(text, format=fmt)` on each row passes all40 Set/structured/JSON/YAML input validations. An initial inspection used an incorrect keyword argument, corrected to the actual public signature before this successful observation.
- Initial positional controls also asserted a fused full Set line. Base output legitimately splits siblings; removed that unsupported layout assertion before baseline approval, retaining full independent-IR round trips and positional syntax controls. No governing requirement was reduced.

Raw pytest summaries and SHA256 manifest are retained privately at main `private_test_data/makeover-work/keyword-leaves-keep-keyword/{unit-red,matrix-red,validation-base}.txt` and `acceptance-logs.json`. Exit statuses were not separately retained in the initial multi-command shell calls; executed native summaries are authoritative, not a claimed green checkpoint.

## Integrity and role status

Pinned OpenSpec strict validation, agent-ready fields/caps/codemap/reconcile/skills, complete test-door scan, ruff and diff whitespace checks pass. Standing tool and skill line-budget notices are unchanged report-only. Phase3 is not applicable to this bug. Independent Test/Challenge is required and pending orchestrator dispatch; Builder tests are not independent evidence.

## Scope and minimum generation plan

Implementation ownership: xsd_fixes.py contextual flat flags; convert/output/dict_walker.py richer-shape fallback; three test paths; public-generated validate/data products; exact count docs/changelog/owned known-differences as actual evidence requires. No input.py, set_input.py, set_validator.py, convert/CONTRACT.md, docs/api/input.md or mkdocs edits.

After STOP-T ruling, repair source then invoke once: `env UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --locked junoscfg schema generate /Users/manon-dev/src/junoscfg/private_test_data/schemas/25.2R2-S1.5_qfx5120.xsd -o src/junoscfg/validate/data`. This necessary product artifact generation is distinct from deferred schema verification. No manual artifact patch, no full schema before final makeover, no21.4/23.2 execution. Preserve final25.2 doublepass/stability/sentinel and unchanged91.47 coverage floor. Later ordinary-full needs explicit root admission.

Expected blast radius from current artifact scan:754 keyworded pkf slots and108 unrelated trigger fd slots; genuine nk slots and two event-options trigger paths retained. Exact regenerated changes and device before/after evidence remain pending; no future result claimed. DEV-V6 remains evidence-blocked, current supported behavior retained.
