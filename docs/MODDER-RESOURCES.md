# Modder resources and implementation map

This is a version-specific reverse-engineering notebook for Project Eglantine update131072, title0400486024DEC000, main buildE0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348. Offsets below are **main-module-relative** unless stated otherwise. They are not universal Switch/OOT addresses.

## Repository layout

- `patches/<variant>/manifest.json`: exact input/output hashes and each changed file. This is the authoritative release file list.
- `install.py`: deterministic native-module reconstruction and checked resource delta application; accepts a NUP or extracted exefs/romfs folder. Optional `--patched-nup` builds an independent playable copy.
- `nup_reader.py`: NUP v1 package/member parsing and copy-only member replacement, TOC/header hashes and read-back verification.
- `native/wheel/`: wheel C, AArch64 hooks, linker script and historical layout/build scripts.
- `native/stamina/`: portable stamina core, game adapter, AArch64 entry/leave hooks and HUD builder snapshots.
- `native/manual-shield/`: the standalone released guard input/frame/state code and linker script.
- `native/hero-with-stamina/`: merged wheel/guard input pipeline and rtld/subsdk linker information.
- `native/hero-without-stamina/`: no-stamina frame/input bridge calling the standalone wheel helpers.
- `native/resources/`: enemy stat/AI builders; `docs/enemy-balance-report.json` records exact balance fields.
- `docs/STAMINA-DEVELOPMENT.md`, `ITEM-WHEEL-DEVELOPMENT.md`, `RESEARCH-AUDIT.md`: detailed earlier findings and failure history. Where older controls/status conflict with FEATURES.md or this page, the release files and current feature guide take precedence.

Historical builder snapshots retain references to the original development `work/` and `outputs/OOT-Test-Kit/` layout. They are implementation references, not a promise that running each old script from this checkout rebuilds every asset. The portable installer is the supported exact-release reconstruction path. Edit the native snapshots and adapt/relink their addresses when developing a new version; never publish a source-only edit without rebuilding the payload and validating its native hook branches.

## Native modules and safe linking

Original main image ends at0x4ea0000. The wheel/manual releases reserve0x5000 additional BSS bytes; with these headers subsdk0 loads at main+0x4ea5000. Original subsdk0 text ends at0x84770 and its rodata begins at0x85000, leaving2192 bytes of alignment space. Thus the guard payload starts at **main+0x4f29770**. Using0x4f2c770 was wrong and caused a black-screen boot freeze.

`rtld` precedes main by0x20000 in the tested layout. The wheel payload uses its original text end0x2740 up to0x3000. Symbols linked from rtld to main must account for the0x20000 relationship. Do not relocate main text/rodata arbitrarily: existing pointer/relocation tables depend on their virtual addresses.

Installable NSOs preserve the original rodata/data bytes and append one uncompressed text replacement, updating header offsets/sizes, BSS, compression flag and text hash. A larger disk NSO does not imply that all its unused stored text copies are mapped into game RAM. The public packager normalizes the text replacement to avoid retaining successive obsolete appended copies.

Payload and state allocations:

| Purpose | Main-relative address |
| --- | --- |
| Stamina/player cache |0x4ea0000 |
| Native stamina or manual-only bridge state |0x4ea0800 |
| Wheel state |0x4ea1000 |
| Guard/target input state |0x4ea3000 |
| Stamina executable payload |0x3c461d0, within original text padding |
| Manual/merged guard payload |0x4f29770, in subsdk0 alignment space |

When relinking, inspect ELF symbols with `llvm-nm`, verify the actual module load address, assert payload capacity and check original instruction bytes before writing branches. An ELF that links successfully can still branch into the wrong mapped module.

## Input and manual guard

The qualified full-controller HID state has40-byte stride; sample clock at+0 and button bits at+8. Logical masks: L=0x40, R=0x80, ZL=0x100, ZR=0x200, right-stick click=0x20. Batch counts1..64 are accepted. Input hooking is scoped to full Pro-controller-style IDs0/32; split Joy-Con/handheld paths still need testing.

The merged path handles wheel timing then guard/target remapping once. L rising-edge toggles targeting; right-stick click cancels; physical ZL means held guard. Native ZL is supplied while targeting or guarding so the **native controller, movement state and animation agree**. Swapping only Wait/Move animation names to LockOnWait/LockOnMove produced the observed random-forward/axis-constrained movement and was removed.

