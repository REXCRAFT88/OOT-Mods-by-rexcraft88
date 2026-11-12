# Hero Mode Unified Beta 12 — Early Access

One Hero addon includes enemy tuning, stamina, the item wheel, manual shield
and targeting controls. Change features in the game's System → Options menu.

## Installation

1. Stop the game. Use your original unmodified game, update 131072 / 2.0.0,
   title 0400486024DEC000, build E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348.
2. Disable/remove older Hero, Hero Core, Wheel, Shield and Wheel + Shield
   addons. They replace the same native files; checking them together does
   not combine their features.
3. Download **OOT-Hero-Mode-Unified-v0.1.0-beta.12-Prepared-Addon.zip**.
4. Right-click the original game → Configure Game → Add-Ons → Import Mod
   from ZIP. Select the downloaded ZIP directly; no commands or new NUP.
5. Enable the single Unified Hero addon, apply, then launch the original game.

Keep the `00-` addon prefix for resource-budget priority. See the
[illustrated installation guide](INSTALLATION.md) for the import screen.
Back up saves before experimenting with beta mods. Releases do not contain
saves, the test arena, the game, or an emulator.

## Settings and controls

| Setting | Choices | Default |
| --- | --- | --- |
| Stamina | On / Off | On |
| Stamina Amount | Half / Full / Double | Full |
| Manual Shield | On / Off | On |
| Targeting Type | Hold / Toggle | Toggle |
| Swap Shield and Target | Off / On | Off |
| Item Wheel | On / Off | On |
| Wheel Bumper | Right / Left / Both | Right |
| Hero Difficulty | Warrior / Hero / Legend / Myth | Warrior |
| Disable Heart / Magic Drops | Off / On | Off |

Default full-controller bindings: **left trigger holds shield**, **left
bumper toggles targeting**, **right bumper holds wheel**, **right trigger
uses the item**. R3 camera reset also cancels custom targeting. The addon
does not install a DualSense emulator profile or controller artwork; bumper
and trigger roles follow the emulator's mapped game inputs on other pads.

With Manual Shield On, the wheel always uses Right so Left remains available
for targeting. Left/Both wheel preferences apply with Manual Shield Off.
Swap exchanges the manual shield and target inputs. Hold the wheel bumper
to select using either stick; release to choose. Tap cycles variants of the
selected group, including bottles, arrows, magic and masks when available.
Wheel Off restores the stock horizontal selector. Its stock bumper behavior
returns when manual controls are also disabled.

Stamina applies during detected combat. Heart containers expand capacity;
lower current health increases consumption rather than shrinking capacity.
Weapon/action costs differ, including heavier Biggoron/hammer use and small
ranged-item costs. Shield holding and accepted blocks consume stamina.
Exhaustion restricts evasive actions and weakens/slows sword attacks to 0.75
speed; Stamina Off removes the bar and stamina restrictions. Half/Full/Double
scales capacity, not regeneration speed or per-action costs.

## Difficulty

| Tier | Hostile damage vs original game | Enemy/boss health vs original |
| --- | --- | --- |
| Warrior | 2× | 1.5×, rounded up |
| Hero | 4× | 2× |
| Legend | 8× | 2× |
| Myth | Lethal accepted damaging hits | 2× |

These are multipliers, not fixed heart damage. Different attacks retain their
native strengths. The normal Stalfos slash tested at 2/4/8 hearts across the
first three tiers; Myth was lethal. Blocks and native invulnerability still
apply. Environmental damage is not deliberately made lethal by Myth.
Known native enemy/boss Life components are scaled without repeated stacking;
changing tiers preserves the living enemy's health fraction and never revives
dead enemies. Boss phase behavior has limited gameplay coverage.

Existing Wolfos behavior tuning remains included. Experimental Deku/Octorok
burst/flaming-seed changes are not advertised as complete in this release.
Blood-floor textures are not included.

Disable Heart / Magic Drops converts ordinary random recovery hearts, magic
jars and random fairies in the common lottery to green rupees. Heart pieces,
containers, quest rewards, inventory and placed map actors are not removed.
Explicit/scripted loot paths and the new pot fixture still need broader live
coverage; report exceptions with location and enabled addons.

## Validation and limits

User tested Fritchii 5.8 with DualSense UI and ultrawide disabled: stamina
settings, difficulty damage against Stalfos, wheel hold/flicker fixes, block
combination routing and final Options captions. Current selector Off visuals,
all boss phases, all controller types and full emulator-restart persistence
have incomplete live coverage. Existing visual compatibility infrastructure
is retained; this revision was not fully retested with every HUD/ultrawide mod.

Native checks cover all 150 known Life baselines through tier transitions,
damage-hook ABI, option tables, stamina gating, drop-filter scope and input
transitions. The optional builder reconstructs the exact release addon files.
Checks are not a claim of exhaustive gameplay validation.

For modders: [native settings and implementation map](../native/hero-options/README.md).
For AI involvement: [development disclosure](AI-DISCLOSURE.md).
