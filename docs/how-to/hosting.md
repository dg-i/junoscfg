<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Hosting: what makes a review mandatory

CODEOWNERS routes review. Nothing in this repository makes a review happen:
that is the hosting platform's setting, and this page is what the template
knows about it. The agreed ownership and review policy for this repository is
in [work with agents](work-with-agents.md); this is the platform behaviour
underneath it, and it is the template's to correct as the platforms change.

## What the generated CODEOWNERS does

`uv run --locked --group dev agent-ready render codeowners` writes the file from `[tool.template.zones]`,
`[tool.template.domains]` and `[tool.template.stage]`. Exact paths union their
owners; nested paths run broad to specific and keep the broader owners;
complex wildcard and basename rules may route extra owners, and the generated
file carries a warning where it detects an overlap. Read those warnings after
changing ownership.

A zone's tier is not an approval count. It is what a mistake there would cost,
and it selects the review policy a human agreed; the file routes, and the
platform enforces.

## GitHub

Required code-owner review is satisfied by any one listed owner. An owner
union therefore does not require both the zone's owners and the domain's
owners to approve — it widens who may approve, not how many must. Where
concurrence from separate groups is the policy, add hosting rules that say so,
or record an operator check; the CODEOWNERS file cannot express it.

Configure protected branches or a ruleset with required pull requests,
required code-owner review, the agreed approval count, and restrictions on
bypasses and direct pushes. GitHub forbids self-approval, which is what makes
a CODEOWNERS review a second human rather than a field the author sets.

## GitLab

Protect the target branch and enable Code Owner approval, which needs Premium
or Ultimate. Add approval rules for the agreed count, disallow author approval
where the policy requires an independent reviewer, and restrict direct pushes
that would bypass merge requests.

## What CI cannot verify

The shipped checks verify what is visible in the repository: that CODEOWNERS
is current with the tables it is generated from, and that the workflow files
are in place. Remote branch protection, approval rules and the reviews that
actually happened are not visible to a check without a hosting integration.
An operator confirms those settings, and a claim that they hold belongs in a
decision record rather than in a check's silence.

Where the remote is a directory rather than a hosting platform, there is no CI
and no code-owner review at all: the hooks are the whole enforcement, and
approval is the human's commit.

References:
[GitHub code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
[GitLab Code Owners](https://docs.gitlab.com/user/project/codeowners/).
