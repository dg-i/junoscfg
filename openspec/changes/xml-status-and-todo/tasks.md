## 1. Verification

- [x] 1.1 Inspect local Markdown links with Python pathlib; all linked targets exist and no new fragments require resolution.
- [x] 1.2 Inspect git diff: no commands or examples change; all referenced source paths exist.
- [x] 1.3 Inspect wording against current conversion sources and owner decision: both surfaces buggy, output unimplemented, no universal-failure claim.
- [x] 1.4 Inspect mkdocs.yml: `/roadmaps/*.md` admits the roadmap; README is the user entry point and roadmap is future work.
- [x] 1.5 Run `env UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --group docs mkdocs build --strict --site-dir private_test_data/xml-status-site`; inspect rendered roadmap and locally rendered README status/link.
- [x] 1.6 Run `git diff --name-only e293b72564ef579a393102e4578f253efa8bdc8f HEAD`: only declared docs and own records change.

## 2. Change

- [x] 2.1 Add concise XML status and TODO link to README.md.
- [x] 2.2 Add deferred roadmap covering input IR parity, output decision/design/evidence, XML format/IR qualification and evidenced defects.

## 3. Review and evidence

- [ ] 3.0 Run root-admitted native checkpoint after actual READY; preserve exact argv, HEAD, raw log and result; no schema execution.

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

QA: strict MkDocs exit 0 at333ef76; activation-only rebase preserves both docs byte-for-byte. Rendered README and roadmap inspected; local links and existing roadmap wildcard resolve. Initial root-architecture link failure corrected; initial root Python lacked Markdown, supported locked docs environment passed.
