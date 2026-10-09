Centralize automatic configuration format detection with explicit conversion,
validation, and audit policies, including flow-style YAML recognition. This
CLI behavior change is released as version 0.14.0; use an explicit input format
to retain lexical classification. Set-mode detection now covers `protect` and
`activate` as well as `set`, `deactivate`, and `delete`.
