## Why

A value written inside free text survives the rule that claims it. Under `--anonymize-ips` an
address in `archive-sites "scp://admin@203.0.114.5/path"` or a description stays (ANON-P5); the
user of a URL survives `--anonymize-identities` (NEW-A-N4) and its password `--anonymize-passwords`
(NEW-R15); `apply-path "protocols bgp group EBGP neighbor <*>"` keeps a renamed group's name, so the
prefix list selects nothing (NEW-A-N7). Revert of an embedded AS number is order-dependent and blind
to digit boundaries (NEW-A-N5); `ebgp` and `EBGP` share one pseudonym, so revert restores one case
(NEW-R13); and `<ge-0/0/1?>` is reported under `--anonymize-as-numbers-in-strings` though no AS
number can match (NEW-R14).

## What Changes

- **BREAKING** One chain rewrites the shapes inside a value, for a placed value as for content the
  walk cannot place: an address beside other text (under `ips`, `ips_in_strings` not needed), a
  URL's user (identity rule) and password (password rule), a password hash word, a sensitive word,
  a configured AS number (under `as_numbers_in_strings`). Text one rule wrote is never offered to
  another. A shape that is the whole value is replaced only where its rule takes the value, so an
  SNMP OID `1.3.6.1` and `from area 0.0.0.0` stay. `ips_in_strings` keeps one effect: an address
  that is a whole value on any leaf.
- The post-walk strings passes go: they move into that chain, so `include`/`exclude` now apply to
  them and an AS number is no longer replaced inside an address or a pseudonym (NEW-R16).
- **BREAKING** A sensitive word's pseudonym is keyed by its spelling (`ebgp` and `EBGP` get two);
  the mapping records each spelling, not each whole value.
- An `apply-path` is read against the schema tree: each name in it is offered to the rules as the
  value of the key field it names; `<*>` passes; another wildcard is treated as change 6 treats a
  wildcard name; keywords are never rewritten. A path the tree cannot place is content the walk
  cannot place (owner answer 5).
- Revert undoes every replacement in one pass, longest first, a number only between non-digits and
  never inside an address; the order-dependent substring loop goes.
- A wildcard under `as_numbers_in_strings` is reported only when a configured AS number can be
  spelled where its `?` or class stands.
- No override, fallback, parameter or environment read is added.

## Capabilities

### New Capabilities

- `anonymization/embedded-values`: values inside free text, `apply-path`, and exact revert.

### Modified Capabilities

- `anonymization/placed-values`: "The IP rule answers by the leaf's type" (an address beside text).
- `anonymization/wildcard-names`: the strings passes are the walk's; the revert exception goes;
  scenario "Sensitive words".

## Non-goals

- An SNMP OID rewritten under `ips_in_strings` (NEW-R17, change 18). AS replacements that equal a
  number the configuration already holds. Hostnames in URLs (no rule claims hostnames).

## Impact

`anonymize/{walker,revert,__init__}.py`, `anonymize/rules/{__init__,ip,as_number,identity,password,sensitive_word}.py`,
contract, developer guide, CLI guide, changelog. Reproduce: `private_test_data/makeover-work/anonymize-embedded-values/repro.py`.
