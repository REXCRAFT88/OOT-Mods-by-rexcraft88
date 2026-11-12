# OOT Mods by rexcraft88

Mods for Project Eglantine / Ocarina of Time, title **0400486024DEC000**, update **131072**, executable build **E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348**.

Download **`*-Prepared-Addon.zip`** from [Releases](https://github.com/REXCRAFT88/OOT-Mods-by-rexcraft88/releases), then use **Configure Game > Add-ons > Import Mod from ZIP**. No commands or builder step are needed. Use an emulator with full NUP RomFS and IPS support; the current regression test setup uses Fritchii v5.8.

November 12 update: **Hero Mode Unified beta.12 — Early Access** replaces the separate Hero variants. One addon has Options for stamina On/Off and Half/Full/Double, manual shield, targeting and swap, wheel and bumper choice, four difficulty tiers, and recovery-drop suppression. [Installation, settings, controls and test limits](docs/HERO-UNIFIED.md). Standalone Item Wheel **0.1.7** and Manual Shield **0.1.7** remain separate choices for users who do not want Hero tuning.

**Upgrading from an older `heromode.nup`? Use your original unmodified NUP with the new Prepared Add-on.** Current releases keep Lichii’s built-in FPS timing fix working through an IPS sidecar; do not stack them onto a previously patched game. See the [illustrated guide](docs/INSTALLATION.md).

| Download | Included |
| --- | --- |
| Hero Mode Unified — Beta / Early Access | All Hero features in one addon; disable stamina, wheel or manual controls independently in Options |
| Item Wheel + Manual Shield — Beta | Both input/UI features in one native package; no enemy tuning or stamina |
| Manual Shield | Only manual guard and associated target/input policy; no wheel, stamina, enemy or texture changes |
| Item Wheel | Standalone wheel with hold selection, tap variant cycling, outline/glow, installer and source |

**Choose one complete mod.** Hero Unified includes the wheel and shield. Do not stack it with separate native wheel/shield/stamina mods or older Hero variants. For Core behavior, turn Item Wheel and Manual Shield Off in Unified Options.

To use the standalone wheel and shield features together, choose **Wheel + Shield**. Checking the two separate packages does not merge their `main`/`subsdk1` replacements and can remove L1 targeting. [Hero Core details](docs/HERO-CORE.md).

Prepared Add-ons contain ready-to-load mod overrides. Optional small patch builders rebuild an Add-on ZIP from your matching game files. Current versions require the Add-ons route rather than a patched-NUP copy.

Read [Installation](docs/INSTALLATION.md), [Changes and controls](docs/FEATURES.md), and [Modder resources](docs/MODDER-RESOURCES.md).

See [Download verification and security checks](docs/SECURITY.md) for checksums, scan scope and results.

The game/version above is required. These are Eglantine patches, not N64 ROM patches, Ship of Harkinian mods, or Zelda64Recomp mods. Other executable updates are not supported by these exact offsets.

Hero Unified has in-game stamina settings. Advanced base configuration remains documented in [stamina/HUD configuration](docs/STAMINA-SETTINGS.md).

Controller settings updates: [Hold/Toggle targeting and bumper/trigger layouts](docs/CONTROLLER-SETTINGS.md).

The private runtime HUD avoids replacing the Common HUD archive and uses a half-height yellow stamina gauge. Keep the addon folder prefix `00-OOT-Hero` for size-table priority. Read [HUD compatibility](docs/HUD-COMPATIBILITY.md) and the [AI development disclosure](docs/AI-DISCLOSURE.md).
