"""Include/exclude path matching for anonymization scope control."""

from __future__ import annotations

from fnmatch import fnmatch


class PathFilter:
    """Decides whether a schema path is in scope for anonymization.

    Uses the same dot-separated path syntax as the edityaml path_walker,
    with glob matching on individual segments.

    Rules:
    - If *include* is non-empty, a path must match at least one include pattern
      (or be a prefix of one) to be processed.
    - If *exclude* is non-empty, a path matching any exclude pattern is skipped.
    - Exclude takes precedence over include.
    - If both are empty, all paths are in scope.
    """

    def __init__(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> None:
        self._include = [p.split(".") for p in (include or [])]
        self._exclude = [p.split(".") for p in (exclude or [])]

    def matches(self, path: list[str]) -> bool:
        """Return True if *path* is in scope for anonymization."""
        if self._exclude and self._matches_any(path, self._exclude):
            return False
        if self._include:
            return self._matches_any_or_prefix(path, self._include)
        return True

    @staticmethod
    def _matches_any(path: list[str], patterns: list[list[str]]) -> bool:
        """Return True if *path* matches any pattern (exact or path is under pattern)."""
        return any(_path_matches(path, pattern) for pattern in patterns)

    @staticmethod
    def _matches_any_or_prefix(path: list[str], patterns: list[list[str]]) -> bool:
        """Return True if *path* matches, or is a descendant/ancestor of, any pattern."""
        return any(
            _path_matches(path, pattern) or _is_prefix(path, pattern) for pattern in patterns
        )


def _path_matches(path: list[str], pattern: list[str]) -> bool:
    """Return True if *path* starts with *pattern* (each segment glob-matched)."""
    if len(path) < len(pattern):
        return False
    return all(fnmatch(p_seg, pat_seg) for p_seg, pat_seg in zip(path, pattern, strict=False))


def _is_prefix(path: list[str], pattern: list[str]) -> bool:
    """Return True if *path* is a proper prefix of *pattern*.

    This ensures that containers above an included path are still walked.
    """
    if len(path) >= len(pattern):
        return False
    return all(fnmatch(p_seg, pat_seg) for p_seg, pat_seg in zip(path, pattern, strict=False))
