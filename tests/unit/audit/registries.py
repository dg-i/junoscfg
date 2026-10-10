"""Small inline registries for the audit engine tests.

Not a conftest: test modules import these names, and a conftest imported as a
module is loaded twice.
"""

from __future__ import annotations

from junoscfg.audit import Registry, TypeEntry


def make_registry(*entries: TypeEntry) -> Registry:
    """A registry of exactly *entries*, in the order given."""
    return Registry(types={entry.name: entry for entry in entries})


POLICY_STATEMENT = TypeEntry(
    name="policy-statement",
    source="curated",
    definition=(("policy-options", "policy-statement"),),
    reference_schema_types=frozenset({"policy-algebra"}),
)

PREFIX_LIST = TypeEntry(
    name="prefix-list",
    source="curated",
    definition=(("policy-options", "prefix-list"),),
    reference_paths=(("from", "prefix-list"),),
)

CONFIG_GROUP = TypeEntry(
    name="config-group",
    source="curated",
    definition=(("groups", "group"),),
    reference_paths=(("apply-groups",), ("apply-groups-except",)),
    implicit=("re0", "re1", "global", "node*", "member*", "fabric*"),
)

# Namespace-only entry (report: false) that anchors collision classification.
AS_PATH_NAMESPACE = TypeEntry(
    name="as-path",
    source="curated",
    definition=(("policy-options", "as-path"),),
    report=False,
)
