## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

`_RuleInfo.has_non_list` is removed; with named lists in their own rule nothing
sets it. Private, and the class is module-local. `_rule_name_for` and
`_LIST_RULE_SUFFIX` are added, also private.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. The two `xfail(strict=True)` pins from `grammar-rule-names`
become ordinary regression guards, and five tests are added.

## Docs

`docs/guide/validation.md` keeps its warning: the generator is repaired, the
shipped artefact is not.
