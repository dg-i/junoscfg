## Why

Field validation compiles schema patterns as written, so a POSIX bracket expression holding a literal `[` (shipped `_patterns` #49 and #83, `[[[:alnum:]]*...`) reaches `re.compile` as `[[a-zA-Z0-9]` and prints `FutureWarning: Possible nested set` on every validated conversion (DEV-V5 = NEW-A4, PROC-F1).

## What Changes

- `convert/field_validator.py` `_posix_to_python_re` translates each bracket expression as a unit: a POSIX class becomes its ranges and a literal `[` is escaped; escapes and the text outside brackets pass through. Every shipped pattern keeps its `re` program (0 of 263 differ); two unshipped shapes change: an unterminated `^[[:alpha:]$` now compiles instead of never matching, and a bare `[:alpha:]` outside brackets is now a set, as in POSIX. One regression test asserts that shape compiles with no warning.
- Remaining failure mode: other POSIX-only spellings (a literal `\`, `[.x.]`, `[=x=]`, an unterminated bracket) and Python's set-operation pairs `&&`, `--`, `||`, `~~` and unknown class names still reach `re` in Python's dialect, the latter two warning; none is shipped today (all 263 patterns of `load_schema_tree()["_patterns"]` compile warning-free after the fix).
- Non-goals: the schema artefacts and their generators (patterns stay as the XSD writes them); a general POSIX ERE translator.
