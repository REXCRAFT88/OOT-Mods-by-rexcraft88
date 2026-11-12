#ifndef REX_HERO_SETTINGS_H
#define REX_HERO_SETTINGS_H
extern unsigned hero_settings_bits; /* bits 0/1/2 disable stamina/shield/wheel */
void hero_settings_refresh(void);
unsigned hero_stamina_enabled(void);
float hero_stamina_amount(void);
unsigned hero_manual_shield_enabled(void);
unsigned hero_wheel_enabled(void);
unsigned hero_wheel_bumper(void);
unsigned hero_difficulty(void);
unsigned hero_no_recovery_drops(void);
#endif
