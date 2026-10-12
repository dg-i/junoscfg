# XML work TODO

**XML input and output are BUGGY; XML work is deferred.** The current makeover
completes non-XML work without qualifying either XML surface. XML input remains
available; XML output is not implemented and raises `NotImplementedError`.
This status does not mean that every XML operation fails.

Existing APIs and tests remain in place. Passing XML controls alone do not
establish complete XML correctness.

## Deferred work

- [ ] Correct XML input and its common intermediate representation using bounded
  device evidence, including names, metadata and context-dependent aliases.
- [ ] Implement XML output after reconciling the accepted scope decision and
  import ban, reviewing the design, and adding device-backed acceptance checks.
- [ ] Qualify XML alongside every captured device format.
- [ ] Qualify full-capture XML intermediate representations and reader/writer
  loops with configuration equivalence and negative controls.
- [ ] Record additional observed XML defects with their exact input, result and
  evidence; distinguish executed failures from proposed probes.

The output work must first reconcile the
[accepted compatibility scope decision](../decisions/2026-10-09-scope-compatibility-to-production-consumer.md)
and the [current architecture](../../ARCHITECTURE.md). Do not remove their
constraints through a documentation edit.
