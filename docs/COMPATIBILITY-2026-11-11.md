# Compatibility update — November 11, 2026

## Choose one native package

| Package | Enemy tuning | Stamina | Wheel | Manual shield / target remap |
|---|---|---|---|---|
| Hero with Stamina beta.11 | Yes | Yes | Yes | Yes |
| Hero without Stamina beta.9 | Yes | No | Yes | Yes |
| Hero Core beta.1 | Yes | Yes | No | No — original game behavior |
| Wheel + Shield beta.1 | No | No | Yes | Yes |
| Item Wheel1.6 | No | No | Yes | No |
| Manual Shield1.7 | No | No | No | Yes |

These full native replacements are mutually exclusive. In particular, separate
Wheel and Shield addons both supply `exefs/main` and `exefs/subsdk1`. File
precedence selects one payload; it does not merge their hooks. Use the combined
**Wheel + Shield** package instead. Do not add the standalone packages to Hero.

Remove the previous native copy, then import the complete Prepared-Addon ZIP
in Configure Game > Add-Ons > Import Mod from ZIP on the original update131072
game. Do not import over an older patched NUP. No commands are required.

## Ultrawide and DualSense UI

Keep DualSense UI and the three43:18 ultrawide layers as separate visual mods.
Retain the native addon folder prefix `00-OOT` for resource-table priority.
Updated wheel variants use private runtime layout metadata and do not replace
the shared Common layout/texture archives. Shield-containing size tables keep
the External font allocation at least16384 bytes, preserving the tested
DualSense font's requirement alongside custom GameData/menu allocations.

Wheel1.4 and Shield1.5 wrote different IPS payloads at the same main padding
cave, overlapping the ultrawide HUD patch. Those old versions are unsupported
for this combination. Updated helpers reside in a separate private module.
NSO section/page extents and supplied PCHTXT records were checked; the loader's
offset_shift0x100 compensates for the NSO header rather than adding another
0x100 to the effective memory address.

## What was tested

Tests used the provided Fritchii5.8 binary (`oot-gather-fix-6e11fee517`), the
matching update131072 game, the installed DualSense UI font/texture addon and
the supplied43:18 aspect/HUD/HUD-edges patches. Fast GPU accuracy, async shaders
and muted audio were used; the release does not set emulator preferences.

- Full Hero beta.11 loaded with the visual combination.
- Wheel compatibility candidate loaded into Continue with the visual
  combination and no test fixture. Its renderer/input path was additionally
  checked in the combined candidate.
- Combined candidate loaded; the tester confirmed L1 targeting, held L2 shield
  and R1 wheel all work together with the visual combination.
- Hero Core loaded in the Stalfos fixture; the tester confirmed combat stamina
  and the original item/shield/target behavior work as expected.
- Standalone Shield compatibility candidate loaded into Continue with the
  visual combination and no test fixture, confirming the release-side table
  works without relying on a fixture's larger allocations.
- Static module/cave checks and native-controller/guard checks passed.

Hero without Stamina uses the same updated wheel/shield path plus its existing
enemy resources; it did not receive a separate full playthrough. Broad boss,
scene reload, ocarina, other equipment and other HUD/controller coverage remain
limited. Initial targeting can briefly move the shield before lowering it;
the experimental repeated-arm-animation suppression is not included.

## Test setup correction

The first full-inventory fixture had a higher-priority ResourceSizeTable that
could hide the DualSense font allocation when the native addon supplied no
size table. This caused misleading wheel load failures. The fixture now merges
the maximum existing allocation for every enabled addon's table. Fixture,
inventory and save files are never included in releases. Normal saves were
not modified. Shader caches remain persistent; moving between emulator builds
may still require one-time preparation of cached pipelines.

The four-preset difficulty selector, recovery-drop toggle and selectable wheel
bumper row are not in these releases. No new antivirus scan is claimed; use
the attached SHA256 files to identify the exact archives.
