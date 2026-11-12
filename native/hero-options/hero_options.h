#ifndef HERO_OPTIONS_H
#define HERO_OPTIONS_H
typedef unsigned int ho_u32;
enum { HO_WARRIOR, HO_HERO, HO_LEGEND, HO_MYTH };
/* Stock values, before the legacy Hero asset multipliers. */
ho_u32 hero_option_max_life(ho_u32 stock, ho_u32 difficulty);
float hero_option_attack_factor(ho_u32 difficulty);
int hero_option_is_hostile_name(const char *name);
#endif
