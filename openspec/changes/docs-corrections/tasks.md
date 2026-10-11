## 1. Verification (one per docs-plan QA item)

- [ ] 1.1 Links and anchors: `uv run --locked --group docs mkdocs build --strict` exits 0; the only INFO notice is the pre-existing `how-to/hosting.md` not in nav (baseline at 5d464a8: exit 0, that notice only)
- [ ] 1.2 Commands and examples: the worked example's `junoscfg convert -i json -e yaml`, `-i yaml -e conf`, `-i json -e set`, and the container example's `-i json -e conf`, run on the page's own input at the checked head, print exactly what the page shows; every set line the changed text names gives the stated `validate_set` result
- [ ] 1.3 Referenced paths: every path the changed text names exists (`ls`)
- [ ] 1.4 Terminology: `git grep -n -e dc-a -e "system location" -- '*.md' ':!openspec/changes/archive' ':!openspec/changes/docs-corrections' ':!openspec/specs'` lists only lines of the corrected validation paragraph (baseline at 5d464a8: six lines in `annotations.md`, one in `validation.md`)
- [ ] 1.5 Placement: the edits stay inside the existing "Set Commands" admonition and the two annotation examples; no new page or section (inspection of the diff)
- [ ] 1.6 Rendered output: markdownlint passes on both pages (pre-commit); the admonition keeps its four-space indentation and renders as one block in the strict build (inspection of `site/guide/validation/index.html`)
- [ ] 1.7 One full checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` passes

## 2. Change

- [ ] 2.1 `docs/guide/validation.md`: the "Set Commands" warning (merge of same-named rules, share of device lines, `system location dc-a` as malformed input with the device spelling)
- [ ] 2.2 `docs/guide/annotations.md`: `location dc-a` becomes `domain-name example.net` in the container example and the worked `replace` example, outputs as rerun

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

## Evidence
