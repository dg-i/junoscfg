## Specification challenges

### Beta API policy prevents immediate shim removal

- **Artifact:** `proposal.md`, removal of `display.to_yaml.json_to_yaml` and
  `convert.output.xml_output`.
- **Counterexample:** The locked full gate's Griffe comparison reports
  `json_to_yaml` and the XML-output module as removed public API objects. The
  repository is beta and `AGENTS.md` requires removals to be deprecated first.
- **User impact:** Merging the proposed deletion would create an undeclared API
  break for direct importers despite preserving the two package-door behaviors.
- **Proposed correction:** Restore both objects, ship a dedicated deprecation
  change first, and schedule deletion for a later permitted minor release.
- **Decision:** Accepted with a different compatibility boundary by the owner
  on 2026-10-09. Package APIs may change provided the production
  `dg-i/ansible-collection-junos-config` consumer remains compatible. Its
  current source imports exactly `FieldValidationError`, `Format`,
  `convert_config`, and `validate_config` from the top-level package, and all
  33 collection tests passed against the roadmap integration checkout. The
  stage now names `consumer` and `cli`; neither removed shim belongs to those
  surfaces. Decision record
  `2026-10-09-scope-compatibility-to-production-consumer` documents the scope,
  migrations, and import bans.

## Findings

1. **MUST — the retired helper name survives as a second test helper.**
   `tests/test_to_yaml.py` defines a new local `json_to_yaml()` immediately
   after the production function is removed. It delegates correctly, but it
   preserves the exact retired concept and lets future tests keep calling the
   old-shaped door, contrary to the accepted decision and the task to route
   characterization through `convert_config()`. Rename it to describe the
   supported door (for example `_convert_json_to_yaml`) or call
   `convert_config()` directly.
2. **SHOULD — the changelog describes removed APIs as internal.**
   `+remove-redundant-conversion-shims.misc.md` says “internal” while the
   proposal, migration, and original Griffe finding all establish that direct
   importers could use them as secondary package APIs. Name both removals and
   their supported migrations so the release note does not hide the break the
   owner explicitly accepted.
3. **SHOULD — the decision overstates automated enforcement.**
   Decision `2026-10-09-scope-compatibility-to-production-consumer` says the
   collection contract is enforced by `agent-ready lane`. That gate detects a
   change to the top-level file; it does not execute the downstream collection.
   Repository tests do import and exercise all four names, and the downstream
   suite passes, so the current change is compatible. Record tests alongside
   the lane as enforcement and describe the 33-test collection run as release
   evidence rather than a gate.

## Review prompts

- **Trust boundary:** configuration text remains the only attacker-controlled
  input. Both supported migrations use the existing parsers and add no new
  trust-boundary path.
- **Incompatible but valid input:** direct imports of the two removed objects
  were valid under the former broad `api` surface. Their removal is the
  owner-approved break; restoring them would contradict the accepted decision.
- **Shared blind spot:** the gates can prove that the top-level file changed,
  but not that a remote consumer still works. Independent evidence is the
  collection at commit `347715a071e44a2cb78b8f87bea79262da63aa5f`, whose 33
  tests pass against this checkout.
- **Second answer:** the local test helper in finding 1 is the only duplicate
  answer introduced by the diff. Production JSON-to-YAML conversion has one
  implementation through the dict-IR pipeline.
- **Figures and non-goals:** the four-import claim was rerun against the named
  collection commit and the 33-test figure was rerun successfully. XML-output
  exception messages and JSON/YAML rendering remain pinned by the focused
  repository suite.
