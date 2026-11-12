# Native Hero OptionType extension

`menu_patch.py` describes the native half of the seven Hero options. It keeps
stock option IDs 0–17 intact and assigns new IDs 18–24 to
`HeroStamina`, `HeroStaminaAmount`, `HeroManualShield`, `HeroItemWheel`,
`HeroWheelBumper`, `HeroDifficulty`, and `HeroNoRecoveryDrops`.

The private module exports three symbols consumed by the guarded main-text
patch plan: `hero_menu_hash_to_enum_id`,
`hero_menu_byml_option_type_reader`, and `hero_menu_option_names`. The
`hero_menu_byml_option_type_reader` assembly bridge handles custom D3 hashes
and tail-branches to the stock parser prologue for stock or unknown hashes.
`hero_menu_hash_to_enum_id` covers all 25 hashes, returning `-1` for unknown
hashes. The generated rodata assembly contains the copied stock hash/name
tables, the complete sorted permutation, then the seven additions.

Candidate builder integration:

1. Construct a native virtual-address image containing the original text and
   decompressed rodata at 0x3c47000. Call
   `menu_patch.emit_module_data_assembly(image)` and assemble the
   result with `menu_native.c` and `menu_native.S` into the private module.
2. Resolve the three required symbols from that module ELF.
3. Call `menu_patch.build_plan(image, symbols)` and
   `menu_patch.apply_plan(main_text_mutable, plan)` before emitting main.
   This replaces the hash lookup and BYML reader entry points, relocates all
   eight inline name/field-table pairs, and raises each inline maximum ID from 17
   to 24. Stock instruction bytes are validated before any patch is applied.

The stock name table uses signed 32-bit string offsets, not 64-bit offsets.
The native field-hash initializer at 0x339c2f8 originally uses ADRP/LDR via
GOT 0x4c8c958; the other seven sites use ADRP/ADD. Missing the initializer
allows labels to appear but produces zero field hashes, so choices do not
save. The guarded plan validates both instruction forms and the nearby
`CMP #17` bounds. The parser's stock fallback replays PACIBSP and branches
to the imported original body at 0x339ab44, preserving relocation and ABI.
The custom parser returns success after restoring its stack/registers.

These sites were checked against the actual executable, including execution
of all 25 hash/parser cases and all eight inline lookups at two ASLR bases.
Host helper checks:

```text
python native/hero-options/menu_patch_test.py
```
