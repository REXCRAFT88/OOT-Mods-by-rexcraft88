#include "hero_core.h"
static float minf(float a,float b){return a<b?a:b;}
static float maxf(float a,float b){return a>b?a:b;}
static HeroResult normal(void){HeroResult r={1,0,0,1.0f,1.0f,0.0f};return r;}
void hero_default_config(HeroConfig* c){
    c->units_per_heart=20;c->regen_delay=1.25f;c->regen_per_second=8;
    c->roll_cost=12;c->backflip_cost=10;c->sidestep_cost=8;
    c->block_base_cost=8;c->block_cost_per_damage_heart=4;
    c->tired_damage=.5f;c->tired_speed=.75f;
    c->weapon_cost[0]=8;c->weapon_cost[1]=12;c->weapon_cost[2]=18;c->weapon_cost[3]=20;
    c->move_cost_scale[0]=1;c->move_cost_scale[1]=1.1f;c->move_cost_scale[2]=1.5f;c->move_cost_scale[3]=1.8f;
    c->low_health_cost_max=2.0f;
    c->guard_hold_per_second=2.0f;
}
void hero_tick(HeroState* s,const HeroConfig* c,const HeroInput* in){
    float unit=maxf(c->units_per_heart,0)*.25f;
    s->full_cap=in->max_life_quarters*unit;
    s->cap=s->full_cap;
    float health=in->max_life_quarters?minf((float)in->life_quarters/(float)in->max_life_quarters,1.0f):0;
    s->drain_multiplier=1.0f+(maxf(c->low_health_cost_max,1.0f)-1.0f)*(1.0f-health);
    s->alive=in->life_quarters>0&&in->max_life_quarters>0;
    s->in_combat=in->in_combat!=0;
    if(!s->initialized){s->stamina=s->cap;s->idle_seconds=0;s->last_action_token=0;s->last_impact_token=0;s->initialized=1;}
    s->stamina=minf(maxf(s->stamina,0),s->cap);
    if(!s->alive){s->stamina=0;s->idle_seconds=0;return;}
    if(!s->in_combat){s->stamina=s->cap;s->idle_seconds=0;return;}
    if(in->guard_held){
        if(in->dt_seconds>0 && in->dt_seconds<10)
            s->stamina=maxf(0,s->stamina-in->dt_seconds*maxf(c->guard_hold_per_second,0)*s->drain_multiplier);
        s->idle_seconds=0;return;
    }
    if(in->attacking||in->exerting){s->idle_seconds=0;return;}
    if(in->dt_seconds>0 && in->dt_seconds<10){
        float before=maxf(0,s->idle_seconds-c->regen_delay);
        s->idle_seconds+=in->dt_seconds;
        float after=maxf(0,s->idle_seconds-c->regen_delay);
        s->stamina=minf(s->cap,s->stamina+(after-before)*maxf(c->regen_per_second,0));
    }
}
HeroResult hero_begin_action(HeroState* s,const HeroConfig* c,u32 action,u32 weapon,u32 move,u32 token){
    HeroResult r=normal();float cost;
    if(!s->initialized||!s->alive||s->cap<=0){r.allowed=0;return r;}
    /* The bridge must provide a non-zero, monotonically changing accepted-action token. */
    if(token==0||token==s->last_action_token){r.allowed=0;return r;}
    if(!s->in_combat){
        if(action>HERO_SIDESTEP||(action==HERO_ATTACK&&(weapon>=4||move>=4))){r.allowed=0;return r;}
        s->last_action_token=token;return r;
    }
    if(action==HERO_ATTACK){
        if(weapon>=4||move>=4){r.allowed=0;return r;}
        cost=maxf(c->weapon_cost[weapon]*c->move_cost_scale[move],0)*s->drain_multiplier;
        if(s->stamina<cost){r.exhausted=1;r.damage_scale=c->tired_damage;r.speed_scale=c->tired_speed;}
    }else if(action==HERO_ROLL)cost=c->roll_cost;
    else if(action==HERO_BACKFLIP)cost=c->backflip_cost;
    else if(action==HERO_SIDESTEP)cost=c->sidestep_cost;
    else{r.allowed=0;return r;}
    cost=maxf(cost,0);
    if(action!=HERO_ATTACK)cost*=s->drain_multiplier;
    if(action!=HERO_ATTACK&&s->stamina<cost){r.allowed=0;return r;}
    s->last_action_token=token;r.spent=minf(s->stamina,cost);s->stamina-=r.spent;s->idle_seconds=0;return r;
}
HeroResult hero_block_impact(HeroState* s,const HeroConfig* c,u32 held,float damage,u32 token){
    HeroResult r=normal();
    if(!held||!s->initialized||!s->alive||token==0||token==s->last_impact_token){r.allowed=0;return r;}
    s->last_impact_token=token;
    if(!s->in_combat)return r;
    float cost=maxf(c->block_base_cost+maxf(damage,0)*c->block_cost_per_damage_heart,0)*s->drain_multiplier;
    r.guard_break=s->stamina<=0||s->stamina<cost;
    r.spent=minf(s->stamina,cost);s->stamina-=r.spent;s->idle_seconds=0;return r;
}
u32 hero_allow_guard(const HeroState* s,u32 held){return held&&s->initialized&&s->alive&&s->cap>0&&(!s->in_combat||s->stamina>0);}
