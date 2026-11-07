# Changes and controls

## Hero Mode and Manual Shield controller labels

Map your pad to a normal Switch Pro Controller in the emulator. The mod uses logical inputs, not a Sony device ID.

| Action | Switch Pro | PlayStation equivalent | Xbox equivalent |
| --- | --- | --- | --- |
| Hold shield | ZL | L2 | LT |
| Toggle targeting | L | L1 | LB |
| Hold wheel / tap variants (Hero Mode) | R | R1 | RB |
| Use selected item | ZR | R2 | RT |
| Reset camera / cancel toggle target | Right-stick click | R3 | RS click |

Face-button actions retain the game's mappings. No PS5 face-button remap, replacement button art, L3 sprint, separate Circle roll/Cross jump, contextual Square put-away, or controller-settings menu is included. The manual shield uses the game's native target/guard locomotion path: guard can align the camera and participate in native target selection. Fully independent guard camera/target selection remains an area for refinement.

The standalone shield was confirmed working by the tester on the running DualSense/Lichii setup. Final L1 exclusivity and moving shield with sword sheathed were also confirmed in both target states. Other full Pro-controller-style pads are expected to work when mapped to the same logical inputs, but Xbox, physical Switch Pro, split Joy-Con and handheld paths have not all been tested. Draw a weapon using the game's normal draw/attack control if the current action prevents the shield drawing. Only the shield slot is requested once on guard entry; the hook does not request drawing the sword.

## Both Hero Mode betas

- **Item wheel:** hold R to open, choose with the left stick, release to equip. Tap R cycles variants without opening the wheel. The selected item has a bright outline/glow. Native inventory/age usability filtering is retained; the layout groups related bow/arrow, bottle and spell entries. Arrow cycle: normal, fire, ice, light, then normal; selecting the bow starts at normal arrows. Bottles and spell groups cycle their owned/usable variants. Wheel size follows the available groups.
- **Manual guard:** hold ZL, release to lower. L toggles targeting; right-stick click cancels it. Target toggle alone is routed through the guard-off policy; guard uses stock locomotion/animation execution rather than swapping walking animation names.
- **Enemy balance:** positive enemy maximum HP becomes `ceil(stock * 1.5)`; enemy damage fields become 2x stock. Examples: 9 HP -> 14, 18 HP -> 27. Includes 174 packs / 188 distinct stat resources, boss variants and dedicated projectile actors where positive stats exist. Zero damage and special invulnerability rules stay intact. Environmental damage is not globally doubled. Per-boss/projectile runtime coverage is incomplete.
- **Wolfos tuning:** first slash wind-up remains stock speed; follow-up attacks use 2x animation speed. The rear-exposure branch is bypassed and the slip branch no longer requests its original turn. Existing Wolfos/Stalfos counter and interval tuning is retained. These changes are not a guarantee that every turn animation disappears.

The requested extra save slots, random double/flaming scrub/Octorok seeds, guaranteed first-hit Wolfos guard break, complete enemy redesign and in-game settings switches are not implemented in these releases.

## With Stamina only

A separate yellow stamina bar sits beneath the green magic bar. Combat is detected by nearby enemy actors (about 25 world units), with a five-second grace after threats disappear; it is a coarse proximity check, not line of sight.

Permanent maximum hearts increase capacity (20 units per heart). Lower current health increases drain rather than shrinking the maximum. Stamina is unrestricted outside combat. Walking remains available when exhausted and permits regeneration.

| Action | Full-health default cost |
| --- | --- |
| Master Sword slash / stab / jump attack / spin | 12 / 13.2 / 18 / 21.6 |
| Kokiri / Biggoron / hammer base melee | 8 / 18 / 20 |
| Move multipliers: slash / stab / jump attack / spin | 1 / 1.1 / 1.5 / 1.8 |
| Roll or ordinary jump | 12 |
| Backflip / sidestep | 10 / 8 |
| Held shield | 2 units per second |
| Successful native shield-block reaction | 8 before injury scaling |

