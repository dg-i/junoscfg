# Review

Fresh agent session, read-only, against `v0.6.32`, isolated in a throwaway
worktree.

## Confirmed exact

All four precedence steps — explicit argument, override, `JUNOSCFG_ARTIFACTS`,
bundle — with an empty environment string correctly falling through.
Conversion provably did **not** honour the variable before (`git show` of the
parent has `load_schema_tree()` with no parameter and a hardcoded path) and
does now. Two directories genuinely yield different trees in one process,
including from cache in both orders. The override is restored on normal exit,
on `sys.exit`, and on an exception. All three claimed mutations die.

## Findings

1. **The knob it introduced made a Python traceback reachable.** Point
   `--artifacts` or `JUNOSCFG_ARTIFACTS` at a directory with no structure tree
   and conversion crashes: `load_schema_tree` returns `None` by design and
   `set_input._merge_tokens` dereferences it immediately.
   `AttributeError: 'NoneType' object has no attribute 'get'`, on set→json,
   set→structured, set→yaml, conf→set and conf→json. Newly reachable: before
   this change the path was hardcoded, so `None` was impossible in an
   installed package. The record claims the opposite — `retires.md` lists a
   test for "a missing directory is None rather than a crash", true at the
   kernel boundary and false end to end. **Fixed in v0.7.0**: a directory the
   caller *chose* raises; only the bundled one answers `None`.
2. **The override still leaks across threads.** `_override_dir` is a module
   global, not a `ContextVar`: a worker thread sees another thread's override,
   and the exiting thread restores its own saved value over a concurrent one.
   Single-threaded scoping is solid — but the docstring's own justification is
   a long-lived `ansible-playbook`. `ContextVar` is the one-line fix.
   Recorded, not fixed.
3. **The schema-tree cache is unnormalised and unbounded.**
   `resolve_artifacts_dir` returns `Path(arg)` unresolved while `_BUNDLED_DIR`
   is resolved, so a relative and an absolute path to one directory produce
   two cache entries and two copies of a 13.8 MB tree. Nothing evicts.
4. **Honest about the remaining smell, silent about deepening it.** The
   proposal says plainly that the kernel still reads a sibling layer's
   directory by path — disclosure `tach` cannot force, since it checks imports
   and not filesystem paths. But the change *promoted* that path from an
   internal constant to the documented final fallback of a newly exported
   public API, and neither record nor `display/CONTRACT.md` says so.
5. `codemap.md` is a pre-implementation snapshot: zero mentions of
   `resolve_artifacts_dir` or `artifacts_dir`.

## Resolution

The central claim is true and well tested, and the context-manager-over-setter
decision was right. Finding 1 was a blocker — a documented knob that produced
a traceback, in the same batch as a change whose whole purpose was removing
tracebacks — and is fixed. 2, 3, 4 and 5 are recorded and left.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.
