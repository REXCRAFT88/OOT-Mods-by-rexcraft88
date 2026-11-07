# Native item wheel development

Target: OOT Project Eglantine v131072, main build ID
`E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348`.

## Current status

Experimental native replacement under live testing. Not yet a released wheel.
The existing stamina release remains the baseline. Manual shield and toggle
targeting remain deferred; L2 retains stock targeting and R2 uses the item.

## Files and build

- `work/wheel_runtime.c`: stick direction, native selection and radial geometry.
- `work/wheel_probe.S`: original-instruction trampolines and bound-icon capture.
- `work/wheel_probe.ld`: qualified native function addresses relative to rtld.
- `work/build_wheel_probe.py`: executable patches based on the stamina release.
- `work/build_wheel_layout.py`: actual Layout2 changes in all duplicate members.
- `work/hero-wheel-trial`: isolated candidate with main, rtld and ROMFS overrides.

Compile C with clang `--target=aarch64-none-elf -Oz -ffreestanding
-ffunction-sections -fdata-sections -fno-stack-protector`, assemble the trampoline,
link both objects with `ld.lld --gc-sections --undefined=wheel_update --emit-relocs
-e wheel_bind_entry -T work/wheel_probe.ld`, then extract `.text` with
`llvm-objcopy`. Run the executable builder before the layout builder, because
the executable builder refreshes ROMFS from the stamina release.

## Qualified integration points

All addresses below are relative to main unless noted.

- `0x33ca110`: filtered item binding callback. x0 is the list widget, x1 is the
  native ListItemEntry. Entry +0 contains the filtered index.
- `0x33ca1d0`: x21 is the item definition and x19 the bound card widget.
- `0xe9ee30`: constructor capture for PaShortCutSlideList_00.
- `0x33c9270`: shortcut selection update; replaced with direct stick selection.
- `0x3773874`: end of generic list update; scoped to the captured shortcut list
  before changing any icon transforms.
- `0x3774350`: native list selection setter.
- `0x33c9800`: native old/new focus effects.
- `0x33c8f50`: native highlighted-item processing, label and equipped item.

The stock controller +0x68 points at the list widget; controller +0x78 holds
the filtered item count. List +0x60 is the card-pool count, **not inventory count**.
List +0x4c is selected index. Native input is reached through main +0x4e982e0,
then +0xc0. Left stick floats are +0x120 X and +0x124 Y.

Card widget +0x20 -> FrameRoot; +0x80 -> LayoutData; +0x100 -> common pane pool.
The first common pane has **authored local position +0x6c/+0x70** and scale
+0x60/+0x64. +0x4c/+0x50 are derived world-matrix translation, so writes there
are recalculated away. OR its first u32 with 0x6f after writes. The virtual list
rewrites local positions each frame, so one-time edits are insufficient.

## Code placement

Main's existing alignment gap is almost full with stamina. The wheel instead
uses rtld's unused executable text gap at rtld +0x2740..0x3000 (2240 bytes).
The qualified emulator mapping places main at rtld +0x20000. Main's BSS is
extended by another 0x4000 for wheel cache at main +0x4ea1000. No original
module segment is moved. This mapping must be requalified for other loaders.

## Layout

`ShortCut_01.buil` and `PaShortCutSlideList_00.buil` each appear four times in
Common's SARC. Patch every duplicate. BFFH's common-pane map at 0x118 stores
name pointers, descriptor pointers, hashes and count. Transform descriptors
are 68 bytes. Float indices: 4/5 scale, 7/8 position, 11/12 dimensions.

The native virtual list only allocated ten cards with its original viewport.
The trial enlarges virtual coverage so all filtered entries can have a card,
then overrides their geometry after the native list update. It hides stock
scroll arrows, masks, sort panel and selection guide. Existing blur is reused.
Both the scissor and N_SlideList_00 height must be expanded to 2160; expanding
only the scissor still clips the top and bottom of the ring. Live confirmed:
54 card-pool entries, all 18 owned adult item entries bound.

The trial groups bow/arrows, bottles, spells and masks. It leaves the
underlying inventory list intact and maps visible groups to native indices.
Hidden variants have zero card scale. Native selection still handles the
actual item, count and label. The stock animated white cursor outline and glow
follow the focused group; an enlarged card supplements the outline. Confirmed
visually and accepted by the user in the live test.

`0x33c8f50` updates the highlighted item and label; it does **not** commit the
equipped item by itself. `0x33c98f0(controller, 0)` is the stock release/commit
handler for this item slot. Normal wheel release still uses the native path.
Tap cycling explicitly calls it after updating the native selection.

