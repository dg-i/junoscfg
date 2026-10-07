- minimise the exported surface from observed usage: unchanged. No name is
  added or removed; `requires-python` widens, which admits callers rather than
  excluding them.
- the deprecation policy, stated: not engaged. Widening a supported range is
  backwards compatible, so no surface break is declared and no deprecation is
  owed. Anonymizer output does change on 3.10 to 3.12, and real callers can
  observe it: v0.5.0 to v0.5.11 shipped `>=3.10` with the crypt branch, and the
  Ansible collection pins `junoscfg>=0.5.8`. A glibc host previously got a
  libc-dependent hash and now gets a deterministic one of the same length.
  That is a bug fix, not a surface break.
