#ifndef OOT_HERO_CORE_H
#define OOT_HERO_CORE_H
typedef unsigned int u32;
typedef struct {
    float stamina, cap, full_cap, idle_seconds, drain_multiplier;
    u32 initialized, last_action_token, last_impact_token, alive, in_combat;
} HeroState;
typedef struct {
    float units_per_heart, regen_delay, regen_per_second;
    float roll_cost, backflip_cost, sidestep_cost;
    float block_base_cost, block_cost_per_damage_heart;
    float tired_damage, tired_speed;
    float weapon_cost[4]; /* Kokiri, Master, Biggoron, hammer: initial balance only */
    float move_cost_scale[4]; /* slash, thrust, jump attack, spin */
    float low_health_cost_max; /* cost multiplier approached as current life falls */
    float guard_hold_per_second;
} HeroConfig;
typedef struct {
    float dt_seconds;
    u32 life_quarters, max_life_quarters, moving, attacking, guard_held;
    u32 in_combat, exerting; /* jumping, rolling, dodging, sprinting or other exertion */
} HeroInput;
typedef struct { u32 allowed, exhausted, guard_break; float damage_scale, speed_scale, spent; } HeroResult;
enum { HERO_ATTACK=0, HERO_ROLL=1, HERO_BACKFLIP=2, HERO_SIDESTEP=3 };
void hero_default_config(HeroConfig* c);
void hero_tick(HeroState* s,const HeroConfig* c,const HeroInput* in);
HeroResult hero_begin_action(HeroState* s,const HeroConfig* c,u32 action,u32 weapon,u32 move,u32 unique_token);
HeroResult hero_block_impact(HeroState* s,const HeroConfig* c,u32 guard_held,float incoming_damage_hearts,u32 unique_token);
u32 hero_allow_guard(const HeroState* s,u32 guard_held);
#endif