The player AS Bool14 setter at0x37ba100 is scoped to the actual player AS-interface pointer, not merely the address of its BSS pointer slot. Other actors and other boolean indices keep the original behavior. The interface is obtained from Actor component table+0x40, then pointer chain+0x18,+0x18,+0x40. Native bool getter is0x37bb4c0; int getter0x37bb2c0. Native enum names and AS-blackboard indices are not interchangeable.

Guard KeepMove flag is bit5 at Actor component188+0x24. Native LockOnWait E50 guard writes are hooked at0x972e18 and0x97320c to suppress guard when the manual policy denies it. PlayerState resolution helper0x973030 takes an action/selector context; Actor component resolver0x974eb0 takes an Actor.

Released guard entry requests **shield slot4 only** through0x6b6820(EquipmentUser,4), once per entry. The former0xa43030(Actor,1,1) sword/equipment draw request could force the sword out while targeting and was removed. EquipmentUser is Actor.table+0x200; Actor.table is Actor+0x270.

A no-player-update watchdog clears guard/menu state but still consumes L/ZL. Passing L through that watchdog let it reach the stock item selector, fighting target toggle; the final release reserves it. This changes L shoulder-tab behavior in paused UI too; retain access to other menu navigation controls.

The implementation still uses native target/guard locomotion and can align the camera/select a native target. Tester confirmed final L1 exclusivity and moving shield with sword sheathed in both toggle states on DualSense/Lichii. This is not exhaustive equipment/child/controller coverage.

## Stamina

`hero_core.c/.h` own the tunable costs and portable policy; `hero_native_runtime.c` owns game observations/action adapters. HeroState stores stamina/capacity at+0/+4, initialized+20, alive+32, combat+36. NativeHero AS interface is+0x80 and tick counter+0x88; confusing decimal128 with hex0x128 breaks the setter scope.

Core rules:20 units per permanent heart; current injury increases cost; no stamina restrictions outside combat. Nearby enemy ActorManager scan uses a25-unit radius and five-second grace. Do not use BattleMode/IsCaution alone as proximity: merely drawing/attacking can enable them.

Explicit action-entry/leave hooks charge slash, stab, jump attack, spin, roll, jump, backflip and sidestep. Costs are in FEATURES.md. AttackComboType int14 value5 identifies a stab in the qualified path. Fatigued melee uses private per-entry damage storage rather than mutating shared actor parameters, with damage0.5 and animation rate0.75. Restore the previous AS rate after the attack; a stored rate field alone is not evidence that animation actually slowed. Earlier timing checks measured normal38–39 vs fatigued50–55 native ticks.

Regeneration delay1.25 seconds, rate24/second. Held guard costs2/second before injury scaling. Successful block spending is now hooked at native ReactionGuard Enter (0x27f7d00). The adapter resolves the player, checks manual guard and combat, then deducts runtime config block_base_cost (8) times injury scaling, clamps to zero and resets the regeneration delay. It charges once per native guard-reaction entry rather than each update. Incoming-damage scaling and a native guard-break/stagger adapter remain unfinished. Compiled AArch64 tests cover player scope, combat scope and clamping; tester reported the behavior working in the Stalfos setup.

Installed block-cost entry: ExecutePlayerReactionGuard vtable0x49c71b8, Enter0x27f7d00, Update0x27f7f90, Leave0x27f8100. GuardBreak vtable0x49c7480, Enter0x27fa200. Enter/Update/Leave slots are+e8/+f0/+f8. Do not invoke GuardBreak Enter using a ReactionGuard object: their object layouts differ. Successful contact enums/token deduplication still need live qualification; do not fake collision by forcing a shared damage/result bit.

## Wheel and HUD resources

Wheel integration hooks bind0x33ca1d0, list constructor0xe9ee30, draw0x3773874, update0x33c9270, MainScheduler tick0x2b30de0 and full HID callsite0x346966c. Native highlight helper0x33c8f50 is not a commit; actual commit0x33c98f0(controller,0). Preserve that distinction for tap-cycling.

Tap/hold uses native sample-clock delta192. Initial hold input is consumed; release emits a variant-cycle event for a tap or preserves long-hold selection. A tap does not open the native selector. Groups preserve native inventory/age usability and remember selected variants. Bow item widget names can change after equipping; grouping must recognize both Weapon_Range and Pouch_Range naming or fire-arrow cycling gets stuck.

Layout2 authored pane position is+0x6c/+0x70; scale+0x60/+0x64, dirty flags OR0x6f at+0. Writes to derived+0x4c/+0x50 are overwritten by the renderer. Reuse native cursor/glow instead of allocating a new renderer. All duplicate ShortCut_01/PaShortCutSlideList SARC members must be patched; a dictionary keyed by filename silently discards duplicates.

