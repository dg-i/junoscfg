# Solo review

This repository is `solo = true`: `manon.goo@dg-i.net` is the only owner in
`[tool.template.stage]`. The policy is **owner acceptance plus a fresh agent
review** — a second read, not a second human, and it never claims otherwise.

For every change, and without exception for a change touching the `anonymize`
red zone:

1. Have a fresh agent session read the proposal, the specs, the tests and the
   diff — fresh meaning a session that did not write them.
2. Resolve its findings, or record why a finding was accepted as-is.
3. Record the owner's acceptance in the change folder.

This is not hosting-platform self-approval and does not satisfy a required
independent reviewer. On `dg-i/junoscfg` the branch protection must therefore
allow the owner to merge their own pull request; that exception, and the risk
it carries, is recorded here rather than hidden in a setting.

`CODEOWNERS` is generated and every rule in it resolves to the one owner, so
each of its overlap warnings unions that owner with themselves. They are
noise today and will stop being noise the moment a second owner appears.

Revisit this whole file when one does: drop `solo = true`, and
`agent-ready fields` will fail until the owner list grows to match.

## Cross-domain changes also get an adversarial corpus review

A change whose behaviour-bearing paths, code under `src/junoscfg/` or the
generated data under `src/junoscfg/validate/data/` and never a `CONTRACT.md` or
a page under `docs/`, fall in more than one of these six areas receives, beside
the fresh agent review above, an independent adversarial corpus review, green
gates notwithstanding: the identifier-key-fields review found three High
findings after the full check was green. The six areas, disjoint, with the paths
the developer guide's rows name:

- the schema pipeline: `validate/xsd_extractor.py`, `xsd_parser.py`,
  `xsd_fixes.py`, `schema_node.py`, `artifact_builder.py`,
  `schema_generator.py`, `grammar_generator.py`;
- the generated artifacts: `validate/data/`;
- conversion: `convert/` except `field_validator.py`, and `input.py`;
- the grammar's runtime: `validate/set_validator.py`;
- validation: `validate/validator.py`, `validate/json_yaml_validator.py`,
  `structured_validator.py`, `xml_validator.py`, `convert/field_validator.py`;
- anonymization: `anonymize/`.

The reviewing agent is fresh, did not implement, and its report carries:

1. the corpus it ran: the JVD corpus tier, the comparison against the frozen
   master baseline when the change carries one, and the device-truth capture
   pairs it has, with the exact commands in the developer guide's
   [pre-review evidence table](../architecture/developer-guide.md#pre-review-evidence-by-the-paths-a-change-touches);
2. the adversarial probes it executed, with inputs and results: complete,
   partial and surplus keys; every reader door (set, structured, JSON, YAML,
   XML); ordinary statements and every meta command (`deactivate`,
   `activate`, `protect`, `delete`);
3. what it could not check, carried forward in the change folder.

It is a second read by a fresh agent, never a second human.
