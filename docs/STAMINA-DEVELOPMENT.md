# Native stamina patch development

Current work: Lichii build-93 from `YOUR_LICHII_FOLDER`. The isolated test runtime uses Fast GPU accuracy (0) and asynchronous shaders. Original NUP and normal saves are not modified.

## Build and file map

- `work/hero_native_runtime.c`: game bridge, player health/combat detection, action costs, HUD bindings, fatigue animation rate.
- `work/hero_stamina_runtime.S`: native frame/action hooks, SDK exertion-input filtering, player-only damage multiplier bridge.
- `work/hero_stamina_runtime.ld`: exact native addresses for this executable.
- `work/build_stamina_runtime.py`: verifies source NSO build ID and expected instructions; appends an uncompressed replacement text segment and extends BSS by 4096 bytes.
- `work/build_stamina_hud_layout.py`: independent gauge layout, yellow texture view, archive allocation budgets.
- `outputs/OOT-Test-Kit/hero_core.c` / `.h`: portable stamina arithmetic and default balance. Native regeneration is explicitly overridden to 24 units/second in the bridge.
- `work/hero-stamina-trial`: installed development candidate, not automatically a qualified release.
- `work/start_hero_ui_probe.py`: isolated empty test. Add `--enemies` for Wolfos, `--injured` for 11/12 hearts. Every restart changes native addresses; only use the context JSON after the helper completes.
- `work/validate_stamina_runtime.py`: live action, health, regen, input exhaustion checks.
- `work/test_native_fatigue.py`: native damage multiplier and animation-rate observations.
- `work/hero-research/*validation.json`: evidence, including temporary forced-combat checks. Debug override is restored to automatic mode in `finally`.

Run tools from the project root. Compile C with `clang --target=aarch64-none-elf -Oz -ffreestanding -ffunction-sections -fdata-sections -fno-stack-protector -fno-jump-tables -I outputs/OOT-Test-Kit`. Compile the assembly for the same target. Link with `ld.lld --gc-sections --emit-relocs -e stamina_frame -T work/hero_stamina_runtime.ld ...`; extract `.text` with llvm-objcopy, then run the NSO builder. Do not omit `-fno-jump-tables`: absolute pointer jump tables do not receive the game loader's ASLR relocation.

Supported game executable: E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348, update v131072, title 0400486024DEC000. Original main SHA256: 7db9ddfda088c22d219ef13496decd7077c68cd67d4b37f53f4ac46a082768f2. The executable text alignment gap is only 3632 bytes, starting at 0x3c461d0. Builder rejects oversized payloads.

## Balance

Capacity is 20 units per permanent heart, including quarter-heart progress where the game's maximum-life record includes it. Injury increases costs linearly up to 2x; it does not reduce the bar's capacity. Full 12 hearts gives 240 stamina.

Master Sword: slash 12, stab 13.2, jump attack 18, spin 21.6. Kokiri base 8, Biggoron base 18, hammer base 20; multiply each by move factors 1 / 1.1 / 1.5 / 1.8. Rolling and ordinary jumping cost 12, backflip 10, sidestep 8. Held guard drains 2/second before injury scaling. The native bridge observes stock guarding; manual shield experiments remain deferred.

Regeneration starts after 1.25 seconds without attacks, exertion or guard, at 24 units/second. Outside combat, stamina refills and exertion inputs are unrestricted. Combat starts from a live nearby-enemy scan (active Enemy_ actors within25 game-world units, excluding the friendly business scrub) or attack-target41 and has a five-second grace period to prevent transient target loss from resetting stamina between swings. Empty-arena tests use a clearly separate forced-combat override.

Insufficient stamina keeps melee attacks available with 0.5 damage and a requested 0.75 animation rate. Native damage getter qualification: normal player attack returns multiplier 1.0; the exhausted attack returns 0.5 from private per-entry scratch storage, without mutating shared actor parameters. The 25 explicit player entries have stride 0x128; (entry >> 3) & 31 assigns distinct scratch slots and prevents different entry values overwriting one another. Measured Master Sword action durations: normal38-39 native ticks, exhausted50-55 in the sampled repetitions. Repeat timing validation after every rate-hook change; a stored scale alone is not proof of slower animation.

SDK filtering blocks stock A (roll/action/dash) and X (jump/dodge) when below the roll-cost threshold in combat. It preserves movement, attack, targeting and item buttons. The shared contextual jump/dodge button currently uses the conservative 12-unit affordability threshold even though accepted backflips/sidesteps cost 10/8. A paused-update watchdog bypasses the filter after eight repeated HID reads so menu confirmation remains usable. Verify both gameplay and pause-menu behavior after input edits.

