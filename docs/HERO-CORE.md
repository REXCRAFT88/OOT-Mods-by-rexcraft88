# Hero Core — Beta / Early Access

Hero Core keeps Hero's existing enemy tuning and combat stamina, with the
game's original item selector, shield behavior and controller mappings.
It does not install the item wheel, manual-shield policy, L1 target remap,
custom target/shield menu rows, or the experimental equipment suppressors.

- Existing enemy/projectile damage tuning and positive enemy health scaling
  remain (2x damage and rounded-up1.5x health, plus current Wolfos/Stalfos work).
- Yellow half-height combat stamina remains, including the current heart-based
  capacity, injury drain multiplier, weapon/action costs and regeneration.
- Exhausted melee retains0.75x animation speed and0.5x damage; stamina input
  limits apply to exertion only. The original game's shield/target policy is
  left intact, including native auto-shield behavior. Native accepted blocks
  spend stamina in combat; this build does not add guard-break/stagger logic.
- Shared HUD metadata is cloned privately for stamina. No Common HUD layout,
  texture, GameData, Bootup or message archives are replaced. The included
  RomFS changes are enemy resources; player AS/equipment files remain stock.

## Install

Use the original update131072 NUP (title0400486024DEC000). Remove the older
Hero package, then Configure Game > Add-Ons > Import Mod from ZIP and select
the entire Hero Core Prepared-Addon ZIP. Keep main, subsdk1 and the IPS sidecar
together. No commands or builder are required. Saves and emulator mappings
are not replaced. Do not stack with full Hero Mode.

The absence of wheel/shield features does not make native executable mods
automatically stackable: independent full-main/subsdk1 replacements still
need a deliberate combined build. Keep visual mods separate. See the current
compatibility notes for the exact tested combinations and remaining limits.

The optional builder reconstructs the prepared files from your matching
original game. Source checkout example: select `--variant hero-core`.
New four-preset difficulty and recovery-drop settings are not included yet.
