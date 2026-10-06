Remove `junoscfg schema makedoc`. The command imported a module that never existed, so every invocation failed; it is a declared `cli` surface break.
