`--path --relative` (and `convert_config(path=..., relative=True)`) now writes what the
absolute output writes at the path, without the path, in every format. Relative JSON and
`yaml-new` coerce a single leaf given as a list (`class: [super-user]`) and keep an
annotation's booleans (`--path system.@`); relative set and structured no longer print a
list name the schema hides (`set ge-0/0/0 ...` under `--path interfaces`, not
`set interface ge-0/0/0 ...`), and a selected list writes its entries' statements instead
of a Python repr or nothing; a selected leaf writes its value in structured output too. A
relative path whose value is `null` writes it instead of nothing, and a key holding a dot
(`class-of-service.classifiers.ieee-802.1`) can be selected. `junoscfg.convert.from_dict`
gains `below=`; `from_dict(value, wrap=False)` is unchanged.
