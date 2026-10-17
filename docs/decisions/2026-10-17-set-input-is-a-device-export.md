---
status: accepted
scope: ["src/junoscfg/convert/input/set_input.py", "src/junoscfg/validate/set_validator.py", "src/junoscfg/input.py"]
enforced-by: tests
review-by: 2027-04-17
---

# Set input is what a device exports

## Context

The QFX5120 probe of 2026-10-16 showed the device taking a typed `set interfaces ge-0/0/1
hold-time up 0 down 0`, which its own `display set` writes as two lines, and refusing verb
lines junoscfg took. The owner wrote on 2026-10-17 (relayed first-hand by the coordinator of
change device-probe-fixes): set syntax has constructs, above all around `delete`,
`deactivate` and `insert`, that need a state machine once they leave format conversion; they
are to be listed and refused with a clean error, especially where support would make the code
much more complex; the main focus is importing a set file exported from a switch.

## Decision

Set input is the file `show configuration | display set` writes. The committed QFX5120 and
vMX captures hold `set`, `deactivate` and `protect` lines only, one statement a line. Out of
scope, each refused with an error naming it (list in `docs/guide/conversion.md`): edit
commands (`insert`, `rename`, `copy`, `annotate`, `unprotect`, `edit`, `replace pattern`:
"Unsupported command in set input on line N"), bracket lists ("Unsupported bracket syntax"),
and several statements on one line (`-v`: "Unsupported in set input, one statement a line";
conversion still reads it). `delete` and `activate` stay: they record Junos's own `operation`
and `active` markers on a statement, are not edit commands, and a `delete` never removes an
earlier line. A verb line names one statement the device can tag, by one walk the reader and
`-v` share (`junoscfg.display.meta_target`); one that names none is refused by both. The
probe tests (`tests/corpus/test_device_probes.py`) and the set reader's and validator's unit
tests pin each refusal.

## Consequences

junoscfg holds no edit state: no ordering, renaming or pattern replacement across lines. A
user with an edit script applies it on a device and exports the result. Supporting a listed
construct is a new decision that weighs the code it costs. A widened grammar for one-line
statements was measured and not taken: it touched 12,416 containers the XSD marks `oneliner`
and grew the shipped grammar by 27 % and its compile by 2.2 s, for a form no export holds.
