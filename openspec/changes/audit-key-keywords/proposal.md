## Why

The unused-object audit builds each keyed entry's CLI path with a local key rule that drops two kinds of key token the set writer prints: the keyword of a key field whose leaf is not `nokeyword` (`virtual-link 10.255.255.1 0.0.0.2` for `virtual-link neighbor-id 10.255.255.1 transit-area 0.0.0.2`, a spelling the device rejects) and the value of a key choice (`route-filter 10.0.0.0/8 upto` for `... upto /24`). Delete, deactivate and show scripts built from such paths are device-invalid (OPEN-12).

## What Changes

- `audit/walker.py` `_key_tokens` writes an entry's key as `convert/output/dict_walker.py` `_entry_key` does: a key field's keyword where the display kernel's `key_is_positional` says the leaf is keyworded (32 key fields of the shipped tree), and a key choice's value after its keyword (`upto`, `through`, `prefix-length-range`, `address-mask`). One regression test asserts both entry paths equal the writer's line.
- Remaining failure mode: the token loop still exists twice (writer and audit), so a future key rule taught to one is silently missed by the other; moving `_entry_key` into `display` waits until the live S-lane change on `dict_walker.py` and `display/__init__.py` merges. The audit does not resolve `KEY_ALIASES` on choice alternatives, as before.
- Non-goals: the writer, the reader and the tree.
