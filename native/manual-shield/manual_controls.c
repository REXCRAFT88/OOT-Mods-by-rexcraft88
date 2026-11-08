typedef unsigned long long u64;
typedef unsigned u32;
typedef unsigned char u8;

/* Full-controller Npad state records: 40-byte stride, buttons at +8. */
extern u8 hero_control_state[];
extern u64 hero_cache[];
extern u8 hero_runtime[];
extern u64 get_guard_component(void *actor);
typedef void (*set_native_bool)(void *, u32, u32);
extern void native_draw_equipment(void *, u32);
extern u32 as_int(void *,u32);
extern void wheel_raw(u64 *, u32);
extern void native_request_as_original(void *,u32,void *,u32,u32);

void hero_controls_raw(u64 *records, u32 count) {
    if (!records || count == 0 || count > 64) return;
    u32 ticks = *(u32 *)(hero_runtime + 136);
    u32 last_ticks = *(u32 *)(hero_control_state + 8);
    u32 stale_reads = *(u32 *)(hero_control_state + 12);
    if (ticks == last_ticks) ++stale_reads;
    else { last_ticks = ticks; stale_reads = 0; }
    *(u32 *)(hero_control_state + 8) = last_ticks;
    *(u32 *)(hero_control_state + 12) = stale_reads;
    if (stale_reads > 8) {
        hero_control_state[0] = (u8)((records[1] & 0x40u) != 0);
        hero_control_state[2] = 0;
        for(u32 i=0;i<count;++i)records[i*5+1]&=~0x140ull;
        return; /* Reserve L/ZL even while the player scheduler is paused. */
    }
    u32 held_guard = 0;
    u32 held_l = 0;
    u32 held_rstick = 0;
    for (u32 i = 0; i < count; ++i) {
        u64 *buttons = &records[i * 5 + 1];
        u64 bits = *buttons;
        if (i == 0) {
            held_guard = (bits & 0x100u) != 0;   /* L2 / native ZL */
            held_l = (bits & 0x40u) != 0;       /* L1 / native L */
            held_rstick = (bits & 0x20u) != 0;  /* R3 camera reset */
        }
        /* Consume physical guard and L1 selector; native ZL is synthesized below. */
        *buttons = bits & ~0x140ull;
    }

    u32 previous_l = hero_control_state[0];
    u32 targeting = hero_control_state[1];
    if (held_l && !previous_l) targeting ^= 1u;
    if (held_rstick) targeting = 0;
    hero_control_state[0] = (u8)held_l;
    hero_control_state[1] = (u8)targeting;
    hero_control_state[2] = (u8)held_guard;

    if (targeting || held_guard) {
        for (u32 i = 0; i < count; ++i) records[i * 5 + 1] |= 0x100ull;
    }
}

void hero_all_input(u64 *records, u32 count) {
    hero_controls_raw(records, count);
}

void hero_guard_frame(void) {
    u64 player_state = hero_cache[0];
    if (!player_state) return;
    u64 actor = *(u64 *)(player_state + 0x18);
    if (!actor) return;
    u64 component = get_guard_component((void *)actor);
    if (!component) return;

    u32 held = hero_control_state[2] != 0;
    float stamina = *(float *)hero_runtime;
    float cap = *(float *)(hero_runtime + 4);
    u32 initialized = *(u32 *)(hero_runtime + 20);
    u32 alive = *(u32 *)(hero_runtime + 32);
    u32 in_combat = *(u32 *)(hero_runtime + 36);
    u32 allowed = held && initialized && alive && cap > 0.0f && (!in_combat || stamina > 0.0f);
    hero_control_state[4] = (u8)allowed;
    /* Apply held guard policy; native input handles locomotion and camera. */
    u32 *state_flags=(u32 *)(player_state+0xe50);
    if(allowed)*state_flags|=0x80100u;
    else *state_flags&=~0x80000u;
    u32 *flags = (u32 *)(component + 0x24);
    if (allowed) *flags |= 0x20u;
    else *flags &= ~0x20u;

    u64 interface = *(u64 *)(hero_runtime + 0x80);
    if (interface) {
        u64 vtable = *(u64 *)interface;
        set_native_bool setter = (set_native_bool)*(u64 *)(vtable + 0x88);
        setter((void *)interface, 14, allowed);
    }

    /* Draw only the shield: targeting must not make our hook draw the sword. */
    if (allowed && !hero_control_state[3]) {
        u64 table=*(u64 *)(actor+0x270);
        u64 equipment=table?*(u64 *)(table+0x200):0;
        if(equipment&&(!interface||as_int((void *)interface,1)!=2))native_draw_equipment((void *)equipment,4);
    }
    hero_control_state[3] = (u8)allowed;
}

extern void *resolve_player(void *);
void manual_frame(void *ai) {
 u64 state=(u64)resolve_player(ai);if(!state)return;
 hero_cache[0]=state;u64 actor=*(u64 *)(state+0x18);if(!actor)return;
 u64 table=*(u64 *)(actor+0x270);if(!table)return;
 u64 anim=*(u64 *)(table+0x40);if(!anim)return;
 u64 p=*(u64 *)(anim+0x18);if(!p)return;
 p=*(u64 *)(p+0x18);if(!p)return;
 *(u64 *)(hero_runtime+0x80)=*(u64 *)(p+0x40);
 *(float *)hero_runtime=100;*(float *)(hero_runtime+4)=100;
 *(u32 *)(hero_runtime+20)=1;*(u32 *)(hero_runtime+32)=1;
 ++*(u32 *)(hero_runtime+136);hero_guard_frame();
}
