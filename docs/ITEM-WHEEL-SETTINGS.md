# Standalone Item Wheel 0.1.7

In the game's **System → Options**, set **Wheel Bumper** to **Right**, **Left**, or **Both**. Right is the default. Hold the selected bumper to open the wheel; tap it to cycle variants of the selected item, such as bottles or arrow types, without showing the wheel. Either stick can select an item. Release the bumper to close the wheel.

The setting uses the game's saved account options. It does not change your emulator controller profile. On DualSense, the bumpers are R1 and L1; on Xbox-style controllers, RB and LB. Other controller types use their mapped equivalents; exhaustive controller testing has not been performed. Normal menu and ocarina inputs bypass the gameplay wheel remapping.

## Install

1. Download the **Prepared-Addon.zip** from the Item Wheel 0.1.7 release.
2. Disable or remove the older standalone wheel addon.
3. Right-click the original game in the emulator, choose **Configure Game → Add-Ons → Import Mod from ZIP**, and select the complete downloaded ZIP.
4. Enable the imported addon, apply the settings, and start the game.

No command prompt, patched NUP or optional builder is needed. Requires game update 131072 / version 2.0.0 and the supported executable build listed in the manifest. Use one native gameplay package: do not stack this standalone addon with Manual Shield, combined Wheel + Shield, or full Hero Mode, which replace the same executable files. The combined package remains a separate release; its settings have not been updated by this standalone release.

## Validation and limitations

The tester confirmed the three-choice setting and the subsequent Left-hold stability fix in the isolated Fritchii 5.8 test. The test retained DualSense UI, reused shader caches, and disabled ultrawide patches. Automated AArch64 checks cover bumper routing, held-wheel input during a paused gameplay heartbeat, tap/release behavior, menu/ocarina bypass, and menu selection initialization. Full process-restart persistence and every controller/scene/visual-mod combination have not been independently qualified for this revision.

## Modder notes

- `native/wheel/build_wheel_options_resources.py` adds the option row, localized labels and independent GameData enum. The supported hidden UI OptionType `916ac217` maps through UserSettings to field `d9749f3e`.
- BYML `Enum.Values` uses type `d5`: each array entry points to an eight-byte UInt64 hash payload. It is **not** a string-table index. The generator reparses and validates all three payloads; malformed entries display labels but reject changes.
- The row needs multi-choice ButtonType `d4c0f4d3`; `bcbe684c` produces a binary On/Off switch.
- `native/wheel/wheel_options.c` reads the alias through pending-aware native enum accessor `404760`. Native dropdown apply at `33cfdec` invokes normal GameData writer `9b3ba0`; no custom disk-save hook is added.
- `native/compatibility/wheel_context.c` routes the selected physical bumper to native Right. During a validated active wheel, a paused gameplay heartbeat must not stop Left-to-Right translation. Explicit ocarina bypass still wins.
- The alias is also used for shield swapping in other packages. Do not copy this standalone options resource into Hero or combined packages without resolving that field collision.
- `native/wheel/check_wheel_options.py` and `check_wheel_option_menu.py` exercise compiled AArch64 code. Resource generation requires the development workspace's game-asset readers; normal users install the prepared addon.

No enemy, stamina, shield or targeting changes are included in this standalone release.
