#include "hero_core.h"
typedef unsigned long long U64;
typedef struct {
 HeroState state;HeroConfig config;
 U64 player,interface;
 u32 ticks,token,active_mask,last_kind,last_weapon,combat_bool,target_bool;
 float raw_delta,last_spent,damage_scale,speed_scale;
 u32 debug_combat_override;
 U64 bar,ratio,trace,maximum,color,mp_owner;
 float last_stamina,last_capacity,combat_grace,saved_as_rate;
 u32 fatigue_applied;
 U64 attack_param_owner;
 float scaled_damage[32];
} NativeHero;
extern NativeHero hero_runtime;
typedef struct { HeroConfig config; float hud_x,hud_y; u32 magic,version; } UserOptions;
extern UserOptions hero_user_options;
extern void copy_config(HeroConfig *,const HeroConfig *);
extern void* resolve_player(void*);
extern u32 as_bool(void*,u32);
extern u32 as_int(void*,u32);
extern void* find_part(void*,const char*);
extern void* find_anim(void*,const char*);
extern void set_frame(void*,float);
extern U64 hero_cache[];
extern U64 actor_manager_slot;
extern void actor_lock(void*);
extern void actor_unlock(void*);
static U64 ptr(U64 p,u32 off){return *(U64*)(p+off);}
static u32 word(U64 p,u32 off){return *(u32*)(p+off);}
/* Actor manager RB-tree groups; duplicate-name actors form an entry+38 list. */
static u32 near_enemy(U64 node,U64 player){
 if(!node)return 0;
 if(near_enemy(ptr(node,0),player))return 1;
 for(U64 entry=node-8;entry;entry=ptr(entry,0x38)){
  U64 actor=ptr(entry,0x28);if(!actor||word(actor,0x2c)-2>4)continue;
  const char* name=(const char*)ptr(actor,0x20);
  if(!name||*(const u32*)name!=0x6d656e45||*(const unsigned short*)(name+4)!=0x5f79)continue;
  if(*(const u32*)(name+6)==0x75726353&&name[12]=='B')continue; /* friendly business scrub */
  float x=*(float*)(actor+0x31c)-*(float*)(player+0x31c);
  float y=*(float*)(actor+0x320)-*(float*)(player+0x320);
  float z=*(float*)(actor+0x324)-*(float*)(player+0x324);
  if(x*x+y*y+z*z<625)return 1;
 }
 return near_enemy(ptr(node,8),player);
}
static void bar_update(NativeHero* r){
 U64 mp=hero_cache[1];if(!mp)return;
 if(mp!=r->mp_owner){r->mp_owner=mp;r->bar=0;}
 if(!r->bar){
  U64 owner=ptr(mp,0x18);if(!owner)return;
  U64 parent=ptr(owner,0x28);if(!parent)return;
  U64 bar=(U64)find_part((void*)parent,"Pa_StaminaGauge_00");if(!bar)return;
  U64 ratio=(U64)find_anim((void*)bar,"GaugeRatio");
  U64 maximum=(U64)find_anim((void*)bar,"GaugeMax");
  U64 trace=(U64)find_anim((void*)bar,"TraceRatio");
  if(!ratio||!maximum||!trace)return;
  r->color=ptr(ptr(parent,0x80),0x100)+33*0xb0;
  r->bar=bar;r->ratio=ratio;r->maximum=maximum;r->trace=trace;
  *(float*)(r->color+0x6c)+=hero_user_options.hud_x;
  *(float*)(r->color+0x70)+=hero_user_options.hud_y;
  *(u32*)r->color|=0x6f;
  r->last_capacity=-1;r->last_stamina=-1;
 }
 /* Qualified Layout2 common-pane scale, not the unrelated legacy UI Pane API. */
 float show=r->state.in_combat?1:0;
 if(*(float*)(r->color+0x64)!=show){*(float*)(r->color+0x64)=show;*(u32*)r->color|=0x6f;}
 float display_scale=20.0f/r->config.units_per_heart;
 if(r->last_capacity!=r->state.cap){set_frame((void*)r->maximum,r->state.cap*display_scale);r->last_capacity=r->state.cap;}
 if(r->last_stamina!=r->state.stamina){
  U64 transform=ptr(r->ratio,0x20);float length=(float)word(ptr(transform,0),0x28);
  float frame=length-r->state.stamina*display_scale;if(frame<0)frame=0;
  set_frame((void*)r->ratio,frame);set_frame((void*)r->trace,frame);r->last_stamina=r->state.stamina;
 }
}
void hero_native_frame(void* ai,void* update){
 NativeHero* r=&hero_runtime;U64 s=(U64)resolve_player(ai);if(!s)return;hero_cache[0]=s;
 U64 actor=ptr(s,0x18),table=ptr(actor,0x270);if(!table)return;
 U64 life=ptr(table,0x2b8);if(!life)return;
 U64 cur=ptr(life,0x1c10),max=ptr(life,0x1c18);
 if(!cur||!max||word(cur,12)!=0x31ab5580||word(max,12)!=0xfbe01da1)return;
 u32 maximum=word(max,8);if(!maximum||maximum>80)return;
 if(r->player!=s){r->state.initialized=0;r->active_mask=0;r->fatigue_applied=0;r->player=s;}
 if(!r->state.initialized)copy_config(&r->config,&hero_user_options.config);
 U64 anim=ptr(table,0x40);U64 a=ptr(anim,0x18);a=ptr(a,0x18);a=ptr(a,0x40);r->interface=a;
 if(!(r->ticks&15)){
  U64 holder=actor_manager_slot;U64 mgr=holder?ptr(holder,0):0;
  if(mgr){actor_lock((void*)mgr);r->combat_bool=near_enemy(ptr(mgr,0x38),actor);actor_unlock((void*)mgr);}
 }
 r->target_bool=as_bool((void*)a,41);
 float dt=*((float*)update+2);r->raw_delta=dt;
 HeroInput in={0};in.dt_seconds=dt>0&&dt<10?dt/60:0;
 in.life_quarters=word(cur,8);in.max_life_quarters=maximum;
 if(r->combat_bool||r->target_bool)r->combat_grace=5;
 else if(r->combat_grace>0)r->combat_grace-=in.dt_seconds;
 in.in_combat=r->combat_grace>0;
 if(r->debug_combat_override)in.in_combat=r->debug_combat_override==1;
 in.attacking=(r->active_mask&((1u<<0)|(1u<<5)|(1u<<6)))!=0;
 in.exerting=(r->active_mask&~1u)!=0;
 in.guard_held=as_bool((void*)a,14)&&!in.attacking;
 hero_tick(&r->state,&r->config,&in);
 u32 tired=in.attacking&&r->state.in_combat&&r->speed_scale>0&&r->speed_scale<1;
 if(tired){if(!r->fatigue_applied){r->saved_as_rate=*(float*)(anim+0x98);r->fatigue_applied=r->saved_as_rate>0;}if(r->fatigue_applied)*(float*)(anim+0x98)=r->saved_as_rate*r->speed_scale;}
 else if(!tired&&r->fatigue_applied){*(float*)(anim+0x98)=r->saved_as_rate;r->fatigue_applied=0;}
 r->ticks++;bar_update(r);
}
void hero_native_action(u32 kind,u32 entering){
 NativeHero* r=&hero_runtime;
 if(!entering){r->active_mask&=~(1u<<kind);return;}
 if(!r->state.initialized)return;
 r->active_mask|=1u<<kind;r->last_kind=kind;
 u32 action=(kind==1||kind==4)?HERO_ROLL:kind==2?HERO_BACKFLIP:kind==3?HERO_SIDESTEP:HERO_ATTACK;
 u32 weapon=as_int((void*)r->interface,1);
 /* ASB class2 is the two-handed sword branch; CutHammer selects the hammer pose. */
 u32 profile=as_bool((void*)r->interface,86)?3:weapon==2?2:as_bool((void*)r->interface,11)?0:1;
 u32 move=kind==5?3:kind==6?2:as_int((void*)r->interface,14)==5?1:0;
 HeroResult result=hero_begin_action(&r->state,&r->config,action,profile,move,++r->token);
 r->last_spent=result.spent;r->damage_scale=result.damage_scale;r->speed_scale=result.speed_scale;
}
u32 hero_native_allow(u32 kind){
 NativeHero* r=&hero_runtime;if(!r->state.initialized||!r->state.in_combat)return 1;
 float cost=(kind==1||kind==4)?r->config.roll_cost:kind==2?r->config.backflip_cost:r->config.sidestep_cost;
 return r->state.stamina>=cost*r->state.drain_multiplier;
}
