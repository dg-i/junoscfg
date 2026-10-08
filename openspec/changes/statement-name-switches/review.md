# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

4,238 nodes, every one named `enable-disable`; 26,386 positional nokeyword
leaves and 352 `freeform-nk` keep the node name; structured output
byte-identical with the fix off, on all three real devices. **Zero near-misses
in 24.4R0** — no nokeyword leaf where only *some* enum values are words of its
own name — so the predicate is not currently marginal.

## Findings

1. **The change made junoscfg emit JSON and YAML that junoscfg rejects.** The
   fix changed `set_input` only; `schema_generator` still named
   `enable-disable` with `additionalProperties: false`, so `disable` became an
   unexpected property everywhere. 19 `disable` lines across the three real
   devices. Nothing caught it because **no test anywhere converted a
   configuration and then validated the result**, and no example file or
   corpus line contains `disable`. **Fixed in v0.7.0**, together with the four
   deeper causes of the same break that it exposed, and the missing test.
2. **The headline was false in general: 286 `enable-disable` keys survived.**
   The guard was `token in allowed`, and 4,152 of the 4,238 nodes carry
   `['disable']` alone — so `set interfaces ge-0/0/0 enable` still wrote
   `enable-disable`. Across the 1,500 convertible jvd configurations: 46
   `enable`, plus 240 others where the pre-existing nokeyword catch-all
   swallows an unmodelled token into a fabricated key.
   **Fixed in v0.7.0** by keying on the node name's own words, which handles
   both spellings; the remaining 240 are the older catch-all, not this change.
3. **The pun is unguarded by anything but a naming convention.** 266 enum
   tables already in the shipped artifact would trip it if a node were ever
   named after them — `tcp-udp-tls` with `['tcp','udp','tls']`,
   `master-standby`. A release applying that convention to a choice of
   *values* rather than *statements* would silently re-key real values.
   Recorded as a known fragility; `test_disable_keys_on_the_statement` is the
   tripwire, but it only fires on `--regen-schema`.

## Resolution

The change was right about the device behaviour and wrong about the blast
radius in both directions — it fixed half the switch and broke the round trip.
Both fixed. Finding 3 stands as recorded fragility.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.
