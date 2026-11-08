# Stamina balance update — 2026-11-08

The current compatibility builder compiles `outputs/OOT-Test-Kit/hero_core.c` (mirrored in `native/stamina/hero_core.c`) and `native/compatibility/stamina_configurable.c`. The 96-byte stamina settings ABI is unchanged. `stamina_settings.py` now encodes the same heavy-weapon defaults.

At default 100% capacity, capacity interpolates linearly from 100 units at 3 permanent hearts to 300 units at 20 hearts. Values below 3 hearts keep the 100-unit floor; values above 20 keep the 300-unit ceiling. Maximum-life quarter-hearts grow capacity between those endpoints. Current remaining health increases costs, never shrinks capacity. Capacity presets scale the entire curve.

| Maximum hearts | Capacity |
|---|---:|
| 3 | 100 |
| 5 | 123.53 |
| 10 | 182.35 |
| 12 | 205.88 |
| 15 | 241.18 |
| 20 | 300 |

Base full-health costs: Kokiri Sword8, Master Sword12, Biggoron Sword24, hammer24. Thrust multiplier1.1, jump attack1.5, spin1.8. Bow release4, child slingshot release3, boomerang throw3. Injury and configured action-cost scaling apply. Ranged items remain usable at zero stamina and outside combat remains unrestricted. Regeneration and exhaustion penalties are unchanged.

Ranged detection observes accepted PlayerState AS request names in slots0/1 (string object at`+0x230`, text pointer at`+0x238`, stride0xd8). `BowShoot[Upper]` is used for both age-appropriate bow/slingshot releases; the player actor name distinguishes Child from Adult. `BoomerangThrow[Upper]` charges once per rising request, unioning the two body slots. `BowCharge`, reload and catch requests do not spend stamina. This is animation-request detection rather than raw button detection; live projectile/empty-ammo edge cases still require in-game testing.

Runtime cache adds `item_latch` at byte392 of NativeHero; reset on player replacement. No config ABI change. To retain FPS/ultrawide compatibility without enlarging module mappings, `near_enemy` now occupies subsdk executable padding at main-relative4f29ed0 (after the controller wrapper ending4f29ec8). The build asserts its 304-byte budget. The controller builder overwrites its assigned slice instead of appending after this additional code. Main code remains within its own executable alignment padding, and SDK additions remain within the original SDK alignment page.

Verification: host C tests check capacity endpoints, monotonic quarter-heart growth, all melee profiles/move multipliers, ranged costs, injury, duplicate tokens, outside-combat exemption and exhaustion. Compiled AArch64 tests in `native/compatibility/check_item_costs.py` check aiming exclusion, upper/lower deduplication, repeated releases, child slingshot, combat exemption and real native Master/Biggoron/hammer cost classification. Combat gate, controller mode, FPS cave eligibility and menu/ocarina checks also pass. Full physical weapon-use validation remains pending.

Biggoron guard correction: the compatibility builder redirects only the mod guard-entry draw call to `guard_equipment.c`. It skips the forced equipment draw for AS WeaponType2 and requests shield slot4 for other weapons. This prevents drawing Biggoron alongside a held hammer. Other native equipment calls are untouched. The wrapper fits the existing SDK executable alignment padding in all three guard variants; no module mappings move. Physical validation of the blocking pose remains required.


Publication decision: keep the equipment adapter that prevents the shield being drawn with Biggoron. Exclude the experimental ASB guard pose entirely: the user confirmed this sword does not block in the game and requested publication without that addition. No adult ASB override is shipped.
