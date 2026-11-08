/* Two-handed equipment must not trigger an extra sword or shield draw. */
typedef unsigned u32;
extern void *player_as_interface;
extern u32 as_int(void *,u32);
extern void native_draw_equipment(void *,u32);
void hero_guard_draw(void *equipment,u32 slot){
 if(player_as_interface && as_int(player_as_interface,1)==2)return;
 native_draw_equipment(equipment,slot);
}
