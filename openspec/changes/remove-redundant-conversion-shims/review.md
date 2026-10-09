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
- **Decision:** Pending owner decision. Safe interim action: both objects were
  restored and this affected change remains unmerged; unrelated roadmap work
  may continue.
