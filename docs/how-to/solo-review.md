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
