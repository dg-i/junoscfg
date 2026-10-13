<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Instruction-audit ownership and output

## Classify provenance

For every repository file in the observable surface, record one ownership
class:

- **application-owned**: application code, documentation, policy, or a seed
  that Copier deliberately leaves to the application after first creation;
- **template-owned**: a file shipped and updated by the template, including
  agent-ready skills, schemas, and selected workflows;
- **locally modified template file**: template-owned, but its bytes diverge
  from the version recorded by the application;
- **generated mirror**: derived from a named canonical source;
- **external**: user, organisation, provider, plugin, tool, or runtime source.

Derive template provenance from `.copier-answers.yml`, its recorded template
ref, `.agent-ready/template.toml`, and the ownership rule in
`agent-ready-refresh`; do not guess from a familiar filename. If provenance
cannot be established, report `unknown` and ask the owner.

## Route the repair

Never edit a template-owned file in the application repository. A defect in an
unchanged template-owned file is an **upstream template finding**. Name the
template source path and template repository from the recorded source, and
recommend this sequence: fix it in the template repository, release the
template, then run `agent-ready-refresh` in the application repository. Do not
open an application change, run `agent-ready-change` there, or recommend a
local edit or deletion for that finding.

Route a generated-mirror defect to its canonical source. Treat a locally
modified template file as drift: show the local and recorded-template sides and
ask whether the local policy still stands, following `agent-ready-refresh`.
The durable outcomes are an upstream fix or a differently named
application-owned extension, never a silent edit to the template-owned file.

For a finding spanning template-owned and application-owned sources, state
which repository owns each side. Route a template defect upstream; recommend
an application edit only when the application-owned instruction is
independently wrong.

Every finding includes `Ownership`, `Remediation repository`, `Canonical
path`, and `Application action`. `Application action` is `refresh after
release` for an upstream template finding.

## Display the scanned files

In the final user-visible response, include a **Scanned repository files**
section listing every repository path discovered in the surface, grouped by
ownership class and marked `read` or `inaccessible`. Include a separate
**External files** list for every disclosable path outside the repository. Do
not replace paths with a count, summary, or link to a saved report. List
protected non-file source classes and blind spots separately so they are not
mistaken for files.

A persistent report may repeat this inventory, but it does not replace the
user-visible list. Do not create an untracked report merely to shorten the
response; write one only when the owner requests it or the application
repository declares a tracked report home.
