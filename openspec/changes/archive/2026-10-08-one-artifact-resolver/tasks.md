## 1. Tests

- [x] 1.1 Precedence: argument, override, environment, bundle.
- [x] 1.2 Conversion honours the environment variable — the gap itself.
- [x] 1.3 Two directories keep separate trees in one process.
- [x] 1.4 The override is restored on exit and when the block raises.
- [x] 1.5 The validator resolves identically.
- [x] 1.6 Three seen to fail under mutation: hardcoding the path, reverting
  the cache to a singleton, and dropping the `finally`.

## 2. Implementation

- [x] 2.1 `resolve_artifacts_dir` and the per-directory cache in the kernel.
- [x] 2.2 `JunosValidator` delegates; `_default_artifacts_dir` removed.
- [x] 2.3 `artifacts_dir` context manager, closed on the click context.
- [x] 2.4 `tach.toml` expose list, which both enforcement gates demanded.

## 3. Verification

- [x] 3.1 The split demonstrated closed: `--artifacts` and the environment
  variable both switch validation, and conversion now resolves to the same
  directory where it previously loaded the bundled tree regardless.
- [x] 3.2 1,489 tests pass, from 1,479.
- [x] 3.3 `tach check` passes; no new cycles.
- [x] 3.4 The Ansible collection's 33 tests pass and its four filters produce
  output byte-identical to junoscfg 0.6.8.
- [x] 3.5 A first version used a setter instead of a context manager. 109
  conversion tests failed, because `CliRunner` runs the CLI in the test
  process and the override leaked into every later test. That is the same
  shape as the Ansible collection, which imports the library into a
  long-lived `ansible-playbook`. Two tests now pin the scoping.
