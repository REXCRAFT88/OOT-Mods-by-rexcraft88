SECTIONS { . = 0x4f29770; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }
hero_control_state = 0x4ea3000;
hero_runtime = 0x4ea0800;
hero_cache = 0x4ea0000;
player_as_interface = 0x4ea0880;
wheel_cache = 0x4ea1000;
get_guard_component = 0x974eb0;
native_draw_equipment = 0x6b6820;
original_setter_body = 0x37ba104;
original_setter_early = 0x37ba138;
original_request_body = 0x933274;
original_guard_flags_resume = 0x972e1c;
original_guard_update_resume = 0x973210;

resolve_player = 0x973030;
main_scheduler_vtable = 0x4b05318;
original_frame_body = 0x2b30de4;
sdk_full = 0x3c42800;

main_image = 0;
