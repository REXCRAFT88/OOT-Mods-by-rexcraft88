# Unified Hero Mode settings (beta.12)

This release combines the Hero variants into one native addon. Do not install it alongside another Hero,
standalone Wheel, standalone Shield, or combined Wheel/Shield native addon:
they replace the same executable module. Compatible visual addons use a
separate layer; they do not require stacking these gameplay addons.

Settings are in the game's System → Options menu, below the stock rows.

| Setting | Choices | Default |
| --- | --- | --- |
| Stamina | On / Off | On |
| Stamina Amount | Half / Full / Double | Full |
| Manual Shield | On / Off | On |
| Targeting | Hold / Toggle | Toggle |
| Swap Shield and Target | On / Off | Off |
| Item Wheel | On / Off | On |
| Wheel Bumper | Right / Left / Both | Right |
| Hero Difficulty | Warrior / Hero / Legend / Myth | Warrior |
| Disable Heart/Magic Drops | On / Off | Off |

With Manual Shield On, left trigger shields and left bumper targets by
default; Swap exchanges those two inputs. The wheel stays on right bumper
to avoid stealing targeting. The saved Left/Both wheel choice takes effect
with Manual Shield Off. Wheel Off restores native horizontal selection.
The bumper preference configures the wheel, not the stock selector.

Stamina Off hides the bar and removes its costs, exhaustion restrictions and
attack slowdown. Amount scales the configured capacity without compounding
on successive frames. Combat-only use and heart-container scaling remain.

| Difficulty | Hostile attack damage vs stock | Enemy/boss health vs stock |
| --- | --- | --- |
| Warrior | 2× | 1.5×, rounded up |
| Hero | 4× | 2× |
| Legend | 8× | 2× |
| Myth | Lethal accepted hostile hits | 2× |

Myth preserves native invulnerability, collision and accepted blocks; it
does not turn environmental damage into an instant kill. Health scaling
uses known native Life components and the shipped asset inventory. Unknown
or progression-backed Life values are deliberately excluded. Boss phases
need further gameplay coverage. Tier changes preserve the living enemy's
health fraction and never revive dead enemies.

Disable Heart/Magic Drops replaces ordinary random hearts, magic jars and
random fairies in the common loot lottery with green rupees. It does not
delete heart containers, pieces, quest rewards, placed map actors, bottled
fairies, or existing inventory. See RECOVERY-DROPS.md for hook scope.

## Implementation map

- `settings.c`: one cached packed snapshot per player frame; native pending
  Options readers, independent `RexHero.*` GameData fields.
- `build_settings_resources.py`: append-only Options/GameData/translated
  labels, valid enum domains, native save metadata and resource budgets.
- `menu_patch.py`, `menu_native.c/.S`: 25 native option types, guarded hash,
  name and field lookup extension; stock fallbacks retained.
- `combat_bridge.c`, `combat_damage.S`: bounded health scans and hostile
  damage multiplier hook; no per-frame allocation or shared parameter edits.
- `combat_inventory.h`: generated baseline provenance; regenerate with
  `build_combat_inventory.py` when deliberately changing the balance inputs.
- `recovery_drops.c/.S`: filter only the native lottery result records.
- `../runtime-hud/stamina_bridge.c`: stamina toggle/capacity and frame refresh.
- `../runtime-hud/hud.c`: private HUD metadata and live selector label switch.
- `../compatibility/wheel_context.c`: context-aware input routing.
- `../hero-with-stamina/wheel_runtime.c`: radial behavior and native Off path.
- `../controller-options/controller_options.c`: manual control settings.

Unit/emulated checks validate native ABI, table bounds, option domains,
damage policy, life transitions, recovery scope and input gates. These do
not substitute for gameplay testing. Current user-confirmed checks include
stamina settings, native selection/L1 routing, Stalfos difficulty damage,
shield/target block routing, wheel opening hold and final caption layout.
The narrowed selector-Off icon/label fix, recovery drops, all boss phases and
persistence across a complete emulator restart have incomplete live coverage.
