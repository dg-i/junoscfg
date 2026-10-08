## 1. Tests

- [x] 1.1 `tests/test_round_trip_validates.py`: eight shapes across JSON and
  YAML, plus `examples/router1.set` whole. 19 tests.
- [x] 1.2 Seen to fail. Each fix mutated in turn, the artifacts regenerated
  under the mutation so the shipped schema actually changed:

  | mutation | failures |
  |---|---|
  | entry key misspelled | 15 of 19 |
  | statement spellings dropped | 4 |
  | presence array dropped | 6 |
  | universal floor dropped | 2 |

- [x] 1.3 `tests/test_artifact_resolution.py` records the new contract: a
  chosen directory raises, only the bundled one answers `None`.
- [x] 1.4 Four tests that pinned the old behaviour were rewritten, not
  deleted, each saying what it used to assert and why that was wrong.

## 2. The round trip

- [x] 2.1 Named list entry key. 4 of 24.4R0's 20,367 named lists carry a
  `name` child; the key is `name`, a flat-entry list's own (`route-filter`
  writes `address`), or an override the set reader spells out
  (`community-name`, which `audit/walker.py` already called "hardcoded in the
  set parser").
- [x] 2.2 Presence flags accept `[null]`.
- [x] 2.3 Containers accept the bare-statement shapes through a type union,
  which keeps the schema navigable where a `oneOf` wrapper buried it.
- [x] 2.4 `UNIVERSAL_STATEMENTS` in the kernel is the floor. Eight modules
  knew the four names separately.
- [x] 2.5 Measured: `examples/router1.set` 8 errors to 0; the three devices
  51/17/38 to 1/0/1. Both residuals are statements the set reader cannot
  parse -- `analyzer`, `uplink-failure-detection` -- already counted among the
  21 rejected set lines.

## 3. What junoscfg accepts

- [x] 3.1 Either-order nodes take `__list__eo`. `set interfaces mtu 9192
  ge-0/0/0` and `set protocols bgp group G neighbor peer-as 64496 10.0.0.1`
  are rejected; `then community add COMM-A` and `flag all detail` still pass.
- [x] 3.2 Rejection rate unchanged at 0.30% (21 of 7,097), per device
  0.36/0.00/0.38. Grammar load 3.8s. Rules 4,386 to 4,402.
- [x] 3.3 `QUOTED_OR_VALUE` slots 11,694 to 10,469. The mutation measure moved
  70.4% to 70.3%: the widening is **not** closed, and cannot be from this
  tree. Recorded as a non-goal rather than claimed.
- [x] 3.4 Integer validation fires. `maximum-entries notanumber` warns; it did
  not, for every `xsd:`-prefixed type, because the table held bare names.
- [x] 3.5 26 closed enums enforced, 4,342 fragments still escaping. `set
  protocols pim rp auto-rp frobnicate` warns and `vlan-id 100` does not.

## 4. Gates

- [x] 4.1 1,517 passed, 44 skipped, 1 xfailed. 1,497 before.
- [x] 4.2 `--jvd`: 7 passed in 177s.
- [x] 4.3 `tach check`, `agent-ready interfaces`, ruff: pass.
- [x] 4.4 `uv build`: sdist 2.3 MB, 0 `private_test_data` files, 5 artifacts.
