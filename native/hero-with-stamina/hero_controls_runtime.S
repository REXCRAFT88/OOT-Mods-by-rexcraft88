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

.global hero_as_request_hook,native_request_as_original,hero_target_guard_flags
hero_as_request_hook:
 sub sp,sp,#48
 stp x0,x1,[sp]
 stp x3,x4,[sp,#16]
 str x30,[sp,#32]
 bl hero_as_request
 mov x2,x0
 ldp x0,x1,[sp]
 ldp x3,x4,[sp,#16]
 ldr x30,[sp,#32]
 add sp,sp,#48
native_request_as_original:
 pacibsp
 b original_request_body

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