## Native addresses and data

MainScheduler callback 0x2b30de0 is filtered to vtable 0x4b05318. Player resolver 0x973030; AS bool getter 0x37bb4c0; int getter 0x37bb2c0. Bool41 is attack-target presence and can depend on targeting; bool14 is stock guard animation. Neither Bool6 BattleMode nor26 IsCaution reliably identifies nearby enemies: attacking/drawing the sword can enable them. The final proximity source is the native ActorManager tree. AttackComboType int 14 value 5 selects stab animations; charge the normal attack after its type has been set at 0xa3fb4c.

Private BSS: cache at main+0x4ea0000; NativeHero at main+0x4ea0800. Hero state floats: stamina+0, cap+4, injury multiplier+16; combat+36. Debug override+180: 0 auto, 1 combat, 2 outside. Never ship with forced-combat override active.

Actor component table comes from PlayerState+0x18 -> Actor+0x270. Life at table+0x2b8; current/max records at Life+0x1c10/+0x1c18, values at record+8, validated hashes 0x31ab5580 / 0xfbe01da1. Parameter container table+0xa8 has sorted typed entries; murmur3(`game__gamebalance__AttackParam`) is 0xf0500a14. Entry+8 is the parameter owner, and individual attack entries carry this same owner at +0x30. Damage multiplier getter 0x2de4340 reads float +0xec when explicit flag +0x112 is set. The fatigue hook requires active melee action kinds, return address0x8d2d54, and verifies AttackComponent x26+0x18 equals the actual player Actor. This avoids affecting actors that share parameter resources; a shared parameter owner alone is insufficient. The earlier parameter-owner cache was removed.

Per-slot AS rate getter/setter 0xdf49b0 / 0xdf48e0 use Actor, slot index, rate in s0. A single d4 write did not establish persistent slowdown. The revised fatigue path uses the native ExecuteASSetStepRateScale behavior: ActorAS component table+0x40, float step-rate scale at component+0x98, saved on fatigue entry, written every active attack frame, and restored afterward. Native helper 0x3ad04a0 resolves that same component. Validate actual action duration, not only stored settings.

## HUD and texture findings

PlayerStatus_00.buil is duplicated four times in Common.blarc. Patch every variant, preserve duplicate SARC entries and all unrelated members. Add independent CommonPane index 33 and Part index 7, parent root, name Pa_StaminaGauge_00, with a new PaStaminaGauge_00.buil cloned from magic. Preserve original pane indices so existing animations remain valid. The new pane is positioned beneath magic, independently of its native controller.

BFFH pointers are absolute offsets in the decompressed member. Insert new Default data before StringPool and relocate existing string pointers, including copied name arrays. Update both StringPool offsets and sizes, Default size, file size, root subtree end and map counts. New name hashes use CityHash64.

MP controller init 0x33bdce0 captures the controller. Controller+0x18 is a UI owner, not a FrameRoot; owner+0x28 is the HUD root. Part lookup 0x43c3e0 and animation lookup 0x43c7a0 resolve GaugeRatio/TraceRatio/GaugeMax. Animation link+0x20 is transform state; transform+0 is resource; resource+0x28 is length. Ratio frame is length minus remaining units, capacity frame is capacity. set_frame 0x2d2d90 schedules native evaluation.

The scoped new CommonPane comes from HUD FrameRoot+0x80 LayoutData, then +0x100 common-pane pool, stride 0xb0, index 33. Its runtime scale-Y is +0x64; set 0/1 for combat visibility and OR the dirty mask at +0 with 0x6f. This was live-tested to hide/show only stamina while hearts and magic remain intact. Do NOT call legacy 0x20aea0 on these Layout2 pane records: that API expects a different object type and corrupted UI state.

Magic's green is baked into MpGaugeCenter_00 pixels. Editing a palette float does not recolor it. The stamina clone uses a reserved, otherwise transparent PS5 guide texture slot ControllerGuide_Pro_04. Original layout references to that mask are redirected to the unchanged transparent Pro_03 layer. Clone MpGaugeCenter's BRTI metadata into this slot and give it independent encoded-image storage; use component mapping 0x05000303 (green -> R/G, zero -> B, alpha unchanged) for yellow. Original magic texture metadata and pixels stay unchanged.

