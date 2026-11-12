#include "hero_options.h"
#include "combat_bridge.h"
#include "settings.h"
#include "combat_inventory.h"
typedef unsigned long long U64;
typedef unsigned U32;
extern U64 actor_manager_slot;
extern void actor_lock(void *);
extern void actor_unlock(void *);
extern unsigned char native_life_vtable[],native_life_value_vtable[];
static U64 q(U64 p,U32 off){return *(U64 *)(p+off);}
static U32 w(U64 p,U32 off){return *(U32 *)(p+off);}
static int eq(const char *a,const char *b){
    if(!a||!b)return 0;
    for(U32 i=0;i<72;i++){if(a[i]!=b[i])return 0;if(!a[i])return 1;}
    return 0;
}
static U64 name_key(const char *s){
    U64 h=14695981039346656037ull;
    for(U32 i=0;i<72 && s[i];i++){h^=(unsigned char)s[i];h*=1099511628211ull;}
    return h;
}

/* The call site has already loaded the attack multiplier; do not modify its
   shared parameter resource. Keep player fatigue/environment factors intact. */
volatile U64 hero_attack_debug[8];
float hero_enemy_attack_scale(void *source_ai,float input){
    hero_attack_debug[0]++;
    if(!source_ai || !(input>0))return input;
    U64 actor=q((U64)source_ai,0x18);
    hero_attack_debug[1]=actor;
    if(actor<0x10000 || actor>>39 || w(actor,0x2c)-2>4 ||
       !hero_option_is_hostile_name((const char *)q(actor,0x20)))return input;
    U32 tier=hero_difficulty();
    float output=input*hero_option_attack_factor(tier);
    hero_attack_debug[2]++;hero_attack_debug[3]=tier;
    union {float f;U32 u;} in={input},out={output};
    hero_attack_debug[4]=in.u;hero_attack_debug[5]=out.u;
    return output;
}

struct LifeCache {
    U64 actor,life,current,maximum,name;
    U32 stock,last_max,epoch;
};
static struct LifeCache cache[256];
static U32 epoch,scan_ticks,last_tier,walk_budget;
volatile U32 hero_combat_debug[8];

static struct LifeCache *slot(U64 actor){
    U32 start=(U32)((actor>>4)^(actor>>13))&255;
    struct LifeCache *available=0;
    for(U32 i=0;i<256;i++){
        struct LifeCache *p=&cache[(start+i)&255];
        if(p->actor==actor)return p;
        if(p->actor<=1 && !available)available=p;
        if(!p->actor)break;
    }
    return available;
}

/* Only touch plain enemy Life values with known legacy asset provenance.
   GameData-backed values, unknown/custom maxima and progression actors stay
   native. Max/current object identity and source-name identity invalidate the
   cache on component replacement; missing actors are retired after a scan. */
void hero_combat_apply_life(U64 actor,U32 tier,U32 this_epoch){
    if(!actor || w(actor,0x2c)-2>4)return;
    const char *name=(const char *)q(actor,0x20);
    if(!hero_option_is_hostile_name(name))return;
    U64 table=q(actor,0x270);if(!table)return;
    U64 life=q(table,0x2b8);
    if(!life || q(life,0)!=(U64)native_life_vtable || q(life,0x18)!=actor)return;
    U64 cur=q(life,0x1c10),max=q(life,0x1c18);
    if(!cur || !max || q(cur,0)!=(U64)native_life_value_vtable ||
       q(max,0)!=(U64)native_life_value_vtable || w(cur,12) || w(max,12))return;
    U32 old=w(max,8),remaining=w(cur,8);
    if(!old || old>1000000 || remaining>old)return;
    struct LifeCache *p=slot(actor);if(!p){hero_combat_debug[3]++;return;}
    U64 key=name_key(name);
    U32 stock=0;
    if(p->actor==actor && p->life==life && p->current==cur &&
       p->maximum==max && p->name==key && p->last_max==old)stock=p->stock;
    else{
        for(U32 i=0;i<HERO_LIFE_RULES;i++)
            if(hero_life_rules[i].legacy==old && eq(name,hero_life_rules[i].name)){
                stock=hero_life_rules[i].stock;break;
            }
    }
    if(!stock){hero_combat_debug[4]++;return;}
    p->actor=actor;p->life=life;p->current=cur;p->maximum=max;p->name=key;
    p->stock=stock;p->last_max=old;p->epoch=this_epoch;
    hero_combat_debug[0]++;
    if(!remaining)return; /* Do not revive enemies, even when the tier changes. */
    U32 target=hero_option_max_life(stock,tier);
    if(target==old)return;
    U32 current=(U32)(((U64)remaining*target+old-1)/old);
    if(!current)current=1;if(current>target)current=target;
    *(U32 *)(max+8)=target;*(U32 *)(cur+8)=current;
    p->last_max=target;hero_combat_debug[1]++;
}

static void walk(U64 node,U32 tier,U32 depth){
    if(!node || depth>32 || !walk_budget)return;
    --walk_budget;
    walk(q(node,0),tier,depth+1);
    U32 links=0;
    for(U64 entry=node-8;entry && links<256 && walk_budget;entry=q(entry,0x38),links++){
        --walk_budget;hero_combat_apply_life(q(entry,0x28),tier,epoch);
    }
    walk(q(node,8),tier,depth+1);
}

void hero_difficulty_tick(void){
    U32 tier=hero_difficulty();
    if((++scan_ticks&15) && tier==last_tier)return;
    last_tier=tier;
    U64 holder=actor_manager_slot,mgr=holder?q(holder,0):0;if(!mgr)return;
    ++epoch;if(!epoch)++epoch;walk_budget=2048;
    actor_lock((void *)mgr);walk(q(mgr,0x38),tier,0);actor_unlock((void *)mgr);
    for(U32 i=0;i<256;i++)if(cache[i].actor>1 && cache[i].epoch!=epoch)cache[i].actor=1;
    hero_combat_debug[2]++;hero_combat_debug[5]=tier;
}
