# OOT Mods by rexcraft88

Mods for Project Eglantine / Ocarina of Time, title **0400486024DEC000**, update **131072**, executable build **E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348**.

Download **`*-Prepared-Addon.zip`** from [Releases](https://github.com/REXCRAFT88/OOT-Mods-by-rexcraft88/releases), then use **Configure Game > Add-ons > Import Mod from ZIP**. No commands or builder step are needed. Use an emulator with full NUP RomFS and IPS support; the current regression test setup uses Fritchii v5.5.

November 9 regression update: Hero with Stamina **beta.11**, Hero without Stamina **beta.8**, Manual Shield **0.1.6**, Item Wheel **0.1.5**. See [changes and remaining test limits](docs/REGRESSION-UPDATE-2026-11-09.md). The new wheel/difficulty/drop options are a separate follow-up.

**Upgrading from an older `heromode.nup`? Use your original unmodified NUP with the new Prepared Add-on.** Current releases keep Lichii’s built-in FPS timing fix working through an IPS sidecar; do not stack them onto a previously patched game. See the [illustrated guide](docs/INSTALLATION.md).

| Download | Included |
| --- | --- |
| Hero Mode with Stamina — Beta / Early Access | Item wheel, manual shield and toggle targeting, enemy balance/behavior changes, combat stamina and HUD |
| Hero Mode without Stamina — Beta / Early Access | The same wheel, shield, enemy changes, with no stamina system or stamina HUD |
| Manual Shield | Only manual guard and associated target/input policy; no wheel, stamina, enemy or texture changes |
| Item Wheel | Standalone wheel with hold selection, tap variant cycling, outline/glow, installer and source |

**Choose one complete mod.** Hero Mode already includes the wheel and shield. Do not stack its native files with separate wheel/shield/stamina mods. Both Hero Mode variants are early-access betas.

Prepared Add-ons contain ready-to-load mod overrides. Optional small patch builders rebuild an Add-on ZIP from your matching game files. Current versions require the Add-ons route rather than a patched-NUP copy.

Read [Installation](docs/INSTALLATION.md), [Changes and controls](docs/FEATURES.md), and [Modder resources](docs/MODDER-RESOURCES.md).

See [Download verification and security checks](docs/SECURITY.md) for checksums, scan scope and results.

The game/version above is required. These are Eglantine patches, not N64 ROM patches, Ship of Harkinian mods, or Zelda64Recomp mods. Other executable updates are not supported by these exact offsets.

Hero Mode with Stamina includes [stamina/HUD configuration](docs/STAMINA-SETTINGS.md).

Controller settings updates: [Hold/Toggle targeting and bumper/trigger layouts](docs/CONTROLLER-SETTINGS.md).

Latest update: combat-only stamina detection, a 100–300 stamina curve, heavier Biggoron/hammer costs, small ranged-item costs, separate targeting/shield settings, and an R1-only Hero wheel. [HUD compatibility](docs/HUD-COMPATIBILITY.md).

Hero with Stamina **beta.10** adds a private runtime HUD: no Common HUD archive replacement, a half-height yellow bar, and a wheel cache fix for menu visits. The full DualSense UI mod was tested separately. Keep the addon folder prefix `00-OOT-Hero` for size-table priority. Read [HUD compatibility](docs/HUD-COMPATIBILITY.md).
