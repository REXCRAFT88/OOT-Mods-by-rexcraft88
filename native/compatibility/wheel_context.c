typedef unsigned long long u64;
typedef unsigned u32;
extern unsigned char wheel_cache[];
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
    *(u32 *)(wheel_cache + 136) = bypass;
    if (bypass) {
        *(u32 *)(wheel_cache + 68) = 0;
        *(u32 *)(wheel_cache + 112) = 0;
        return;
    }
    u64 sample = state[0];
    u32 held = (state[1] & 128) != 0;
    u32 *last = (u32 *)(wheel_cache + 68);
    if (held && !*last) *(u64 *)(wheel_cache + 96) = sample;
    if (!held && *last)
        *(u32 *)(wheel_cache + 112) = sample - *(u64 *)(wheel_cache + 96) <= 192 ? 1 : 2;
    *last = held;
    if (held && sample - *(u64 *)(wheel_cache + 96) <= 192)
        for (unsigned i = 0; i < count; ++i) state[i * 5 + 1] &= ~128ull;
}
