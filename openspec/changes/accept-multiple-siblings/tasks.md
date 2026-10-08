## 1. Tests

- [x] 1.1 Add reviewed acceptance tests for compact and expanded sibling forms,
  public validation doors, CLI behavior, narrow rejection, corpus accounting,
  and parse cost; confirm the new behavior fails before implementation.

## 2. Implementation

- [x] 2.1 Isolate oneliner named-list grammar rules and repeat only their
  keyworded child alternatives after the entry name.
- [x] 2.2 Recognize flat positional children and allow their parent rule to
  append repeated keyworded siblings after consuming the positional value.
- [x] 2.3 Regenerate the shipped Lark grammar from the shipped structure tree.
- [x] 2.4 Update validation documentation, changelog, and patch version.
- [x] 2.5 Run the reviewed acceptance tests, pre-commit, and the complete
  agent-ready check; tick every task only after its evidence is green.
  Acceptance tests, pre-commit, full pytest, and every change-scoped gate are
  green against local `master`. The complete command also reports two
  repository-global failures already present on that base: stale generated
  CODEOWNERS and a stage-lever render collision. They are carried forward
  below rather than mixed into this bug fix.
