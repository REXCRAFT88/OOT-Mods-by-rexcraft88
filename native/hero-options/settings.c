#include "settings.h"
typedef unsigned u32;
typedef unsigned char u8;
extern void *game_data_singleton;
extern u32 settings_read_enum(void *, u32 *, void *, u32);
extern u32 settings_read_bool(void *, u8 *, void *, u32);

#define HOLD 0x60fc6939u
#define SWITCH 0x212dc0e7u
#define NORMAL 0x390b012du
#define PRO 0xd4b93848u

/* A single naturally aligned snapshot: zero is the complete default policy.
   This avoids partial feature combinations during input/frame callbacks. */
u32 hero_settings_bits;
#define settings_bits hero_settings_bits
struct Descriptor { void *entry; u32 index, active; };

static u32 enum_value(void *g, struct Descriptor *d, u32 key, u32 fallback) {
    u32 value = fallback;
    return settings_read_enum(g, &value, d, key) ? value : fallback;
}
static u32 bool_value(void *g, struct Descriptor *d, u32 key, u32 fallback) {
    u8 value = (u8)fallback;
    return settings_read_bool(g, &value, d, key) ? value != 0 : fallback;
}

void hero_settings_refresh(void) {
    u8 *g = game_data_singleton;
    if (!g) return;
    u32 *map = *(u32 **)(g + 0xc20), slots = *(u32 *)(g + 0xc2c);
    if (!map || !slots || slots > 1048576) return;
    const u32 key = 0x834d9d9eu;
    u32 at = key % slots, start = at;
    do {
        if (map[at * 2] == key) {
            u32 index = map[at * 2 + 1];
            if (index >= *(u32 *)(g + 0xc10)) return;
            u8 *entry = *(u8 **)(g + 0xc18);
            if (!entry) return;
            entry += index * 32;
            struct Descriptor d = {entry, 0, *(u32 *)(entry + 24) >= 2};
            u32 bits = 0, value;
            if (!bool_value(g, &d, 0xe86f4645u, 1)) bits |= 1; /* HeroStamina */
            if (!bool_value(g, &d, 0xe21b9fedu, 1)) bits |= 2; /* HeroManualShield */
            if (!bool_value(g, &d, 0x5af5d93au, 1)) bits |= 4; /* HeroItemWheel */
            if (bool_value(g, &d, 0xf1c1f7eeu, 0)) bits |= 8;  /* HeroNoRecoveryDrops */
            value = enum_value(g, &d, 0x9ea340d8u, NORMAL);
            bits |= (value == HOLD ? 1u : value == SWITCH ? 2u : 0u) << 4;
            value = enum_value(g, &d, 0x9fe1614bu, HOLD);
            bits |= (value == SWITCH ? 1u : value == NORMAL ? 2u : 0u) << 6;
            value = enum_value(g, &d, 0x76269af3u, HOLD);
            bits |= (value == SWITCH ? 1u : value == NORMAL ? 2u : value == PRO ? 3u : 0u) << 8;
            settings_bits = bits;
            return;
        }
        if (!map[at * 2]) return;
        at = at + 1 == slots ? 0 : at + 1;
    } while (at != start);
}

unsigned hero_stamina_enabled(void) { return !(settings_bits & 1); }
unsigned hero_manual_shield_enabled(void) { return !(settings_bits & 2); }
unsigned hero_wheel_enabled(void) { return !(settings_bits & 4); }
unsigned hero_no_recovery_drops(void) { return (settings_bits >> 3) & 1; }
float hero_stamina_amount(void) {
    u32 amount = (settings_bits >> 4) & 3;
    return amount == 1 ? .5f : amount == 2 ? 2.0f : 1.0f;
}
unsigned hero_wheel_bumper(void) { return (settings_bits >> 6) & 3; }
unsigned hero_difficulty(void) { return (settings_bits >> 8) & 3; }
