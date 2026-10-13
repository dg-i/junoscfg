# schema_content_worker — contract

Pure isolated operations for template-owned content evidence.

- Accept only the declared operation and captured input filename.
- Preserve Draft202012Validator.check_schema defaults and Lark(start="start").
- Import only stdlib and the operation's declared distribution closure.
- Read exact input bytes; do not read application state, mutate files, or publish receipts.
- Failure exits nonzero; no fallback or weaker checker.

Not for artifact generation, cache admission, or changing the schema dialect.
