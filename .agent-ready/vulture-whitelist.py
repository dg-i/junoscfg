# Vulture whitelist. Regenerate with:
#   vulture src --make-whitelist > .agent-ready/vulture-whitelist.py
#
# Why each entry is here, so a future reader does not take the file as a licence:
#
# - The twenty `_convert_*_to_*` functions in __init__.py are reached through
#   the _CONVERTERS dict by name, never by a literal call. Vulture reads calls.
# - `fullhelp` is a click command registered by its decorator.
# - `types_audited`, `category`, `description` and `applies_to` are dataclass
#   fields read by the test suite, which vulture does not scan.
# - `json_to_yaml` and `build_from_xsd` are public API exercised by tests only.
# - `ConfigStore.subtree` is genuinely unreferenced. It is public and appears in
#   docs/api/internals/config_store.md, so removing it is an API change with a
#   docs edit, not a phase 4 edit. Carried forward as its own change.
#
# Three genuinely dead private members were removed rather than whitelisted in
# phase 4: CommunityRule._counter, SetWalkOutput.meta_lines, _add_sibling.
_convert_json_to_set  # unused function (src/junoscfg/__init__.py:186)
_convert_json_to_structured  # unused function (src/junoscfg/__init__.py:198)
_convert_json_to_yaml  # unused function (src/junoscfg/__init__.py:210)
_convert_json_to_set  # unused function (src/junoscfg/__init__.py:186)
_convert_json_to_structured  # unused function (src/junoscfg/__init__.py:198)
_convert_json_to_yaml  # unused function (src/junoscfg/__init__.py:210)
_convert_xml_to_set  # unused function (src/junoscfg/__init__.py:222)
_convert_xml_to_structured  # unused function (src/junoscfg/__init__.py:234)
_convert_xml_to_yaml  # unused function (src/junoscfg/__init__.py:246)
_convert_yaml_to_set  # unused function (src/junoscfg/__init__.py:258)
_convert_yaml_to_structured  # unused function (src/junoscfg/__init__.py:270)
_convert_yaml_to_json  # unused function (src/junoscfg/__init__.py:282)
_convert_xml_to_json  # unused function (src/junoscfg/__init__.py:294)
_convert_set_to_structured  # unused function (src/junoscfg/__init__.py:306)
_convert_set_to_json  # unused function (src/junoscfg/__init__.py:318)
_convert_set_to_yaml  # unused function (src/junoscfg/__init__.py:330)
_convert_structured_to_json  # unused function (src/junoscfg/__init__.py:342)
_convert_structured_to_yaml  # unused function (src/junoscfg/__init__.py:354)
_convert_structured_to_set  # unused function (src/junoscfg/__init__.py:366)
_convert_json_to_json  # unused function (src/junoscfg/__init__.py:378)
_convert_set_to_set  # unused function (src/junoscfg/__init__.py:390)
_convert_yaml_to_yaml  # unused function (src/junoscfg/__init__.py:402)
_convert_structured_to_structured  # unused function (src/junoscfg/__init__.py:414)
types_audited  # unused variable (src/junoscfg/audit/model.py:87)
fullhelp  # unused function (src/junoscfg/cli.py:908)
_.meta_lines  # unused attribute (src/junoscfg/convert/output/set_output.py:19)
_.subtree  # unused method (src/junoscfg/display/config_store.py:335)
json_to_yaml  # unused function (src/junoscfg/display/to_yaml.py:19)
_.build_from_xsd  # unused method (src/junoscfg/validate/artifact_builder.py:84)
category  # unused variable (src/junoscfg/validate/xsd_fixes.py:24)
description  # unused variable (src/junoscfg/validate/xsd_fixes.py:25)
applies_to  # unused variable (src/junoscfg/validate/xsd_fixes.py:26)
