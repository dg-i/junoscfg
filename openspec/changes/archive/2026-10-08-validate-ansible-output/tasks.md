## 1. Tests

- [x] 1.1 `tests/test_set_corpus.py` records four fewer rejections; the pinned
  list is what proves nothing else regressed.
- [x] 1.2 The nine adversarial commands are still rejected.

## 2. Implementation

- [x] 2.1 Splice a child the parent is transparent over.
- [x] 2.2 Strip `apply-flags` and `apply-macro` as well as `apply-groups`.
- [x] 2.3 A named list's entry name is `QUOTED_OR_VALUE`.
- [x] 2.4 Every leaf value is `QUOTED_OR_VALUE`; `_QUOTED_FIELDS` goes.
- [x] 2.5 A oneliner list of bare keywords takes them on either side of the
  entry name.
- [x] 2.6 A bare `set apply-groups <name>` is accepted: stripping left `set`,
  which parses as nothing.
- [x] 2.7 A presence list takes its entry name: 5,808 nodes emitted a bare
  keyword with nowhere for the name to go.
- [x] 2.8 A parenthesised policy expression is one value, confirmed against the
  device's own `| display json`: it carries the expression as one opaque string.
- [x] 2.9 `flat-dict` and `flat-entry` take a run of values.
- [x] 2.10 The apply-* stripper stops at a quote; the check is positional, so
  `apply-groups "foo"` is still stripped while a description is not.
- [x] 2.11 Rebuild `src/junoscfg/validate/data/junos-set.lark`.

## 3. Verification

- [x] 3.1 The collection's example playbook runs under ansible-core 2.21.5 and
  renders `router1.conf` and `router2.conf`; both now validate clean, from
  seven errors each.
- [x] 3.2 Corpus 100 to 104 of 116; nine of nine adversarial rejected;
  4.2s compile, 4 ms a line.
- [x] 3.3 A real 6,941-line border-gateway configuration converts to set, JSON
  and YAML in 1.2s, 2.1s and 1.4s. Validation rejects 8.6% of its 3,369 set
  lines, from 9.1%. Across three devices -- a border router, an admin switch
  and a lab switch, 7,093 set lines -- 7.1% to 0.30%. The admin switch validates
  completely clean. `then community <action> <name>` was 343 of the 507,
  `snmp filter-interfaces interfaces <n>` 43, and policy algebra 33.
- [x] 3.4 The collection's 33 tests pass and its four filters produce output
  byte-identical to junoscfg 0.6.8, before any of this session's work.
