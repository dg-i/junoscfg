## Context

`find_non_json_value` (kernel, `src/junoscfg/input.py`) is the one check the yaml-new reader
(`junos_yaml_to_dict`), writer (`dict_to_junos_yaml`) and validation
(`JsonYamlValidator.validate_yaml_as_json`) share. It visits each mapping and list once and
reports one met again as `alias`. PyYAML's `safe_load` keeps an alias as the same Python
object and builds a cycle as a cyclic object, in time linear in the text. The writer checks
only the finished document, after `junos_json_object` and `_unshared` have walked the IR.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| `find_non_json_value` and `_unshared` (this repository) | kinds, paths, the shared walk; writing a shared object out | treats sharing as a refusal; `_unshared` has no bound | in-tree, 2026-10-15 | Extend the check; move `_unshared` to `junoscfg.convert.ir` as `unshared`, beside `wrap_configuration`, used by reader and object stage |
| Standard library (`copy.deepcopy`, `json` round trip) | copying | `deepcopy` keeps sharing (memo); a JSON text round trip expands without any bound and re-parses text, which the architecture forbids for yaml-new | stdlib | Reject |
| PyYAML alias limits / another YAML library | none in PyYAML 6 (no alias or expansion limit); ruamel.yaml is not a dependency | a new dependency for one check | not looked up online (no web access in this session) | Reject |

## Decisions

1. **Rule.** A mapping or list reached again is a copy (expanded); one reached inside itself
   is refused as `cycle` at the path where it is reached again (tracked by the set of open
   containers on the walk).
2. **Bound (SC-2, interim).** Count the parsed document: each mapping and list once, plus the
   scalars it holds. The expanded walk may visit at most twice that many values; the visit
   past it refuses the outermost alias being written out (kind `alias`) at its path. Why two:
   every value reached at most twice passes (the owner's "reached twice"), and the walk, the
   copy and every later stage stay within twice the parsed size: linear, as the interim rule
   was. A document without aliases visits exactly its parsed size and never reaches it.
   Alternatives (a fixed node count, go-yaml's alias ratio, SnakeYAML's 50 collection aliases)
   need a number the owner did not state, or still allow exponential growth (a fixed alias
   count with nesting). Strictly, a block reached twice needs only 2P-1 (the root is reached
   once); 2P is the simpler statement and the difference is one value.
2a. **Depth bound (SC-A, interim, from Test/Challenge TC3).** A walk of the written-out
   document may not go deeper than the parsed document's deepest value, an alias counted as
   a leaf as in the text; past it the outermost alias is refused (`alias`, "nests the
   document deeper than it is written"). Without it a 17 KB alias chain nests 1,200 deep
   within the size bound and every recursive stage raises `RecursionError`. With it no stage
   meets a depth an alias-free document of the same text could not hold, and no number is
   needed. The counting pass is iterative, in document order, so an anchor is met before its
   aliases as in the text.
3. **API.** `find_non_json_value(data) -> NonJsonValue | None`, `NonJsonValue(kind, path,
   reason)` a `NamedTuple` exported from `junoscfg.input` (tach expose gains it). `reason` is
   "has no JSON spelling" or "expands the document past twice its size", so every door says
   the same thing: reader `Invalid input: a YAML {kind} {where} {reason}`, writer `Cannot
   write yaml-new: the {kind} {where} {reason}`, validation `YAML {kind} {reason}`. The old
   trailing hints go (they misdescribe a cycle or a bound).
4. **Doors.** Reader: check, then `unshared(data)` to the JSON object stage, so the IR never
   shares (later stages mutate per schema context). Writer: check the IR (wrapped as the
   output will be, for paths) before `junos_json_object`, which now copies with `unshared`
   instead of `deepcopy`, so a shared IR is written out the same in `json` and `yaml-new`
   and the YAML dumper meets no shared object (no anchor). Validation: check, then validate
   the loaded object (read-only, bounded).
5. **Walk.** Two passes: an iterative count of values and deepest depth (each container
   once, document order; ends on cycles), then the recursive expanded walk in which only
   visits inside a copy spend a budget of the parsed size (the rest of the walk visits
   exactly that many, so the total stays within twice) and only they meet the depth
   ceiling, so a refusal is always met inside a copy and names its outermost alias
   (Reviewer R1), building paths on return as today. The walk recurses no
   deeper than the parsed document, which PyYAML's own recursive composer already built.

## Risks

- The bound refuses heavy reuse of a block in a small file (a three-value block reached four
  times in a file of only that block). Interim, reported; loosening is additive.
- Recursion depth: alias chains reach any depth (Test/Challenge TC3), hence the depth bound;
  a document whose text nests past the recursion limit fails in PyYAML's composer first.
- Linear in the loaded object, not the text: scalar aliases and merge keys are expanded by
  PyYAML while loading (TC6, SC-B, pre-existing).
- The depth bound refuses a block defined shallow and aliased deeper than anything else in
  the file (SC-A); the size bound counts written-out values, so nested anchors each aliased
  once can be refused by it (SC-C).
- Merge keys (`<<: *a`) are resolved by PyYAML at load as a shallow copy of keys; a container
  value they copy is shared and now written out (refused at base); a merge chain costs
  quadratic time in PyYAML itself (pre-existing, unchanged).
- Legacy `yaml` input keeps its cycle recursion and bomb expansion (C5, out of the ruling).
