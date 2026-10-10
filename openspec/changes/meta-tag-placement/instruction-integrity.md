<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Immutable platform constraints (harness, organisation policy) | every action; no credentials or operator data in output; confirmation before outward-facing or hard-to-reverse actions | 1 | yes | captures read, never copied; test-data values only; no push, tag or merge without the owner |
| Runtime and provider configuration (Claude Code, `claude-opus-5-5`, scratchpad, agent roster without the removed `junoscfg-*` definitions) | tools, isolated agents | 2 | yes | Test/Challenge and Reviewer run as fresh `general-purpose` agents given only frozen artefacts |
| Invoked skill `agent-ready-change` (`SKILL.md`, `batches.md`, phase files) | lanes, phases, batching, asking | 3 | yes | standard lane, type `bug`; stacked on change A (`xml-inactive-leaf`) |
| Repository `AGENTS.md`, `ARCHITECTURE.md` (evidence hierarchy, one-IR rule), `src/junoscfg/{display,convert,validate}/CONTRACT.md`, `docs/architecture/developer-guide.md` (`--regen-schema`, XSD-fix counts), `pyproject.toml` `[tool.template.*]` | house rules, zones, stage `beta`, named surfaces `consumer` and `cli` | 4 | yes | ask for a device artefact before inferring; patch bump; `SetConverter.to_set()` and `ConfigStore` collapse stay on the `consumer` surface |
| Owner instructions: `private_test_data/deactivate-fix-prompt.md` (change B: defects 1, 3, 4, 5; steps 1–4; out-of-scope list; tests; blast radius; report) and the owner's answers of 2026-10-10 (balanced; stacked; quick checks during, intensive tests and reviews for A and B together at the end) | this change | 5 | yes | as recorded in change A's preflight |
| Approved specifications and decisions: `openspec/specs/**` (`conversion/entry-keys` "kept whole", `conversion/raw-set-input`, `conversion/diagnostics`), `docs/decisions/*.md`; change A's new `conversion/meta-tags` | current promises | 6 | yes | phase 2 quotes any requirement this change contradicts; `raw-set-input` names the internal `replace` form that step 2 removes |
| Acceptance and contract tests under `tests/` | the oracle | 7 | yes | never weakened |
| Observed behaviour (scratchpad, test-data values) | defects 1–5 | 8 | yes | defect 1 reproduced: `inactive: route 0.0.0.0/0 apply-groups [ G_LOC G_DEF ];` gives two `could not be placed` diagnostics and `deactivate … apply-groups G_LOC`; `… next-hop 10.0.0.1;` silently deactivates `next-hop` |
| Device evidence `private_test_data/deactivate{,2,3,4,5}.txt`, XSD `private_test_data/schemas/23.2R2-S7.5_vmx.xsd` (and the shipped `25.2R2-S1.5_qfx5120.xsd`) | rule 1–3 of the prompt | evidence, above the schema model | yes | family is evidenced; see C1 for every other `homogeneous` node |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Prompt rule 3 "a `homogeneous` container never carries a tag" and "the same flags decide how the curly writer prints: `family inet {` for `homogeneous`" versus the XSD: `homogeneous` sits on 1,716 lists (`address` 97 kinds, `prefix-list`, `vlan`, …), 336 non-list containers and 14 leaves in the shipped dump. A tag on a list entry (`deactivate … family inet address 10.0.0.1/24`) is ordinary, so rule 3 cannot read "every `homogeneous` node". Besides `family` (145), the non-list containers are port-mirroring/analyzer `routing-instance`, `vlan`, `bridge-domain` (each with a `name` key), `tunnel encapsulation`, `domain-path-id`, `secondary`, `collector`, two ipsec-vpn address containers and `securid-server` | owner decision required | owner; question B1. Safe default: rule 3 and the `name child {` print apply to non-list `homogeneous` containers only; the tag refusal (defect 5) applies to `family` only, as the prompt says, until device evidence covers another container | B's spec waits for B1 |
| C2 | Prompt out-of-scope "`_apply_meta` ignoring a value after a leaf stays until device evidence says the CLI rejects it" versus `deactivate5.txt`, which shows the CLI rejects `deactivate policy-options community C1 members 64496:2` | owner decision required | owner; question B2. Safe default: record it as a follow-up; the evidence covers a leaf-list value, not a single leaf's value (`deactivate system host-name r1`) | none until answered |
| C3 | Owner memory (2026-10-09, identifier-key-fields): structured-output device shapes are cosmetic, output must load and mean the same, not copy the device layout; versus this prompt's writer step (decide collapse and tag placement from the print flags; device line shapes in the round-trip tests) | automatically resolved by precedence | Builder: the later, explicit owner instruction (this prompt) wins for this change; the round trips are the correctness oracle and the device line shapes are asserted where the prompt names them | blast radius measured and reported, not minimised |
| C4 | `oneliner` on 12,419 non-list nodes and 2,405 lists in the shipped dump versus the four lists `_fix_flat_entry_keys` sets today | automatically resolved by precedence | Builder: the prompt says carry the flags from the XSD; the corpus blast radius of the writer is measured and every class of changed line explained in the report | larger rendering change than four lists; reported |
| C5 | Multi-key entries: the prompt says check whether a `oneliner`/`oneliner-plus` list keyed by more than one field exists | automatically resolved by evidence | Builder: they exist (203 in the shipped dump): `policy-options … from route-filter` (`address` + match type), `as-path-neighbors` (`list-type`, `list-name`), `prefix-list-filter`, `nexthop-weight`; tests use `route-filter` | reader tests include a multi-key entry |
| C6 | `phases/0-preflight.md` "require a clean governed tree" and `batches.md` "merge a predecessor before implementation starts on a change that needs its code" versus owner answer 3 (stacked, reviews together at the end) | automatically resolved by precedence | Builder: B branches from A's head (`change/meta-tag-placement` from 60b32a6); the owner merges A, then B; each keeps its own full check and `review.md` | B's diff is reviewed against A's head |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Owner-confirmed preference: balanced (owner answer of 2026-10-10)
- Mandatory risk floor: high: cross-domain (schema-pipeline: `artifact_builder.py`, `xsd_fixes.py`; conversion: `set_input.py`, `dict_walker.py`, field validation; kernel: `set_converter.py`, `config_store.py`) and regenerated schema artifacts. Independent Test/Challenge work and a fresh Reviewer at least as capable as the Builder; one `--regen-schema` after the generator settles; `--schema` tier over every dump; the full check; the corpus blast radius.