Regeneration waits 1.25 seconds after exertion/guard, then restores 24 units/second. Exhausted melee stays available at half damage and a requested 0.75 animation rate; actual slower attack duration was measured in earlier stamina validation. Roll/jump/dodge/dash input is restricted when exhausted. The shared contextual jump/dodge input currently requires the 12-unit threshold even though accepted backflips/sidesteps cost 10/8. Manual guard is disabled by the stamina policy at zero in combat.

**Successful native shield-block reactions cost 8 stamina before injury scaling.** One deduction occurs on the native guard-reaction entry, separately from the 2/second held drain. No impact cost is charged outside combat. Native zero-stamina guard-break/stagger is still not connected. Do not interpret the held drain or guard-pose policy as proof of a finished guard-break mechanic. Child Link, unusual equipment, bosses and transitions need more gameplay coverage. These limits are why Hero Mode is labeled Beta / Early Access.

## Without Stamina

Includes the same wheel, manual-shield/targeting policy, enemy balance/behavior tuning. It installs no stamina HUD, attack costs, fatigue, regeneration or stamina-based action limits.

## Manual Shield standalone

Installs only executable hooks for held guard, target toggle/cancel, scoped guard animation/state policy and the native shield-slot draw request. It contains no item wheel, stamina HUD/system, enemy stat/AI pack, PS5 artwork or controller profile. Use it by itself; Hero Mode already contains the corresponding shield implementation.

## Item Wheel standalone

Hold R/R1 to open the wheel, choose with the left stick and release to equip. Tap R/R1 cycles owned variants of the selected group without opening the wheel. The selected group has the outline/glow described above. Bow/arrow, bottle, spell and mask grouping uses the native available inventory.

This variant keeps the game's normal targeting, shielding, item-use and face-button behavior; it does not install Hero Mode's L/L1 target toggle or ZL/L2 manual-shield policy. It contains no stamina or enemy balance changes. Do not combine its executable/UI replacements with Hero Mode, which already includes the wheel.

Use the prepared Add-on ZIP on Lichii build95 (release tag build-94), which fixes NUP RomFS overrides. Build93 needs the optional patched-NUP fallback for the complete wheel layout.

## Compatibility update

Hero Mode with Stamina Beta4 relocates its native code out of the known Dynamic FPS and 3440x1440 ultrawide code areas. The installed Dynamic-fps IPS and Ultrawide 21x9 (3440x1440) IPS were checked for byte overlap; both were enabled in the live build95 check. This does not promise compatibility with every FPS, aspect-ratio or UI mod. Two mods replacing the same RomFS archive still need a merged resource; use one Hero/standalone native package at a time.

All four updated variants pass shoulder inputs through in paused menus. Wheel variants additionally bypass their R/R1 tap/hold filter during the native ocarina action. Compiled passthrough checks pass; a live ocarina check on a normal progressed save is still pending because the synthetic development save cannot activate the instrument even in a peaceful area. Existing game saves are not modified.

## Slow-motion timing repair

The earlier compatibility packages extended main's NSO text size into padding. Lichii therefore rejected its built-in Dynamic FPS cave as part of the executable text, even when no byte overlap remained. That could leave a decent presentation FPS with slow game simulation. Current packages preserve the original text size0x3c461d0 and supply only our separate cave at0x3c46600 through a build-ID-matched IPS sidecar. Lichii can then apply its own FPS routine at0x3c46200. The sidecar does not bundle or enable an FPS fix; enable the built-in fix or the checked standalone alternative. Install through Add-ons using the original NUP.

## Configurable stamina (Beta6)

Hero Mode with Stamina now has a configuration block for capacity, regeneration, delay, action/shield costs and HUD offsets. Default balance remains the same, with the yellow gauge moved24 layout units upward toward magic. Ready-to-import125% and150% capacity presets and an optional Python settings tool are available; there is no in-game settings screen yet. The meter's visual length remains tied to permanent hearts when capacity is boosted. See [Stamina settings](STAMINA-SETTINGS.md).
