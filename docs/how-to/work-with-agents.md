# Work with agents

Start with the onboarding skill and record the agreed ownership and review
policy in this repository. Read proposal, specs, tests, agent review and diff
in that order; accept the change only after its checks and acceptance criteria
are satisfied.

CODEOWNERS routes review; hosting settings make it mandatory. The generated
file combines owners for exact and nested overlaps, orders broad rules before
specific rules, and warns about overlaps. Complex wildcard or basename rules
can request extra reviewers. Review the warnings after changing ownership.

GitHub accepts any one listed owner when code-owner review is required. An
owner union does not require both zone and domain approval, and a tier comment
does not enforce an approval count. Configure protected branches or rulesets
with required pull requests, code-owner reviews, the agreed approval count and
restrictions on bypasses and direct pushes. For concurrence from separate
groups, use additional hosting rules or record an operator check.

On GitLab, protect the target branch and enable Code Owner approval
(Premium/Ultimate). Configure additional approval rules and disallow author
approval where the team policy requires independent reviewers. Restrict direct
pushes that could bypass merge requests.

The template verifies visible configuration and generated-file freshness. It
does not verify remote branch protection or approvals without a hosting
integration. The operator must check those settings and the actual reviews.

A team can require an independent human for red-zone changes. For one
maintainer, follow [solo review](solo-review.md) and document that exception.

References: [GitHub code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
[GitLab Code Owners](https://docs.gitlab.com/user/project/codeowners/).
