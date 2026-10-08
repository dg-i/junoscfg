## 1. Tests

- [x] 1.1 `TestAnUnmodelledStatementIsKeptWhole`: the rest of the line kept,
  the set round trip exact, a switch and a switch-then-sibling unchanged, a
  typeless schema node kept whole. Three of five seen to fail first.
- [x] 1.2 `TestAnUnmodelledStatementIsReported`: an unknown key is an error;
  an entry key, a flat entry's key and `_v` values, an overridden key, a
  universal statement and a switch spelling are not. One seen to fail first.
- [x] 1.3 The pipeline keeps the statement, names it on stderr, raises under
  strict. Seen to fail first.
- [x] 1.4 The jvd tier splits the two axes; `TestUnmodelledStatementsAreCounted`
  records the share and prints the shapes.

## 2. Implementation

- [x] 2.1 `set_input.py`: the nokeyword leaf takes one token only when the
  line ends or a sibling follows; the typeless-node fallback keeps the line.
- [x] 2.2 `field_validator.py`: `_is_structural_key`, the universal skip, the
  error on any other key the schema does not name, naming the list entry;
  the `configuration` wrapper stripped rather than reported.
- [x] 2.5 `convert/__init__.py`: anonymization refuses an unplaced statement,
  whatever `validate` and `strict` say; the review found the leak.
- [x] 2.3 Version 0.9.0 in four places; break declared for api and cli.
- [x] 2.4 `docs/guide/validation.md`: the check and its default-behaviour line.

## 3. Verification

- [x] 3.1 Blast radius before, three devices: 0 catch-all, 7 unknown-token
  lines of 6,998. jvd: 0 catch-all, 69,122 unknown-token of 2,222,948 set
  lines, 407 shapes; `bridge-domains` 85%. Like with like on the 24.4R0
  artifacts: 114 catch-all drops and 69,193 unknown-token, so the schema swap
  removed the silent drops and the `bridge-domains` gap is in both trees: the
  node exists with its children, without the transparent flag.
- [x] 3.2 After, jvd: conversion 1,500 of 1,535 unchanged; 69,165 unmodelled
  reported against 69,122 the reader keeps whole, a residue of 43 keys from
  other IR paths left for the review to name; value warnings 233 to 542, all
  309 of them mandatory-field warnings the pipeline prints only beside an
  error, then 521 once the false `enable-disable` one was fixed. The tier
  passes: 8 passed, 0.11 value warnings per 1k against 0.5, share 1.4%
  against 3%.
- [x] 3.3 Full suite green, pre-commit, openspec validate and fields clean.