The yellow stamina gauge is a separate cloned PlayerStatus part and PaStaminaGauge asset. Green magic remains stock. A BNTX view reuses a copied magic gauge image with channel swizzle for yellow; it must be placed under `romfs/UI/Layout2Archive/`, not next to romfs. Missing that file produced a visually empty gauge despite240/240 runtime stamina. Common UI resource allocations must cover the expanded uncompressed layouts and texture archive. The public builds restore original controller/font/guide members instead of redistributing the PS5 profile/art.

## Enemy resources

Enemy packs are compressed SARC archives containing parameter/AI resources. Patch positive HP with ceiling1.5x and positive attack scalars2x, preserve zero/special cases, and ensure shared named resources have identical edited content in all owners. Include dedicated enemy projectile packs; exclude player arrows/reflected-player actors. The balance report records exact paths and values.

Wolfos edits retain first attack speed, accelerate follow-ups and bypass rear-exposure control flow. Stalfos retains counter/interval edits. Reparse the complete graph, verify exact-length resource edits and compression round trips; branch names alone are not behavior evidence.



## Test workflow and boundaries

Use an isolated adult/full-inventory save and a separate game copy. Fresh native-module launches are stronger evidence than live code writes. JSON input injection does not reliably traverse the raw HID hook; physical-controller confirmation is needed for raw guard/target routing. Automated AArch64 emulation checks relocation, masks, batch handling, scoped setters and exhaustion policy but cannot prove shield collision or visible poses.

Test stamina capacity/injury separately, guard held/released, target alone, shield moving diagonally, target+shield with sword sheathed, R1 tap without popup, wheel hold/equip, R2 bombs/bow, green magic/yellow stamina, pause UI and scene transitions. Do not publish the Stalfos test override as global balance: the special test used36 HP (2x), while released global Stalfos HP is27 (1.5x18).

Future work: broader multi-hit impact coverage and native guard break; optional in-game controller settings; broader controller/child/boss coverage; more enemy patterns and extra saves. These are future work, not shipped features.

## Compatibility repair (November 7, 2026)

The previous stamina payload occupied main+0x3c461d0..0x3c46ff0, overlapping Dynamic FPS at0x3c46200 (120 bytes) and the supplied ultrawide routines at0x3c46400..0x3c465e4. The new helper/core assembly starts at main+0x3c46600; its maximum end is0x3c47000, before rodata. The stamina native C bridge uses SDK text alignment padding at sdk+0x87e850 (main+0x5803850) and must fit before sdk+0x87f000. Main still grows BSS by0x5000; module positions remain main+0x4ea5000 for subsdk0 and main+0x4f85000 for SDK. FPS state main+0x4e9fe00 is left alone.

The rtld frame bridge and all stamina entry branches are retargeted to the relocated functions, including the HID tail. Do not merely move bytes: ADRP/BL relocations must be linked again. native/compatibility/build_compatibility.py builds the compatibility layer from the qualified prior variants; its inputs are the workspace's matching game/resources and compiled baseline artifacts. native/compatibility/check_context.py exercises the compiled input routines in Unicorn. The offset layout supports this exact executable build only.

ExexutePlayerPlayOcarina (native spelling) has Enter0x2894340 and Leave0x28947f0, with PACIBSP preserved by each trampoline. wheel_cache+120 tracks the action; +124..136 hold menu heartbeat/bypass state. Input passthrough in paused menus is detected from stopped player ticks (or the wheel scheduler for standalone). The native ocarina action bypass clears pending wheel events; it does not remap notes.

### Built-in FPS eligibility regression

Leaving the FPS cave's bytes untouched was insufficient: PatchNSO also checks that its executable-padding record lies outside header.segments[0].size. Extending main text beyond0x3c46200 made this check fail. Keep main text at its original0x3c461d0 and apply our code at0x3c46600 via the supplied IPS32 sidecar (IPS offsets include the synthetic0x100-byte NSO header). Loader page alignment already maps this padding executable. Our inline branches and extended BSS remain in the replacement NSO. This retains module placement while allowing built-in FPS eligibility; the previous patch-copy NUP workflow cannot carry a new ExeFS IPS sidecar, so current builders output Add-ons instead.

## Stamina configuration (Beta6)

The IPS sidecar now seeds a 96-byte configuration block at main+0x4ea4000, inside the already reserved BSS. It contains HeroConfig (20 floats, 80 bytes), HUD offset X/Y (two floats), little-endian STM1 magic and schema version1 (two u32s). Frame initialization copies only the first80 bytes into NativeHero.config; game/save files are not parsed for these settings. The optional stamina_settings.py edits this record and the ZIP receipts, preserving executable code and all other resources. Defaults retain20 units/heart and24/sec regeneration; HUD Y offset is+24.

