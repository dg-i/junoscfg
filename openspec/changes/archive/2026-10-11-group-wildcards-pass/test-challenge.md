# Test/Challenge: group-wildcards-pass (ANON-P3 = NEW-C12)

Role: independent Test/Challenge (phase 4, STOP-T). Read: roles brief, phase 4, proposal, delta,
evidence freeze, `review.md` (S1), `git diff 1ebeed9..08a944b -- tests/`, `repro-base.out`,
`tests-on-base.out`, `anonymize/rules/ip.py`. The probe is `roles/challenge_probe.py`, its output
`roles/challenge_probe.out`. It runs on the checked-out product, which is still the base, and applies
the delta's report trigger (fnmatchcase selection over the names at the place) by hand.

## What holds

- The tests fail on the base for the right reasons: the wildcard is renamed or left, or
  `patterns` is missing. The freeze names the 18 pins, and they pass for stated reasons.
- The tests assert the IR (meaning), not layout. No oracle is weakened: the `<` filters go and SHA
  `8e13d961…` stays pinned. The tests reach the library door, `convert_config`, the CLI door
  (message rows) and four corpus input formats.
- The `selects-nothing` and `sensitive-word` rows refute a plain "report whenever the text
  changed" implementation.

## Findings, ranked

### F1 (high, leak; specification gap): an address pattern with nothing at its place leaks unreported

Probe C1: `groups GR-BGP protocols bgp group <*> neighbor "<203.0.114.*>"` with `--anonymize-ips`
and no neighbour at the place. The IP rule finds no address token (`address_tokens("203.0.114.*") == []`),
so it does not claim the text. The selection is empty before and after. **The trigger does not fire,
and `203.0.114` stays in the output.** When neighbours are present (the `[ip]` row), the pattern is
reported, but the /24 still leaks under `--anonymize-ips`.

The IP rule is prefix-preserving: `203.0.114.7` becomes `203.211.226.136` and `.8` becomes
`203.211.226.130`, and `10.0.0.1` becomes `10.32.52.103`. An octet-aligned `<a.b.c.*>` therefore has
an exact rewrite that leaks nothing (`<203.211.226.*>`). S1's options omit this, and
`test_a_wildcard_that_selects_other_names_is_reported[ip]` would forbid it.

- Proposed test: C1 must satisfy `"203.0.114" not in output or path in result.patterns`.
- Proposed challenge S2: rewrite octet-aligned address patterns through the prefix permutation,
  or report every address pattern the IP rule cannot rewrite.

### F2 (high, leak): a sensitive word hidden by wildcard syntax

Probe C2: `"<[Aa]cme-*>"` with `sensitive_words=["acme"]` and no `acme` names. The substring match
misses it, the selection does not change, and the pattern is not reported. `[Aa]` is the usual
Junos case-insensitive idiom.

- Proposed test: no `cme` in the output, or the path appears in `patterns`.
- Spec: add "a sensitive word or pattern that the text could spell once its classes and `?` are
  expanded".

### F3 (medium; a wrong implementation passes): case folding

Probe C3: `<acme-*>` beside `ACME-A`, with `acme` as a sensitive word. The output is
`<word_…-*>`, which now selects `word_…-A`. Before, it selected nothing. The trigger fires, but no
test covers this. An implementation that treats "a rule rewrote the text" as "same selection"
passes all 39 tests.

- Proposed test: this case is reported.
- The same input breaks "Revert SHALL restore every wildcard exactly" (NEW-R13: one pseudonym
  serves both cases). Add a strict xfail that cites NEW-R13, or scope the requirement.

### F4 (medium): name sets

Every target name sits at top level, outside groups. Two wrong implementations pass every test:
one that uses only names outside groups, and one that matches on the path suffix and ignores
`routing-instances`. Proposed tests:

- (a) `<EBGP-*>` in `GR-A`, with `EBGP-B` only in `GR-B`: reported, as the spec's "inside and
  outside groups" requires.
- (b) `routing-instances <*> protocols bgp group <EBGP-*>`, with `routing-instances R1 protocols bgp
  group EBGP-A`: reported.
- (c) Top-level `<EBGP-*>`, with `EBGP-A` only in R1: not reported.
- (d) `<*BGP*>` beside `<EBGP-*>` in another group: wildcard strings are excluded from the name set.

Device question for (a): does group A's wildcard select a name inherited from group B? Ask for a
capture of that path only.

### F5 (medium-low): the count is never asserted

Proposed test: two reported wildcards at one path give that path twice in `patterns` and one
warning that says 2.

### F6 (low): the corpus negative depends on a word

`[w for w in run.warnings if "wildcard" in w] == []` passes vacuously if the message changes.
Assert instead that no `anonymize` diagnostic names a wildcard's path, or assert `patterns == ()`
through `anonymize()`.

### F7 (low): a spurious report

`198.51.100.1` maps to itself (it is preserved). Under the "claims its text and leaves it as
written" clause, `<198.51.100.1>` would be reported although it leaks nothing and selects the
same names. Add a negative test, or reword the spec.

### F8 (low): Junos semantics against fnmatch

They agree on `*`, `?`, `[...]`, `[!...]`, `]` first and `-` first or last. `*` crosses `/`, as the
device's `<ge-*>` does on `ge-0/0/0`. They diverge here:

- `[^...]`: Python reads `^` literally, while FreeBSD fnmatch(3) negates.
- `\`: Python reads it literally, while FreeBSD treats it as an escape.
- An unclosed `[`.

The check uses one matcher before and after, so a divergence changes a verdict only on renamed
names in the divergent class. The implementation must use `fnmatchcase`. The freeze's "same syntax"
needs a citation or the label "unverified".

### F9 (low)

`test_a_match_all_wildcard_name_passes` checks only for `<`. Also assert that `"*"` is never an
original in the mapping.
