# Instruction integrity

Effective instructions: platform and organisation policy (no internal infrastructure
identifiers leave through the commit: the probe log names a lab device and user and
stays in private_test_data/); owner's request of 2026-10-16 to add the QFX probe cases
to tests/data/device/synthetic so the device data can be updated from it later;
standing rules (no push, preserve unrelated work, owner decides backlog); root
AGENTS.md (never real operator data, evidence hierarchy, test-data values);
tests/data/device/README.md (capture procedure, importer); agent-ready-change phase 0
and the maintenance short route.

Base: 2d4904be9f01adca8e2ab472a4f457ef5ce0c403, master clean apart from untracked
.agents/skills/openspec-*, version 0.28.21. Worktree: /private/tmp/junoscfg-qfx-null-probes;
branch change/qfx-null-probes. Python 3.14.7.

Lane: maintenance, economy assurance (tool.template.assurance default). No product
behaviour changes; the importer is repository tooling with no test of its own. Zone
conversion: the probe questions the JSON writer's `[null]` spelling.

Evidence (device first): on the QFX5120 25.2R2-S1.5 the owner ran `load merge json` of
junoscfg's JSON for 15 statements the device itself writes as `{}`, plus the inactive
`l3vpn` junoscfg writes as `{"@": {"inactive": true}}`. The device printed `load
complete` and `show | display set` listed all 16 lines of the set source
(private_test_data/qfx-null-probe/probe.out). This answers device question C8 for these
paths: `[null]` loads as the same statements. The committed capture (four renderings
after `load override json`) is still to be taken; the importer must keep the source
and skip that capture until its renderings exist.

Canonical full: uv run --locked --group dev --with griffe --with tach --with towncrier
--with vulture agent-ready check --set full. Archive --skip-specs, patch bump from
master's version, tag v0.28.22, no push.

Verification cadence: 85 first-parent commits since anchor 95585fb; invitation pending,
deferred to job end. No material owner decisions remain. Next: implementation.