The native C bridge source is native/compatibility/stamina_configurable.c. Its near_enemy helper is linked into main's existing executable alignment padding to leave SDK space for configuration and HUD logic. copy_config is a small AArch64 vector copy preserving the state fields outside the80-byte destination. The main NSO text extent stays original; both code and configuration are installed via IPS. Keep the existing FPS loader regression checks.

HUD coordinates are changed only when the additive stamina pane binds. Capacity scaling is normalized for display, so the visual GaugeMax continues to correspond to permanent hearts at20 display units per heart while the underlying stamina pool can be larger. The visibility scale continues to be combat-only, and the magic gauge resource is unchanged. A real in-game settings frontend remains separate work; JSON in the ZIP is a receipt, not a file automatically loaded by the game.

Edit stamina_settings.py DEFAULTS for user defaults or encode_settings for base costs/percent conversion, then rebuild the sidecar and release manifest. The legacy hero_default_config routine alone no longer supplies native Beta6 defaults.


## Standalone wheel right-bumper-only (v0.1.4)

The base game has separate left and right shortcut branches. Filtering only R at HID level leaves L able to open the replaced selector. `native/wheel/right_bumper_only.py` disables the L-only BoolSelector True branches by routing them to their existing False destinations: Event node141, ShortCut node52, UpdateShortCutOpenHoldFrameCounter nodes3/14. R, menu and ocarina queries are untouched; no global L input mask is installed. Resource sizes do not increase. The installer applies source/target SHA256-checked binary deltas for these three uncompressed AINB resources. Do not stack another mod replacing these sequences without merging its graph changes. This change applies only to standalone Item Wheel.

Validation on build117 PGO: initial and repeated L85-frame holds leave the wheel closed; R85-frame hold opens it; R5-frame tap does not open it. Installer round-trip verifies all seven files. Compiled context and FPS loader regression checks pass. These checks do not replace a full controller/ocarina playthrough.


## Controller options implementation

`native/controller-options/` builds the four-choice native controller setting for Hero and Manual Shield. Run its native builder and resource builder after `native/compatibility/build_compatibility.py`, then run `native/build_public_bundles.py --controller-options`. Development resource dependencies are the workspace `oot_assets`, `byml_inspect` helpers and Jungle's SARC/MSBT common readers; end-user installers need none of these.

The native helper lives at main-relative0x4f29c40 inside subsdk0's existing text alignment gap (ends before0x4f2a000). It reads OptionData via the GameData singleton at0x4e842a8, field hash0xc713c7da. Hold/Switch tokens preserve the original two choices; existing Normal/Pro tokens encode the swapped choices in this row only. OptionSetTable ChoiceType and GameData enum index53 RawValues/Values gain those two existing tokens; other enum properties remain unchanged. English row-local MSBT labels00..03 are supplied in all language archives. Native UI initializer0x32df4e4 maps the four tokens to indices. Input native Switch processing is disabled at0x574e1c and query0x279d640 so it cannot toggle again after our hold/toggle policy. The original main text size, FPS cave, ultrawide cave and module data addresses stay unchanged.

The helper normalizes physical L/ZL before the qualified independent-shield policy. Hold updates the target latch continuously; Toggle retains the existing edge latch. R3 cancels. Private control state+20 records the setting, +24/+32 record physical/normalized button samples. Changing modes clears the old target latch. The existing context guard bypasses the helper in menus/ocarina.

Resource budgets merge with each variant's existing table and grow for changed archives. **ResourceSizeTable must be compressed without a Zstandard dictionary:** it loads before the dictionary pack. A dictionary-compressed table causes a startup resource lookup loop. GameData overrides replace synthetic test defaults, so an unmerged test harness may spawn child Link despite its Adult selection; this is separate from real saved progress. Before removing the mod, choose a bumper mode so the saved enum is one of the original two values.

Validation: compiled AArch64 checks pass all four choices and independent shielding in all three variants. Live build117 PGO checks confirm bumper Hold releases, bumper Toggle latches and toggles off, swapped menu choices display and persist across restart. A physical-trigger check is tracked separately because automated ZL injection does not reach the raw trigger path reliably.

Runtime HUD source/research: [native/runtime-hud](../native/runtime-hud/README.md). Includes private UIL metadata, module format, SDK relocation, bar geometry and ASLR/cache regression checks. See [HUD compatibility](HUD-COMPATIBILITY.md) for size-table priority.
