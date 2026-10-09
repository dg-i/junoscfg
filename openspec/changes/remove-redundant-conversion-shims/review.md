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
