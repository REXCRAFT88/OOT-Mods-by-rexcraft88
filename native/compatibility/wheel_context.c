typedef unsigned long long u64;
typedef unsigned u32;
extern unsigned char wheel_cache[];
#ifdef WHEEL_OPTIONS_ONLY
extern unsigned wheel_bumper_mode(void);

/* The native item selector can pause the gameplay scheduler while its own
   UI continues polling input. Keep the selected bumper mapped during that
   interval; a stale gameplay heartbeat alone must not release the wheel. */
static unsigned wheel_visible(void) {
    unsigned char *controller = *(unsigned char **)(wheel_cache + 48);
    void *list = *(void **)(wheel_cache + 16);
    if (!controller || !list || *(void **)(controller + 0x68) != list) return 0;
    unsigned char *owner = *(unsigned char **)(controller + 0x20);
    unsigned char *screen = *(unsigned char **)(controller + 0x18);
    if (!owner || !screen || owner[0x3a] != 2 || screen[0x1a6] != 2 ||
        (signed char)screen[0x1a5] < 0) return 0;
    u32 items = *(u32 *)(controller + 0x78);
    return items && items <= 64 && *(u32 *)(wheel_cache + 36) == items;
}
#endif
#ifdef HERO_CONTEXT
extern unsigned char hero_runtime[];
#endif

unsigned context_bypass(void) {
#ifdef HERO_CONTEXT
    u32 heartbeat = *(u32 *)(hero_runtime + 136);
#else
    u32 heartbeat = *(u32 *)(wheel_cache + 124);
#endif
    u32 *seen = (u32 *)(wheel_cache + 128);
    u32 *stale = (u32 *)(wheel_cache + 132);
    if (heartbeat == *seen) { if (*stale < 16) ++*stale; }
    else { *seen = heartbeat; *stale = 0; }
    return *(u32 *)(wheel_cache + 120) || *stale > 8;
}

/* Only filter gameplay R input. The native ocarina uses R as a note modifier. */
void wheel_context_raw(u64 *state, unsigned count) {
    if (!state || !count || count > 64) return;
    u32 bypass = context_bypass();
#ifdef WHEEL_OPTIONS_ONLY
    if (bypass && !*(u32 *)(wheel_cache + 120) && wheel_visible())
        bypass = 0;
#endif
    *(u32 *)(wheel_cache + 136) = bypass;
    if (bypass) {
        *(u32 *)(wheel_cache + 68) = 0;
        *(u32 *)(wheel_cache + 112) = 0;
        return;
    }
    u64 sample = state[0];
#ifdef WHEEL_OPTIONS_ONLY
    /* 0=Right, 1=Left, 2=Both. Both bumpers count as one held input. */
    u32 mode = wheel_bumper_mode();
    u64 mask = mode == 1 ? 0x40ull : mode == 2 ? 0xc0ull : 0x80ull;
#else
    u32 mode = 0;
    u64 mask = 0x80ull;
#endif
    u32 held = (state[1] & mask) != 0;
    u32 *last = (u32 *)(wheel_cache + 68);
    u32 elapsed;
    if (held && !*last) *(u64 *)(wheel_cache + 96) = sample;
    if (!held && *last)
        *(u32 *)(wheel_cache + 112) = sample - *(u64 *)(wheel_cache + 96) <= 192 ? 1 : 2;
    *last = held;
    elapsed = held ? (u32)(sample - *(u64 *)(wheel_cache + 96)) : 0;
    if (held && elapsed <= 192) {
        for (unsigned i = 0; i < count; ++i)
            state[i * 5 + 1] &= ~(mask | (mode == 1 ? 0x80ull : 0));
    } else {
        for (unsigned i = 0; i < count; ++i) {
            u64 *buttons = &state[i * 5 + 1];
#ifdef WHEEL_OPTIONS_ONLY
            if (mode == 1) *buttons &= ~0x80ull; /* Right is disabled in Left mode. */
            if (mode && (*buttons & 0x40ull)) {
                *buttons = (*buttons & ~0x40ull) | 0x80ull;
            }
#endif
        }
    }
}
