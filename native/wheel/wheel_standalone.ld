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

main_scheduler_vtable = 0x4b25318;
frame_resume = 0x2b50de4;
sdk_full = 0x3c62800;
