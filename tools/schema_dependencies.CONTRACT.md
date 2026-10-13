# schema_dependencies — contract

Application-owned dependency relevance for schema qualification; no test cache.

- Fingerprint the complete locked records of SCHEMA_PACKAGES and their transitive
  dependencies, including every locked platform/marker variant, source and
  artifact hash. Roots cover generation, validation, public CLI regeneration and
  the pytest harness; Python/lock resolution constraints remain bound.
- Exclude unrelated packages, the editable root release version and requirements
  outside that execution closure. Require one valid editable junoscfg root,
  nonempty execution closure and resolvable dependency edges; ambiguity refuses.
- agent-ready-checks distribution versions and updater bytes are not a schema
  dependency. Native runtime-modules binds its actual transitive execution code
  and external dependencies; an engine change still invalidates relevant proof.
- Historical lock text uses exactly the current fingerprint_text projection.
- Lock, fingerprint and required-obligation inputs must be physical files;
  absent, malformed, symlinked or inconsistent inputs fail closed.
- `write` deliberately refreshes the committed projection. `check` never does:
  it publishes only the dependency-consistency obligation and clears prior guard
  completion first. Native verification owns success, caching and locking.
- Installed pytest plugins and runtime dependency bytes participate separately
  in native execution identity and immutable prepared runtime observations.

Not for claiming schema execution, changing assertions, or overriding selection.
