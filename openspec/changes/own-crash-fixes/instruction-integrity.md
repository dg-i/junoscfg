## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree `/private/tmp/junoscfg-own-crash-fixes`; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Synthetic values only (AGENTS.md test-data table); no credentials or personal data echoed |
| Coordinator brief carrying the owner request of 2026-10-16 (first-hand, approved) | This change | Owner (relayed) | yes | Fix three junoscfg defects in one change: (1) legacy `yaml` crashes on a non-string key; (2) JSON nested ~1,600 deep crashes with `RecursionError`, reuse the 64-level rule, measure the other input formats; (3) an absolute `--path` ending at a single leaf drops the leaf's own tags in every output format. Builder runs phases 0 to 5 with the full check, then stops for the coordinator's independent Reviewer; no push, no archive, no backlog without the owner |
| ARCHITECTURE.md section 8, decisions 2026-10-15-configuration-input-is-trusted and 2026-10-15-yaml-nests-at-most-64-levels | Repository | Repository | yes | Input is trusted: no guards against hostile input, no work-arounds for parser limits (PyYAML past ~490 levels, `json.loads` past ~20,000); junoscfg's own crash, loop or wrong output is fixed |
| AGENTS.md | Repository | Repository | yes | Equivalent-not-identical output, fix at the owning layer, measure the blast radius, tests first, documentation checklist, beta stage, patch for non-breaks |
| agent-ready-change skill, batches.md, phases 0 to 5 | Workflow | Skill | yes | Standard lane (type bug: three failure modes the owner asked for as one change); tests first and observed failing; one full checkpoint on a committed snapshot |
| `src/junoscfg/input.CONTRACT.md`, `src/junoscfg/convert/CONTRACT.md`, `src/junoscfg/display/CONTRACT.md`, `tests/CONTRACT.md` | Modules, tests | Repository | yes | `find_non_json_value` is the one depth/cycle boundary; `display` is the kernel owning `filter_dict_by_path`; import through package doors |
| openspec/specs/conversion/junos-json-yaml, conversion/path-filtering, validation/junos-json-yaml | Approved specs | Specs | yes | Requirements this change modifies (non-string keys in `yaml`, JSON depth, absolute leaf selections) |
| Archived change 2026-10-15-relative-selections | Evidence | Evidence | yes | Relative selections drop a tag on the selected statement itself on purpose; out of scope here |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | batches.md: several failure modes are separate fixes or one standard-lane bug when they form one coherent outcome; the owner asks for the three defects as one change | automatically resolved by precedence | Owner instruction wins; one standard-lane `bug` change whose outcome is "junoscfg's own conversion code neither crashes nor silently changes meaning on trusted input" | One branch, one review, one full check |
| C2 | Tests `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_key_that_is_not_a_string_is_named_by_its_kind` and `tests/unit/input/test_input.py::TestFindNonJsonValue::test_without_scalars_only_a_cycle_or_depth_is_refused` walk YAML documents holding non-string keys with `scalars=False`; the owner delegates the key rule to the Builder (refuse or read as string) | automatically resolved by precedence | Builder chooses the rule in the proposal; the tests change with it, recorded in the spec delta | Two existing tests change their expectation |
| C3 | Measured at base: an absolute selection through a deactivated ancestor (`deactivate system`, `--path system.host-name`) also drops the ancestor's tag; the request names the leaf's own tags only | owner decision required | Not acted on; reported as a pending owner decision (needs a device artefact: what `show configuration system host-name \| display set` prints under a deactivated `system`) | Out of this change's scope |
| C4 | Coordinator brief: `change/qfx-null-probes` is "ready" in the inventory from an abandoned attempt; master's `.agent-ready/activation.json` does not list it and `agent-ready readiness --activate` refused (`unassessed local branches: change/qfx-null-probes`) | runtime/operator correction | Builder recorded it `ready`, as that branch's own activation.json and the shared assessment hold it, and preserved every other entry; reported to the coordinator | Inventory installed |
| C5 | `docs/VERIFICATION.md` invitation pending since 1a79527 | automatically resolved by precedence | Unattended job: invitation deferred to job end (coordinator) | None for this change |

## Assurance

- Standing preference: economy (`pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; key `default`).
- Mandatory risk floor: high. Named surfaces change output (`consumer`: `convert_config`
  and `validate_config` raise or report where they crashed, and keep a leaf's tags under
  `path=`; `cli`: `junoscfg convert` exits with an error where it printed a traceback, and
  `--path` keeps a leaf's tags).
- Required roles: Builder; independent Test/Challenge (fresh agent, no Builder reasoning);
  fresh isolated Reviewer at least as capable as the Builder, dispatched by the coordinator;
  Finalizer (Builder, bounded, after the verdict).

## Execution checkpoint

Base `2d4904be9f01adca8e2ab472a4f457ef5ce0c403` (master, v0.28.21). Branch
`change/own-crash-fixes`. Standard lane, type bug, zone conversion. Full check: `uv run
--locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready
check --set full` on a committed snapshot; physical schema dumps copied from
`private_test_data/schemas` if a schema tier is selected. Evidence probes in the session
scratchpad, results recorded in `tasks.md` and `review.md`. Integration (merge order, bump,
tag, park) by the coordinator after review; no push. `tests/data/device` and
`tools/import_device_captures.py` untouched (parallel session).

## Owner decision batch

None blocking. C3 is reported at hand-off.

## Delta log

- Initial preflight: consistent after C1 to C5. Resume: phase 1 proposal.
