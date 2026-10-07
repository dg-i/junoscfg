## Findings

A fresh session reviewed this change. It verified the technical core exactly —
both `_safe_rule_name` defects are real, the mutations bite, and the two-`start:`
provenance holds: `d7e19c3` had one `start:` rule, `3b55b78` two, and `a2edd22`
is byte-identical to `3b55b78`. It reproduced the user-visible failure against
the old artefact. Ten findings; five acted on here.

1. **"exits 0" was false, and it shipped.** `cli.py` `_run_validation` has done
   `sys.exit(3)` on `SchemaLoadError` since `d7e19c3`. The tool failed loudly;
   it never passed configurations silently. The claim survived in
   `changelog.d/+grammar-rule-names.bugfix.md`, which goes to release notes,
   and in a comment in `grammar_generator.py`. I had measured the exit code
   through `... | head -1`, so `$?` was `head`'s. **Fixed** in both, and the
   proposal.
2. **The colliding element is `start`, not `start-options`.** The artefact is
   unambiguous: the pre-fix grammar's second rule is
   `start: "start-options" start_options`, so `start` is the element and
   `start-options` its child. The shipped comment and a test docstring said
   otherwise. **Fixed.** My first correction was a blanket replace that broke
   `assert _safe_rule_name("start-options") == "start_options"` — a deliberate
   assertion that only the exact name is reserved. Caught by the suite and
   restored.
3. **The uppercase element was mis-cited.** It is
   `jnx-tel-RE-local-interfaces-stats:interfaces`, and of 60 names producing an
   uppercase rule name in 23.2R2 it is the only one with children, so the only
   one that becomes a rule definition and breaks the grammar. **Fixed** in the
   proposal; the sharper fact is now recorded.
4. **~300 lines of test infrastructure had no record.** `tests/schema_data.py`,
   `tests/test_schema_data.py` and the `--schema` flag, marker and fixtures in
   `conftest.py` all landed in `998915f` and appeared in no change document.
   **Fixed**: recorded in What Changes, and `private_test_data/README.md`,
   which still described the superseded layout, is rewritten.
5. **The record was stale.** Three declared `xfail(strict=True)` tests, none of
   which exists now, and an Impact line saying validation stays broken. **Fixed**
   to describe what this change did and name the successors that finished it.
6. **`retires.md` undercounted tests (four, actually sixteen) and said no docs
   changed**, when `4c633d5` removed a promise from `docs/guide/validation.md`.
   **Fixed.**
7. **Stale `codemap.md`** against the symbol index. **Fixed** by regenerating.

## Accepted as-is

- The reviewer notes the lowercase fix has no dump-free end-to-end test: it is
  held by two string assertions plus `test_schema_data.py`, which needs
  `--schema`. True, and worth closing, but the generator is not what ships —
  `TestBundledGrammarIsReproducible` covers the artefact. Carried forward.
- `checklist.md`'s deprecation reasoning is loose: rule names are unobservable
  because `SetValidator` discards the parse tree, not because the grammar did
  not compile. The conclusion stands; not reworded.
- The 706 KiB figure in tasks.md 3.1 is not reproducible after three generator
  changes. Left as the record of what was measured then.

## Specification challenges

No challenge. `skip_specs: true`.

## Verdict

Accepted after correction. The engineering was right and the record was not:
one claim was false and user-facing, one named the wrong element, and a third
of the change was undocumented. Owner acceptance: the owner asked for the open
changes to be archived in this session; they have not reviewed these findings
individually.
