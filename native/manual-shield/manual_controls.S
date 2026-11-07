.text
.global hero_setter_hook
hero_setter_hook:
 /* Preserve the original high-bit early return exactly. */
 tbnz w1,#31,2f
 adrp x9,player_as_interface
 add x9,x9,:lo12:player_as_interface
 ldr x9,[x9]
 cmp x0,x9
 b.ne 1f
 cmp w1,#14
 b.ne 1f
 adrp x9,hero_control_state
 add x9,x9,:lo12:hero_control_state
 ldrb w9,[x9,#4]
 cbz w9,3f
 mov w2,#1
 b 1f
3:
 mov w2,#0
1:
 b original_setter_body
2:
 b original_setter_early

.global hero_target_guard_flags
hero_target_guard_flags:
 stp x16,x17,[sp,#-16]!
 adrp x16,hero_cache
 ldr x16,[x16,:lo12:hero_cache]
 cmp x20,x16
 b.ne 1f
 adrp x16,hero_control_state
 add x16,x16,:lo12:hero_control_state
 ldrb w17,[x16,#4]
 cbnz w17,1f
 bic w9,w9,#0x80000
 bic w8,w8,#0x80000
1:
 ldp x16,x17,[sp],#16
 orr w8,w8,w9
 b original_guard_flags_resume

.global hero_target_guard_update
hero_target_guard_update:
 stp x16,x17,[sp,#-16]!
 adrp x16,hero_cache
 ldr x16,[x16,:lo12:hero_cache]
 cmp x21,x16
 b.ne 1f
 adrp x16,hero_control_state
 add x16,x16,:lo12:hero_control_state
 ldrb w17,[x16,#4]
 cbnz w17,1f
 bic w9,w9,#0x80000
 b 2f
1:
 orr w9,w9,#0x80000
2:
 ldp x16,x17,[sp],#16
 b original_guard_update_resume

.global manual_frame_entry,manual_hid_entry
manual_frame_entry:
 ldr x16,[x0]
 adrp x17,main_scheduler_vtable
 add x17,x17,:lo12:main_scheduler_vtable
 cmp x16,x17
 b.ne 1f
 sub sp,sp,#32
 stp x0,x1,[sp]
 str x30,[sp,#16]
 bl manual_frame
 ldr x30,[sp,#16]
 ldp x0,x1,[sp]
 add sp,sp,#32
1:
 pacibsp
 b original_frame_body
manual_hid_entry:
 stp x19,x30,[sp,#-32]!
 mov x19,x0
 ldr w9,[x2]
 str w9,[sp,#16]
 bl sdk_full
 cbz w0,1f
 ldr w16,[sp,#16]
 cbz w16,2f
 cmp w16,#32
 b.ne 1f
2:
 stp x0,x30,[sp,#-16]!
 mov w1,w0
 mov x0,x19
 bl hero_controls_raw
 ldp x0,x30,[sp],#16
1:
 ldp x19,x30,[sp],#32
 ret
