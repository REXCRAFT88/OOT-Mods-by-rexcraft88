SECTIONS { . = 0x2740; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }
/* rtld precedes main by 0x20000 in this qualified process layout. */
wheel_cache = 0x4ec1000;
bind_entry_resume = 0x33ea114;
bind_item_resume = 0x33ea1d4;
list_ctor_resume = 0xebee34;

draw_resume = 0x3793878;
pad_global = 0x4eb82e0;
set_index = 0x3794350;
change_focus = 0x33e9800;
equip_index = 0x33e8f50;

original_hero_frame = 0x3c66574;
commit_item = 0x33e98f0;

full_hid_return = 0x3489670;

hero_controls_raw = 0x4f4c770;

hero_all_input = 0x4f49940;
hero_guard_frame = 0x4f4996c;