A scheduler bridge preserves the stamina frame call, then processes pending
tap events. A scoped hook at the existing stamina HID epilogue observes real
Npad state without changing its contents. R1 is Npad bit 7. Do not use UI pad
+0x114 as the held mask: it does not provide a reliable held-state signal.
Observe only the full-controller return at main +0x3469670 for Npad ID 0/32.
Combining reads from different controller formats creates false transitions.
The sample counter advanced by 65 during a four-present tap in this build;
the former 12-sample cutoff rejected ordinary taps. Current cutoff: 192.
The raw observer queues events; it never calls game UI functions on the HID
thread. Variant memory survives the stock selector's bow-entry reset, while
a long wheel selection resets that memory to the chosen default item.
The bow's icon changes from `Weapon_Range_Bow` / `Item_Arrow_Fire` to
`Item_Arrow_Normal` / `Pouch_Range_BowAndArrow_Fire` after elemental equip.
Both names must stay in the bow group; otherwise remembered cycling stops at
fire. Do not classify solely by the original icon prefix.

Automated input sequences must explicitly release with `buttons: []` and
`left_stick: [0, 0]`. Omitting fields retains previous input. Avoid interpreting
such an omitted-field test as a stuck input bug in the patch.

Gemini's `build_radial_shortcut_wheel.py` is a conceptual reference: it creates
a JSON specification but does not emit a patched archive. The new builder
actually writes and validates the modified members.

## Remaining acceptance checks

- Child-age filtering, masks, filled bottles, empty and small inventories.
- Broader cancel/sorting and scene-transition qualification.
- Dark glass styling and updated controller guide.
- Controller-settings switches and layout rebinding UI.

## Live qualification, 2026-11-07

Lichii build-93, isolated adult full-inventory arena:

- All 18 entries bind; nine grouped slots render in a complete ring.
- White animated cursor outline/glow follows the focused group. User accepted
  the clearer highlight.
- Native release handler receives index 5 for the lower-left bow slot.
- Repeated taps: arrows `[5,6,7,8,5]`, bottles `[12,13,14,15,16,12]`, spells
  `[9,10,11,9]`. All passed `work/validate_wheel_live.py` in a fresh process.
- With the bow drawn, tapping R1 selected fire arrows and R2 fired one:
  ammo fell from 50 to 49 and the fire effect appeared at impact.
- The original green magic meter still renders correctly.

Saved experimental package: `outputs/OOT-Hero-Wheel-v0.1.zip`. Source and
validation evidence are included. Manual shield and toggle targeting remain
deferred; controller settings and final artwork are not claimed complete.

## Standalone release and tap visibility

`outputs/OOT-Item-Wheel-Standalone-v0.1.zip` is built from original main, rtld
and Common layout files. It includes no stamina, AI, controller remaps or PS5
artwork. Builders: `work/build_standalone_wheel.ps1`,
`work/build_wheel_standalone.py`, `work/wheel_standalone.S/.ld`, shared C and
layout builder. The standalone payload is 2226 bytes in the 2240-byte rtld gap.
Main BSS grows by 0x5000; the wheel cache address remains main +0x4ea1000.

Standalone hooks the original scheduler at main +0x2b30de0, scopes it to vtable
+0x4b05318, processes pending wheel events, and executes the displaced PAC.
It wraps the original full-controller SDK call at +0x346966c directly, rather
than depending on stamina's HID epilogue or its frame function.

The raw observer now receives the returned state count. During the initial
192 samples of a held R press, it clears R only in the returned native state
records (40-byte stride), preventing the stock selector from seeing a tap.
The observer retains the original raw press/release for cycling. Sustained
holds pass R through after the threshold. Other buttons remain untouched.

Independent fresh-process checks passed: four-present tap never reached the
visible wheel update, while a 120-present hold did. Repeated arrows, five
empty bottles and three spell cycles all passed. `work/validate_wheel_hold_gate.py`
and `work/validate_wheel_live.py` save the evidence. User confirmed the tap
no longer shows the wheel and requested to perform further hands-on testing.

Only DualSense has been physically tested. Controllers mapped as a Pro
Controller are expected to share the same Switch R/left-stick path. Joy-Con
and handheld-specific formats are not claimed supported by the tap filter.
The current portable test is running standalone; settings were backed up to
`work/settings-before-standalone-wheel.json`. PS5 artwork merging is disabled
for this independent test. Use `work/start_wheel_standalone_probe.py` for a
research launch; the stamina-specific player-cache helper does not apply.
