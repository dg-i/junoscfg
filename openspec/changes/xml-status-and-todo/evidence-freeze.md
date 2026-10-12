## Resolved instructions

Committed instruction-integrity and proposal; owner unattended approvals and
latest XML deferral apply. Roadmap home approved by root; no MkDocs edits.

## Requirements

Documentation-only status and bounded TODO; no behavioral requirements change.

## Evidence

Source inspection at base e293b72564ef579a393102e4578f253efa8bdc8f:
- `README.md`: SHA256 `ec8629daa4b898b94109b50e050a12b1501e43bd5743d195288f9a4c9289465f`
- `mkdocs.yml`: SHA256 `282520e3cd5e1cecf0ca4f44ec5246a4645c064e2974ab6d97c6f997124730a3`
- `ARCHITECTURE.md`: SHA256 `b59acd798ca321e08cdc7b97c2821b27e816d67e7793a24e5182a66826377c5a`
- `src/junoscfg/__init__.py`: SHA256 `8d983fb27b41696483022492500f18666792a1e2c7f90292a1ed80d77410a6ed`
- `src/junoscfg/convert/CONTRACT.md`: SHA256 `5caff337f26088699bd67fd76b87bd21e67a31feec5ee7f3eefa7c3b9f6cd0cb`
- `src/junoscfg/convert/input/xml_input.py`: SHA256 `34af3907960ef56bfdae78a29c540875891b216ac7bfa8776970c5bf3adf6f8e`
- `docs/decisions/2026-10-09-scope-compatibility-to-production-consumer.md`: SHA256 `fd3813fe672a01f83987c950edcc822ed6cbd52f3866e110425c7c1c3d0d2af3`
- `pyproject.toml`: SHA256 `7e83a8938b9d7f9e16e8f99da4531459e2b6bf9c8a0cb61ad4ad3c5264c958b4`

## Non-goals

Preserve APIs, tests and behavior; no XML repair or output implementation.
Do not reverse the accepted XML retirement decision in a documentation change.

## Acceptance criteria

All docs-plan checks pass; public wording accurately distinguishes buggy input
qualification from unimplemented output. No blanket skip or weakened assertion.

## Performance expectations

None: no runtime or toolchain behavior changes.

## Outstanding decisions

None. Required execution permission is root-owned activation, not scope approval.

## Execution and checkpoint

- Assurance preference: economy.
- Risk floor: normal; documents only, no named behavior change.
- Roles required: continuous Builder and economical Finalizer; TC and fresh Reviewer omitted by policy. Root may perform bounded review.
- Resume point: phase 4 QA design; intent commit c6f4ad4.

## Delta log

- Freeze established: docs-plan and hashes above; no changed technical behavior.

- Root preserved/rebased onto activation-only BASE `6a956c1dbf31e7c6f32b7d2bb214a629f9db3951`; all ten owned paths retained byte-for-byte. No runtime or documentation source changed. Initial readiness on old activation failed and is not proof. Root admitted native docs-only full after confirming zero expensive tiers and no application adapter. Resume current-head QA/readiness/full.
