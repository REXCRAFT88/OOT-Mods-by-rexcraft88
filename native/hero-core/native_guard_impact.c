typedef unsigned long long U64;
typedef unsigned U32;
extern unsigned char hero_runtime[],hero_control_state[];
extern U64 hero_cache[];
extern void *resolve_player(void *);
/* Entry is the native accepted-guard reaction, not a manual-shield request.
   Native shield/target/equipment policy remains untouched in Hero Core. */
void hero_guard_impact(void *action) {
    if ((U64)resolve_player(action)!=hero_cache[0]) return;
    if (!*(U32 *)(hero_runtime+20)||!*(U32 *)(hero_runtime+32)||
        !*(U32 *)(hero_runtime+36)) return;
    float stamina=*(float *)hero_runtime;
    float cost=*(float *)(hero_runtime+64) * *(float *)(hero_runtime+16);
    if (stamina<=0||cost<=0) return;
    float spent=cost<stamina?cost:stamina;
    *(float *)hero_runtime=stamina-spent;
    *(float *)(hero_runtime+12)=0;
    *(float *)(hero_runtime+168)=spent;
    *(U32 *)(hero_runtime+28)=++*(U32 *)(hero_control_state+64);
}
