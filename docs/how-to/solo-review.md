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
a page under `docs/`, cross more than one of the schema pipeline
(`validate/xsd_*.py`, `schema_node.py`, `artifact_builder.py`,
`schema_generator.py`, `grammar_generator.py`), the generated artifacts,
conversion (`convert/`), the grammar, validation (`validate/*_validator.py`,
`convert/field_validator.py`) or anonymization (`anonymize/`) receives, beside
the fresh agent review above, an independent adversarial corpus review, green
gates notwithstanding: the identifier-key-fields review found three High
findings after the full check was green. The reviewing agent is fresh, did not
implement, and its report carries:

1. the corpus it ran: `uv run pytest --jvd tests/test_jvd_corpus.py -q`, the
   comparison against the immutable baseline the
   [developer guide](../architecture/developer-guide.md#when-to-use-each-tier)
   names when the change carries one, and
   `uv run pytest tests/test_device_truth.py -q` over the capture pairs it has;
2. the adversarial probes it executed, with inputs and results: complete,
   partial and surplus keys; every reader door (set, structured, JSON, YAML,
   XML); ordinary statements and every metadata verb (`deactivate`,
   `activate`, `protect`, `delete`);
3. what it could not check, carried forward in the change folder.

It is a second read by a fresh agent, never a second human.
