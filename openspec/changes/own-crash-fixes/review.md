## Findings

Pending: independent Test/Challenge (fresh agent, Opus, no Builder reasoning, high risk
floor) on tests commit `5c513a9` against base `2d4904b`; fresh isolated Reviewer dispatched
by the coordinator after the full check.

## Specification challenges

### SC1: a leaf selected relative now writes its tags as a selected container's

- Artifact: the coordinator brief (owner request 2026-10-16: "Relative selections are out of
  scope: the archived change deliberately drops a tag on the selected statement itself when
  relative") and this change's first delta wording ("a relative selection ... unchanged by
  this one"), against the approved requirement `conversion/path-filtering` "A relative
  selection is written as absolute output writes it, without its path": "a tag on the
  selected statement itself is a bare command in set output (`deactivate`) and, in
  structured output, dropped with a note".
- Counterexample (executed): `set system host-name r1`, `deactivate system host-name`,
  `protect system host-name`, `--path system.host-name --relative -e set`. Base writes
  `set r1` (the tags silently dropped, as for the absolute selection); with the fix, which
  hands every writer the leaf's annotation, it writes `set r1`, `deactivate`, `protect`,
  as `--path system.syslog --relative` of a deactivated syslog already writes `deactivate`;
  structured writes `r1;` with the existing note "2 tag(s) of the selected statement itself
  dropped"; json, yaml and yaml-new write the value alone, unchanged. Device corpus
  (`probe_selections.py`, 2,875 relative selections): 2 relative outputs change, both set,
  `routing-options.forwarding-table.chained-composite-next-hop.ingress.l3vpn` (a deactivated
  flag) from `set` to `set`, `deactivate`.
- Violated invariant: base violates the approved relative requirement for leaves (a tag on
  the selected statement itself was dropped without the bare command or the note); the brief
  asks for relative output to stay as it is.
- User impact: a relative leaf selection loaded under `edit system host-name` was active at
  base; with the fix it is deactivated, as the configuration says. A script comparing the
  relative text of a tagged leaf sees new lines.
- Proposed correction: accept, and record the relative leaf behaviour in the path-filtering
  delta (done, scenario "A tagged leaf selected relative"). The alternative keeps base: the
  pipeline strips the selected key's annotation for a relative selection (about three lines
  in `junoscfg.convert.pipeline`), keeping an output the approved relative requirement calls
  wrong.
- Decision: Pending owner decision. Interim action, fixed by the approved relative
  requirement and needing no code of its own: the fix applies to relative selections too;
  pinned by `TestPathFiltering::test_a_relative_leaf_selection_writes_its_tags_as_a_container_does`.