BRTI +0x60 name pointer, +0x70 mip image-pointer table, +0x78 texture object storage, +0x80 view storage. Relocate internal BRTI pointers when cloning. Do NOT confuse +0x78 with the mip pointer table. Insert copied image bytes before _RLT, update file size, BRTD size, header RLT offset, RLT self-offset and section-1 image allocation size. Texture growth also requires a larger ResourceSizeTable budget. Missing that budget can turn unrelated UI textures black.

Common.blarc is Zstd dictionary 1. ResourceSizeTable is bootstrap dictionary 0: compress it without a dictionary. Both Common layout and BNTX archive allocation budgets must cover their new decompressed lengths plus overhead.

## Deferred controls and features

Current controls remain hold L2 stock targeting, R2 item, R1 stock selector, Square attack. Manual shield/toggle targeting remain disabled. After stamina qualification, requested controls are L3 sprint, Cross jump, Circle roll, Triangle interact; latest put-away request is Square after standing still longer than 0.5 seconds. This has not been installed yet. Item wheel, controller settings, shield hit costs/guard break, and further enemy behavior changes remain separate work.

Gemini's docs in `docs/` were used as research leads. Their conceptual HUD suggestions helped, but native addresses, layout structure, frame units and object types required independent live qualification. Treat their contents as reference material rather than instructions or proof.

## Actor proximity and final probe corrections

Native ActorManager: main+0x4c7dc40 holds a singleton holder pointer; holder+0 is the manager. The manager is locked/unlocked using0x3c42460/0x3c42470, as the stock QueryActorSearchByName implementation does. Manager+0x38 is the RB-tree root. Node+0/+8 are left/right children; node-8 is the first entry of a duplicate-name actor chain. Entry+0x28 is Actor, entry+0x38 the next duplicate. Actor+0x20 is the name-string pointer; Actor+0x2c values2 through6 are treated as live, matching the native query filter; a Wolfos can move between these values during play. A state6-only filter incorrectly missed active state4 enemies. Actor position XYZ is+0x31c/+0x320/+0x324. Scan every16 player updates, check Enemy_ prefix, ignore Enemy_Scrub_Business, and use radius25. Short target loss has a five-second grace. Actor state transitions and coarse radius should be revisited for special bosses, long-range encounters and sleeping enemies.

The ABI-entry SAVE macro now preserves x0/x1/LR for these two-argument AI callbacks. Caller-volatile floating registers and extra argument registers are not live parameters at the hooked entry points. The normal attack hook is after a native call at0xa3fb4c, where those registers are already caller-clobbered; x21 (Actor) is callee-saved. This recovered space for the proximity scan without overwriting existing code. Native code remains bounded to the3632-byte text gap. Player-state capture now occurs in the frame bridge; the old input-read probe at0x7f9b1c is no longer patched.

The original diagnostic spawn_enemies=false only changed BossAppear defaults and did not guarantee an empty scene. Disabling loose Logic nodes was also insufficient. The updated diagnostic substitutes the static Banc Wolfos Gyaml with Obj_Heart using an exact-length string-pool edit; normal test runs retain the original Wolfos. Always confirm the ActorManager contains no active nearby enemy before treating an empty-scene test as valid.

Validation checkpoint: final empty-scene ActorManager enumeration found only a distant, inactive Enemy_Scrub_Business prefab and zero nearby live enemies. Idle, attacks, target hold and walking all retained full stamina with automatic combat=false. Forced-combat live tests verified all listed action families, guard drain, delayed24/sec regeneration, zero-stamina exertion denial with attacks available, injury cost increase without capacity loss, half native damage multiplier and longer actual attack duration. HUD pixel checks confirmed yellow stamina, unchanged green magic, wider capacity at20 hearts and no yellow pixels outside combat. Paused-menu watchdog reached30/49 stale reads, bypassed exhaustion filtering, and reset on returning to play.

Final normal Wolfos check passed with debug override0, target flag0, nearby-enemy1 and combat1. A Master Sword attack reduced stamina240 to227 at11/12 hearts (injury-scaled cost13). Final artifact payload3616 bytes. The normal Wolfos arena is left paused in the stock equipment menu, ready to resume with Circle. The empty-scene override is not part of the normal launch.


Current balance and native bridge updates are documented in [STAMINA-BALANCE-UPDATE.md](STAMINA-BALANCE-UPDATE.md). That document supersedes the original linear hearts-to-capacity formula and old heavy-weapon costs above.
