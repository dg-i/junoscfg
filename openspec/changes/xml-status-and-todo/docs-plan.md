## Reader and task

- Reader: users selecting formats and maintainers planning XML work.
- Task: recognize XML status and locate the bounded deferred work list.

## Authoritative sources

| Claim | Source |
|---|---|
| Both XML surfaces are buggy and deferred | Owner XML deferral, 2026-10-12; root scope ruling |
| XML output raises NotImplementedError | src/junoscfg/__init__.py::convert_config; ARCHITECTURE.md |
| XML input exists, without whole-surface qualification | src/junoscfg/convert/input/xml_input.py; convert/CONTRACT.md |
| Output requires scope/ban reconciliation before future implementation | docs/decisions/2026-10-09-scope-compatibility-to-production-consumer.md; pyproject.toml ban |
| Roadmap is registered without configuration edits | mkdocs.yml not_in_nav /roadmaps/*.md |

## Affected documents

- README.md: visible format status at the main user entry point.
- docs/roadmaps/xml-work-todo.md: deferred future work, not current instructions.

## Documentation QA

- Links and anchors: resolve README roadmap and roadmap architecture/decision links; no new fragment anchors.
- Commands and examples: not applicable; no commands or examples added or changed.
- Referenced paths: verify sources and linked documents exist at the checked HEAD.
- Terminology: both surfaces say buggy; distinguish input qualification from absent output; no claim that every operation fails.
- Diátaxis placement: README status and roadmap are appropriate for status and future work; existing not_in_nav wildcard admits roadmap.
- Rendered output: offline locked MkDocs build to private output; inspect rendered README Markdown and roadmap HTML status/link/list.
- Preservation: git diff names only the declared product documents and own change records; no API, tests, configuration or ban change.
- Native checkpoint: root must admit docs-only full or a qualified substitute before execution; no real schema run in this phase.

- changelog.d/xml-status-and-todo.doc.md: required stage news fragment, documentation-only.
- Changelog QA: native towncrier stage accepts the `.doc.md` fragment.
