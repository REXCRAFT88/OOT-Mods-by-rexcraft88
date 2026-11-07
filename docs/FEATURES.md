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

Regeneration waits 1.25 seconds after exertion/guard, then restores 24 units/second. Exhausted melee stays available at half damage and a requested 0.75 animation rate; actual slower attack duration was measured in earlier stamina validation. Roll/jump/dodge/dash input is restricted when exhausted. The shared contextual jump/dodge input currently requires the 12-unit threshold even though accepted backflips/sidesteps cost 10/8. Manual guard is disabled by the stamina policy at zero in combat.

**Per-impact shield stamina cost and native guard-break/stagger are not connected yet.** Do not interpret the held drain or guard-pose policy as proof of a finished guard-break mechanic. Child Link, unusual equipment, bosses and transitions need more gameplay coverage. These limits are why Hero Mode is labeled Beta / Early Access.

## Without Stamina

Includes the same wheel, manual-shield/targeting policy, enemy balance/behavior tuning. It installs no stamina HUD, attack costs, fatigue, regeneration or stamina-based action limits.

## Manual Shield standalone

Installs only executable hooks for held guard, target toggle/cancel, scoped guard animation/state policy and the native shield-slot draw request. It contains no item wheel, stamina HUD/system, enemy stat/AI pack, PS5 artwork or controller profile. Use it by itself; Hero Mode already contains the corresponding shield implementation.

## Item Wheel standalone

Hold R/R1 to open the wheel, choose with the left stick and release to equip. Tap R/R1 cycles owned variants of the selected group without opening the wheel. The selected group has the outline/glow described above. Bow/arrow, bottle, spell and mask grouping uses the native available inventory.

This variant keeps the game's normal targeting, shielding, item-use and face-button behavior; it does not install Hero Mode's L/L1 target toggle or ZL/L2 manual-shield policy. It contains no stamina or enemy balance changes. Do not combine its executable/UI replacements with Hero Mode, which already includes the wheel.

On Lichii build-93, use the generated patched NUP to ensure the wheel's RomFS layout loads. The generated Add-on ZIP is for a loader with verified NUP RomFS override support. Seeing the mod in Add-ons does not establish that its layout was applied.
