# Add the QFX JSON null probe as a synthetic device source

Commit the owner's QFX `[null]` probe as `synthetic/sources/json-null-probes.json.gz` so its four renderings can be captured and imported later.
Preserved behaviour: junoscfg runtime unchanged; every committed capture, the manifest and the existing sources re-import byte-identical.
Verification: re-import from private_test_data into a scratch copy, diff against the tree; a simulated capture imports; fresh lightweight review; canonical full.
Changelog: misc fragment naming the new device probe source.
Scope: the JSON source, importer support for a JSON source and a capture awaiting the device, the device-data README, change records and the patch release.
Exclusions: capturing on the device, editing known-differences.json, changing the JSON writer, pushing.
Approval: owner asked on 2026-10-16 to add the new probe cases to tests/data/device/synthetic for a later device update.
