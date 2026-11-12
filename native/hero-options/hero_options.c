#include "hero_options.h"
#include "combat_inventory.h"

ho_u32 hero_option_max_life(ho_u32 stock, ho_u32 difficulty) {
    if (!stock) return 0; /* Scripted/non-life actors stay non-life actors. */
    if (difficulty > HO_MYTH) difficulty=HO_WARRIOR;
    unsigned long long result=difficulty==HO_WARRIOR
        ? ((unsigned long long)stock*3+1)/2
        : (unsigned long long)stock*2;
    return result>0x7fffffffu ? 0x7fffffffu : (ho_u32)result;
}

float hero_option_attack_factor(ho_u32 difficulty) {
    /* Relative to the existing 2x enemy attack assets. Native protection,
       collision, blocking and invulnerability are still evaluated by the game. */
    switch(difficulty) {
    case HO_HERO: return 2.0f;
    case HO_LEGEND: return 4.0f;
    case HO_MYTH: return 1000000.0f;
    default: return 1.0f;
    }
}

static int prefix(const char *s,const char *p) {
    while(*p) if(*s++!=*p++) return 0;
    return 1;
}
static int equal(const char *s,const char *p) {
    while(*p) if(*s++!=*p++) return 0;
    return *s==0;
}
int hero_option_is_hostile_name(const char *name) {
    if(!name) return 0;
    if(prefix(name,"Enemy_Scrub_Business") || prefix(name,"Enemy_Skulltula_Gold")) return 0;
    if(prefix(name,"Enemy_")) return 1;
    /* Projectile names are added only after matching the shipped balance
       inventory; do not classify arbitrary fire, falling objects or items. */
    for (unsigned i=0;i<HERO_PROJECTILES;i++)
        if(equal(name,hero_projectile_names[i])) return 1;
    return 0;
}
