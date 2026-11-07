SECTIONS { . = 0x3c461d0; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }
hero_cache = 0x4ea0000;
hero_runtime = 0x4ea0800;
resolve_player = 0x973030;
as_bool = 0x37bb4c0;
as_int = 0x37bb2c0;
frame_resume = 0x2b30de4;
main_scheduler_vtable = 0x4b05318;
player_resume = 0x7f9b20;
mp_resume = 0x33be064;
attack_enter_resume = 0xa3fb50;
attack_leave_resume = 0x7a0764;
roll_enter_resume = 0x6b9a34;
roll_leave_resume = 0x9390b4;
back_enter_resume = 0x2795984;
back_leave_resume = 0x2796394;
side_enter_resume = 0x800b74;
side_leave_resume = 0x800624;
jump_enter_resume = 0x93a9b4;
jump_leave_resume = 0xb397c4;
spin_enter_resume = 0x27c6ac4;
spin_leave_resume = 0x27c7364;
jumpattack_enter_resume = 0xa42024;
jumpattack_leave_resume = 0x92c164;
roll_gate_resume = 0x7f4c54;
back_gate_resume = 0x7f4f74;
side_gate_resume = 0x7f6c34;
jump_gate_resume = 0x7f6264;

find_part = 0x43c3e0;
find_anim = 0x43c7a0;
set_frame = 0x2d2d90;
mp_init_resume = 0x33bdce4;

root_pane = 0x209650;
pane_visible = 0x20aea0;

sdk_full = 0x3c42800; sdk_dual = 0x3c427f0; sdk_left = 0x3c42810; sdk_right = 0x3c42820; sdk_handheld = 0x3c42830;

get_as_rate = 0xdf49b0;
set_as_rate = 0xdf48e0;

damage_resume = 0x2de4344;

damage_call_return = 0x8d2d54;

actor_manager_slot = 0x4c7dc40;
actor_lock = 0x3c42460;
actor_unlock = 0x3c42470;
