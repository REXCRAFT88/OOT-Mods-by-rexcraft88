# Regression update — November 9, 2026

Current packages: Hero with Stamina beta.11; Hero without Stamina beta.8;
Manual Shield0.1.6; Item Wheel0.1.5. Both Hero packages remain Beta/Early Access.

Install the complete Prepared-Addon ZIP through Configure Game > Add-Ons >
Import Mod from ZIP on the original, unmodified update131072 game. Remove the
previous native package. Hero includes wheel and shield: install only one.
Keep the custom subsdk1 and applicable IPS sidecar together with main. No CMD
or Python is required. No game NUP, emulator or test save is included.

## Changes

- Helpers now live in a private module rather than the alignment space also
  used by the supplied ultrawide patches. Original main text extent and other
  native modules are preserved. A reported ocarina crash landed directly in
  the former overlapping helper region.
- Wheel rebinding clears cached widgets even when a reload reuses a list
  address; incomplete binding blocks draw/selection. Variant taps update
  native focus as well as equipment. Both sticks select equally; the default
  wheel uses only the right bumper.
- Shield guard uses the actual native carry state and avoids concrete busy
  tool actions. Holding the shield button during carrying no longer requests
  the shield attachment. Two-handed equipment exclusions remain.
- Combat stamina refreshes nearby enemies on attack entry instead of waiting
  for the periodic cache; drops and collectible Gold Skulltulas are excluded.
  Native combat-music detection remains, with a12-unit proximity fallback.
- The experimental native equip suppression caused repeated arm motion and
  was removed. Native equipment requests can finish as in beta10. Initial
  targeting may still briefly move the shield before lowering it.

## Evidence and remaining limits

The tester confirmed held L2, carry/pickup protection, filled-bottle cycling,
right-stick navigation, L1 target-only behavior and menu tabs during this pass.
Exact published beta10 was also used as a baseline for the arm-animation
regression. Compiled policy/ABI checks and static supplied-ultrawide overlap
checks passed. The final packaging removes unused diagnostics and stock
modules that do not need overriding.

These checks do not establish every reported issue fixed. Ocarina play/exit and
free movement, full ultrawide/FPS gameplay, repeated scene/save reloads, all
carry/ranged states, spell/mask variants and Young Link enemy/NPC stamina still
need broader live testing. Other full controllers use logical mappings, but
the reporter's PowerA/Xbox setup was not physically verified. Another mod
replacing the same Bootup/GameData/message/resource-size files or subsdk1 may
still conflict. Keep HUD mods separate; retain the 00-OOT folder priority.

No new antivirus scan is claimed for these archives. Published SHA256 files
identify the exact downloads. Earlier scan reports apply only to their dated
files and are not a certification of these new packages.

Wheel bumper selection, Hero difficulty presets and the heart/magic-drop
option are follow-up features, not included in this regression release.
