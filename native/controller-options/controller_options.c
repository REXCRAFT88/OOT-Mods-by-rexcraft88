typedef unsigned long long U64;
typedef unsigned U32;
extern unsigned char hero_control_state[];
extern void *game_data_singleton;
extern U32 read_enum(void *, U32 *, void *, U32);
extern void native_controls(U64 *, U32);

/* Values already supported by the game's choice enum; labels are row-local. */
#define HOLD 1627154745u
#define TOGGLE 556646631u
#define SWAP_HOLD 957022509u
#define SWAP_TOGGLE 3568908360u /* filled by build script */

static U32 setting(void) {
    unsigned char *g = game_data_singleton;
    if (!g) return HOLD;
    U32 *map = *(U32 **)(g + 0xc20);
    U32 slots = *(U32 *)(g + 0xc2c);
    if (!map || !slots || slots > 1048576) return HOLD;
    U32 start = 0x834d9d9eu % slots, at = start;
    do {
        if (map[at * 2] == 0x834d9d9eu) {
            U32 index = map[at * 2 + 1];
            if (index >= *(U32 *)(g + 0xc10)) return HOLD;
            unsigned char *entry = *(unsigned char **)(g + 0xc18) + index * 32;
            struct { void *entry; U32 index; U32 active; } descriptor = {entry, 0, 0};
            descriptor.active = *(U32 *)(entry + 24) >= 2;
            U32 value = HOLD;
            return read_enum(g, &value, &descriptor, 0xc713c7dau) ? value : HOLD;
        }
        if (!map[at * 2]) break;
        at = at + 1 == slots ? 0 : at + 1;
    } while (at != start);
    return HOLD;
}

void controller_options_raw(U64 *records, U32 count) {
    if (!records || !count || count > 64) return;
    U32 value = setting();
    if (*(U32 *)(hero_control_state+20) != value) {
        hero_control_state[0]=0; hero_control_state[1]=0;
        *(U32 *)(hero_control_state+20)=value;
    }
    *(U64 *)(hero_control_state+24)=records[1];
    U32 swapped = value == SWAP_HOLD || value == SWAP_TOGGLE;
    U32 toggle = value == TOGGLE || value == SWAP_TOGGLE;
    /* Normalize physical buttons before the qualified shield/target policy. */
    if (swapped) for (U32 i = 0; i < count; ++i) {
        U64 bits = records[i * 5 + 1];
        records[i * 5 + 1] = (bits & ~0x140ull) | ((bits & 0x40) << 2) | ((bits & 0x100) >> 2);
    }
    if (!toggle) {
        U32 held = (records[1] & 0x40) != 0;
        hero_control_state[0] = held; /* prevent the original toggle edge */
        hero_control_state[1] = held;
    }
    *(U64 *)(hero_control_state+32)=records[1];
    native_controls(records, count);
}
