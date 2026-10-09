## Context

The CLI currently owns a lexical detector for conversion and audit, while the
top-level validation facade separately distinguishes set from structured. The
shared answer must sit below both surface modules without importing the
conversion or validation pipelines, and must preserve malformed-input parser
doors as well as successful classifications.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| `junoscfg.display.is_display_set` | Existing display-set recognition shared by both current detectors | Recognizes only set input | Repository-owned with characterization tests, checked 2026-10-09 | Reuse inside the shared classifier |
| `json` and `xml.etree.ElementTree` | Standard-library parse confirmation for JSON and XML | Does not parse YAML | Python standard library on the supported interpreter range, checked 2026-10-09 | Use JSON parsing for JSON/YAML precedence; retain the XML lexical door so malformed XML reaches its existing parser |
| PyYAML `safe_load` | Already-declared runtime dependency and parser used by YAML input | JSON is a YAML subset | PyYAML 6.0.3 locked in `uv.lock`, checked 2026-10-09 | Reuse after JSON parsing and accept only mapping/list documents |

## Decisions

- Put `detect_format()` in the `junoscfg.display` package door because display
  is the existing shared kernel and already owns `is_display_set()`.
- Require callers to pass an accepted-format set. Conversion and audit pass all
  five formats; validation passes only set and structured.
- For brace- or bracket-prefixed input, attempt JSON first and YAML second. A
  YAML mapping/list therefore fixes flow-style YAML while valid JSON retains
  its historical classification.
- Preserve the old parser door for malformed brace-prefixed and angle-prefixed
  input: return JSON or XML respectively so the owning parser still reports
  the syntax failure.
- Declare the improved YAML inference as a CLI behavior change and raise the
  minor version to 0.14.0; an explicit input format is the compatibility path.
- Accept YAML auto-detection only for parsed mappings or lists. Scalar YAML is
  left to the structured parser, matching the previous default.

## Risks

- PyYAML accepts a broad language; restricting inferred YAML to mappings and
  lists prevents ordinary structured tokens from becoming YAML scalars.
- Validation's narrow policy intentionally ignores JSON, XML, and YAML even
  when the classifier could recognize them under the full policy.
- Empty conversion and audit input already short-circuit in the CLI. The
  classifier itself raises a stable `ValueError` so direct callers do not get
  a meaningless structured guess.
