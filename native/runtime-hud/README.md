# Private runtime HUD — Hero with Stamina beta.10

Exact build E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348, update131072. Prepared addons need no commands. The optional manifest builder reconstructs checked files from the user's game.

`hud.c` and `hud.S` hook main+0x43a6f8: x0 is a UI handle, x1 a build config whose first pointer is relocated UIL data. Handle+0x30 is the instance name. Core initialization at0x1525b60 allocates pane arrays from resource counts, so metadata is substituted before allocation. The config copy is0x100 bytes; truncating it loses a required+0x80 field.

PlayerStatus gets private header/tables/root/part descriptors and a new Pa_StaminaGauge_00 instance of the stock PaMpGauge_00 asset. That instance alone receives a relocated gauge copy, stock White8_00_BC4L, and private palettes at BFFH+0x74d8/+0x74e8. Magic stays untouched. UIL Common/Parts tables are at+0x20/+0xc0; descriptor sizes68/88. Runtime panes are resolved by name (not index33), stride0xb0, local scale+0x60/+0x64, translation+0x6c/+0x70. Geometry: X1/Y0.5, root(-1560,736) plus configurable offsets. `stamina_bridge.c` also uses visible Y0.5 on combat entry. Private wheel resources widen virtualized list/scissor bounds and hide stock masks.

Our minimal subsdk1 begins main-relative0x4f85000, VM size0x80000. Fixed exports: trampoline0x4f85100, pane lookup0x4f85104. SDK shifts to0x5005000; its bridge must be relinked at0x5883850. Keep main's original text extent0x3c461d0 and FPS/ultrawide caves0x3c46200..0x3c46600 untouched. No absolute static pointer tables: the minimal module has no dynamic relocation entries, so helper references must be PC-relative.

Build the helper: `python native/runtime-hud/build_module.py <output-directory>` (clang/ld.lld.exe/LLVM tools/cityhash). `check_resources.py <output-directory>` runs compiled AArch64 changes with nonzero ASLR (Unicorn). Full native builds additionally need the existing research-workspace baselines and compatibility/controller bridges relinked for the new SDK address. `apply_candidate.py` finalizes that intermediate. The optional manifest installer is the supported fresh-checkout reconstruction route and does not need the research workspace.

Wheel regression: generic list constructor main+0xe9ee30 overwrote wheel_cache+16 on menu creation. Restore its stock entry and let specific item binding populate cache+16 instead of debug-only cache+0/+8. Equivalent source fixes are in wheel_probe.S/wheel_standalone.S. `check_wheel_binding.py` checks compiled cache/register/stack behavior. Live tests covered repeated menu/tab visits with full DualSense UI.

Metadata caches are bounded and fall back to originals when full. No per-frame heap allocation/archive rebuilding. Long-session/reload coverage is limited. Hookshot's matching AOT image/address-labelled symbols helped cross-check code; this is not high-level Hookshot game source. Hookshot's overlay loader does not apply these ExeFS patches.

See ../../docs/HUD-COMPATIBILITY.md for font allocation16384 and the tested separate-addon priority. Do not redistribute third-party font/texture assets in Hero.
