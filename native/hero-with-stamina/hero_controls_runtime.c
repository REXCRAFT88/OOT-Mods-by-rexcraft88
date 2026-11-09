typedef unsigned long long u64;
typedef unsigned u32;
typedef unsigned char u8;

/* Full-controller Npad state records: 40-byte stride, buttons at +8. */
extern u8 hero_control_state[];
extern u64 hero_cache[];
extern u8 hero_runtime[];
extern u8 wheel_cache[];
extern u64 get_guard_component(void *actor);
typedef void (*set_native_bool)(void *, u32, u32);
extern void native_draw_equipment(void *, u32);
extern u32 as_int(void *,u32);
extern u32 as_bool(void *,u32);
extern void wheel_raw(u64 *, u32);
extern void native_request_as_original(void *,u32,void *,u32,u32);
extern void *resolve_player(void *);
u32 hero_guard_busy(u64 interface,u64 player_state);
u32 hero_guard_should_apply(u64 interface,u64 player_state,u32 held,u32 initialized,u32 alive,u32 combat,float cap,float stamina);
static u64 current_guard_interface(u64 actor) {
    u64 table=*(u64 *)(actor+0x270);if(!table)return 0;
    u64 anim=*(u64 *)(table+0x40);if(!anim)return 0;
    u64 p=*(u64 *)(anim+0x18);if(!p)return 0;
    p=*(u64 *)(p+0x18);if(!p)return 0;
    return *(u64 *)(p+0x40);
}
__attribute__((noinline)) u32 hero_player_carrying(u64 actor) {
    if(!actor)return 0;
    u64 table=*(u64 *)(actor+0x270);if(!table)return 0;
    u64 lifter=*(u64 *)(table+0x2c8);if(!lifter)return 0;
    return *(u32 *)(lifter+0x2b0)!=0;
}
__attribute__((noinline)) u32 hero_input_guard_active(u64 buttons) {
    return (buttons & 0x100u) != 0 && !hero_control_state[5];
}

/* ExecutePlayerReactionGuard Enter: native code has accepted a real block.
   Never charge merely for raising the shield or for a different actor. */
void hero_guard_impact(void *action) {
    if((u64)resolve_player(action)!=hero_cache[0]||!hero_control_state[4])return;
    if(!*(u32 *)(hero_runtime+20)||!*(u32 *)(hero_runtime+32)||
       !*(u32 *)(hero_runtime+36))return;
    float stamina=*(float *)hero_runtime;
    float cost=(*(float *)(hero_runtime+64)) * (*(float *)(hero_runtime+16));
    if(stamina<=0.0f||cost<=0.0f)return;
    float spent=cost<stamina?cost:stamina;
    *(float *)hero_runtime=stamina-spent;
    *(float *)(hero_runtime+12)=0.0f;
    *(float *)(hero_runtime+168)=spent;
    u32 token=++*(u32 *)(hero_control_state+64);
    *(u32 *)(hero_runtime+28)=token;
    *(float *)(hero_control_state+68)=spent;
}

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
            held_guard = hero_input_guard_active(bits); /* L2 / native ZL */
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
    wheel_raw(records,count);
    hero_controls_raw(records, count);
}

void hero_guard_frame(void) {
    *(u64 *)(hero_control_state + 0x70) = 0;
    *(u64 *)(hero_control_state + 0x78) = 0;
    hero_control_state[4] = 0;
    hero_control_state[5] = 0;
    u64 player_state = hero_cache[0];
    if (!player_state) return;
    u64 actor = *(u64 *)(player_state + 0x18);
    if (!actor) return;
    hero_control_state[5] = (u8)hero_player_carrying(actor);
    u64 component = get_guard_component((void *)actor);
    if (!component) return;

    u32 held = hero_control_state[2] != 0;
    float stamina = *(float *)hero_runtime;
    float cap = *(float *)(hero_runtime + 4);
    u32 initialized = *(u32 *)(hero_runtime + 20);
    u32 alive = *(u32 *)(hero_runtime + 32);
    u32 in_combat = *(u32 *)(hero_runtime + 36);
    u64 interface = *(u64 *)(hero_runtime + 0x80);
    if (!interface || interface != current_guard_interface(actor)) interface=0;
    u64 table=*(u64 *)(actor+0x270);
    u64 equipment=table?*(u64 *)(table+0x200):0;
    if(interface) *(u64 *)(hero_control_state+0x70)=actor;
    if(interface&&equipment) *(u64 *)(hero_control_state+0x78)=equipment;
    /* Let native item/AS ownership keep both hands during aiming, carrying,
       block movement, hammer use, and ocarina playback. */
    u32 allowed = interface && hero_guard_should_apply(interface,player_state,held,initialized,alive,in_combat,cap,stamina);
    hero_control_state[4] = (u8)allowed;
    /* Match the native mobile guard flag without requesting target/camera. */
    u32 *state_flags=(u32 *)(player_state+0xe50);
    if(allowed)*state_flags|=0x80100u;
    else *state_flags&=~0x80000u;
    u32 *flags = (u32 *)(component + 0x24);
    if (allowed) *flags |= 0x20u;
    else *flags &= ~0x20u;

    if (interface) {
        u64 vtable = *(u64 *)interface;
        set_native_bool setter = (set_native_bool)*(u64 *)(vtable + 0x88);
        setter((void *)interface, 14, allowed);
    }

    /* Draw only the shield: targeting must not make our hook draw the sword. */
    if (allowed && !hero_control_state[3]) {
        if(equipment&&(!interface||as_int((void *)interface,1)!=2))native_draw_equipment((void *)equipment,4);
    }
    hero_control_state[3] = (u8)allowed;
}

static u32 guard_action_busy(u64 player_state) {
    if(!player_state)return 0;
    for(u32 i=0;i<2;i++){
        const u8* name=(const u8 *)*(u64 *)(player_state+0x238+i*0xd8);
        if(!name)continue;
        u64 first=*(const u64 *)name;
        if(first==0x6d657449646c6f48ull || *(const u32 *)name==0x7466694c ||
           *(const u32 *)name==0x62617247 || first==0x6772616843776f42ull ||
           first==0x746f6f6853776f42ull || first==0x616f4c6552776f42ull ||
           first==0x746f68736b6f6f48ull || first==0x6e6172656d6f6f42ull ||
           first==0x6573726f486d6941ull) return 1; /* Hold/Lift/Grab; bow, hookshot, boomerang, horse aim */
    }
    return 0;
}
__attribute__((noinline)) u32 hero_guard_busy(u64 interface,u64 player_state) {
    return interface && (hero_control_state[5] || (*(u32 *)(wheel_cache+120)!=0) || guard_action_busy(player_state) ||
        as_bool((void *)interface,62) ||
        as_bool((void *)interface,86) ||
        as_int((void *)interface,1)==2);
}

__attribute__((noinline)) u32 hero_guard_should_apply(u64 interface,u64 player_state,u32 held,u32 initialized,
                                                       u32 alive,u32 combat,float cap,float stamina) {
    return interface && held && !hero_guard_busy(interface,player_state) && initialized && alive && cap>0.0f &&
           (!combat || stamina>0.0f);
}


void *hero_as_request(void *state,u32 slot,void *name_ref) { return name_ref; }