## Owner decision batch

1. **B1, which `homogeneous` nodes rule 3 covers.** Evidence and safe default in C1. Device artefact, on a lab candidate with `rollback`: `set forwarding-options port-mirroring family inet output routing-instance R1 ip-address 10.0.0.1`; `show forwarding-options port-mirroring` (curly shape); `deactivate forwarding-options port-mirroring family inet output routing-instance` (accepted?); `deactivate forwarding-options port-mirroring family inet output routing-instance R1` (accepted?); after each accepted one `show forwarding-options port-mirroring` with `| display set`, `| display xml`. Control for the list case: `deactivate interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24` accepted, as expected.
2. **B2, set input's `deactivate … members <value>`.** Evidence and safe default in C2.
3. **B3, `protect:` on a one-line entry.** The prompt names it; the reader treats `protect:` like `inactive:` by the same rule. Device artefact: `set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1`; `protect routing-options static route 0.0.0.0/0`; `show routing-options static`, `| display set`, `| display xml`, `| display json`. Safe default: `protect:` placed as `inactive:` is.

## Delta log

<!-- Append later instructions or evidence and their consistency result. -->

- Initial preflight: C3–C6 resolved by precedence or evidence; C1 and C2 open, asked with B3 in one batch together with change A's outstanding D1 and D2.
