#include <stdint.h>

/* menu_patch.py emits this 25-word array into module .rodata. */
extern const uint32_t hero_menu_option_hashes[25];

/* Stock enum IDs remain 0..17; custom IDs are appended as 18..24. */
int32_t hero_menu_hash_to_enum_id(uint32_t hash) {
    for (int32_t i = 0; i < 25; ++i) {
        if (hero_menu_option_hashes[i] == hash) return i;
    }
    return -1;
}
