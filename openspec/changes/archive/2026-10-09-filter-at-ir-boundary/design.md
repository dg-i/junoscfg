## Context

The conversion pipeline owns the dict IR after parsing, anonymization, and
validation. Rendering currently happens before `convert_config()` delegates to
one of four output-specific filters. Existing public filter helpers must remain
during beta even though the main conversion path no longer needs them.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| `display.path_filter.filter_dict_by_path` | Navigates wrapped or unwrapped dicts, rebuilds paths, supports relative mode and missing paths | Was not exposed through the package door | Repository-owned, covered by `tests/test_display_filters.py`, checked 2026-10-09 | Reuse; expose through `junoscfg.display` and `tach.toml` |

## Decisions

- Filter after validation and anonymization so both continue to inspect the
  complete configuration and anonymization cannot leak an unvisited subtree.
- Let `from_dict()` optionally omit the JSON/YAML `configuration` wrapper so
  relative output needs no reparsing.
- Retain all format-specific filters as compatibility surfaces during beta.

## Risks

- JSON and YAML renderers normalize their input in place; the filtered IR is
  local to one pipeline call, so no caller-owned object is newly mutated.
- The pipeline signature gains optional keywords, but existing positional and
  keyword calls are unchanged.
