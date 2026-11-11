typedef unsigned u32;
typedef unsigned char u8;
typedef unsigned long long u64;

extern void *game_data_singleton;
extern u32 read_enum(void *, u32 *, void *, u32);

/* Temporary C6 diagnostics: populated by the live option initializer. */
void *wheel_option_live_list;
void *wheel_option_live_descriptor;
void *wheel_option_live_vtable;
void *wheel_option_live_setter;

#define WHEEL_BUMPER_FIELD 0xd9749f3eu
#define WHEEL_BUMPER_OPTION 0x916ac217u /* stock-supported hidden OptionType */
#define BUMPER_RIGHT       0x60fc6939u /* native Hold choice */
#define BUMPER_LEFT        0x212dc0e7u /* native Switch choice */
#define BUMPER_BOTH        0x390b012du /* native Normal choice */

u64 wheel_bumper_mask(unsigned mode) {
    return mode == 1 ? 0x40ull : mode == 2 ? 0xc0ull : 0x80ull;
}

u64 wheel_bumper_remap(unsigned mode, u64 buttons) {
    if (mode && (buttons & 0x40ull))
        return (buttons & ~0x40ull) | 0x80ull;
    return buttons;
}

/* Return 0=Right, 1=Left, 2=Both; missing or invalid values keep Right. */
unsigned wheel_bumper_mode(void) {
    u8 *g = (u8 *)game_data_singleton;
    if (!g) return 0;
    u32 *map = *(u32 **)(g + 0xc20);
    u32 slots = *(u32 *)(g + 0xc2c);
    if (!map || !slots || slots > 1048576) return 0;

    const u32 map_hash = 0x834d9d9eu;
    u32 at = map_hash % slots, start = at;
    do {
        if (map[at * 2] == map_hash) {
            u32 index = map[at * 2 + 1];
            if (index >= *(u32 *)(g + 0xc10)) return 0;
            u8 *entry = *(u8 **)(g + 0xc18) + index * 32;
            struct { void *entry; u32 index; u32 active; } descriptor = {
                entry, 0, *(u32 *)(entry + 24) >= 2
            };
            u32 value = BUMPER_RIGHT;
            if (!read_enum(g, &value, &descriptor, WHEEL_BUMPER_OPTION)) return 0;
            if (value == BUMPER_LEFT) return 1;
            if (value == BUMPER_BOTH) return 2;
            return 0;
        }
        if (!map[at * 2]) break;
        at = at + 1 == slots ? 0 : at + 1;
    } while (at != start);
    return 0;
}

/* Called at the end of the native option-list initializer, with its live
   GameData descriptor and list object. Read through the pending-aware native
   enum accessor so menu changes are reflected before GameData flushes them. */
void wheel_option_append(void *game_data, void *descriptor, void *list) {
    if (!game_data || !descriptor || !list) return;
    wheel_option_live_list = list;
    wheel_option_live_descriptor = descriptor;
    u32 value = BUMPER_RIGHT;
    u32 index = 0;
    if (read_enum(game_data, &value, descriptor, WHEEL_BUMPER_OPTION)) {
        if (value == BUMPER_LEFT) index = 1;
        else if (value == BUMPER_BOTH) index = 2;
    }

    struct WheelLabel {
        const char *data;
        u32 capacity;
        char inline_data[64];
    } label;
    label.data = label.inline_data;
    label.capacity = sizeof(label.inline_data);
    const char title[] = {
        'M','e','s','s','a','g','e','W','i','n','d','o','w','T','r','a','n','s','p','a','r','e','n','c','y',0
    };
    for (u32 i = 0; i < sizeof(title); ++i) label.inline_data[i] = title[i];
    for (u32 i = sizeof(title); i < sizeof(label.inline_data); ++i)
        label.inline_data[i] = 0;

    void **vtable = *(void ***)list;
    wheel_option_live_vtable = vtable;
    if (!vtable) return;
    wheel_option_live_setter = vtable[0x58 / sizeof(void *)];
    if (!wheel_option_live_setter) return;
    void (*append)(void *, const struct WheelLabel *, u32) =
        (void (*)(void *, const struct WheelLabel *, u32))vtable[0x58 / sizeof(void *)];
    append(list, &label, index);
}
