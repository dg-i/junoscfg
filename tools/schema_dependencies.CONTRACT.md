# schema_dependencies — contract

Application-owned dependency relevance for schema qualification; no test cache.

- Fingerprint the complete parsed uv.lock, excluding only the nonempty version
  field of exactly one package named junoscfg with source `{editable: "."}`.
  Retain every other field, including root dependencies, Python constraints,
  third-party versions, sources and artifact hashes. Ambiguity refuses.
- Lock, fingerprint and required-obligation inputs must be physical files;
  absent, malformed, symlinked or inconsistent inputs fail closed.
- `write` deliberately refreshes the committed projection. `check` never does:
  it executes consistency and publishes only its named guard obligation.
- Clear prior guard completion before checking. A failed check leaves no success.
  Native verification owns admission, immutable identity, caching and locking.
- This tooling uses the repository's existing tomllib developer environment;
  it does not change the Python compatibility floor of the runtime package.

Not for selecting a reduced dependency subset, claiming schema tests ran,
relaxing generator triggers, or changing real-schema assertions.
