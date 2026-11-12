.text
.global hero_guard_impact_entry
hero_guard_impact_entry:
 sub sp,sp,#80
 stp x0,x1,[sp]
 stp x2,x3,[sp,#16]
 str x30,[sp,#32]
 stp q0,q1,[sp,#48]
 bl hero_guard_impact
 ldp q0,q1,[sp,#48]
 ldr x30,[sp,#32]
 ldp x2,x3,[sp,#16]
 ldp x0,x1,[sp]
 add sp,sp,#80
 pacibsp
 b original_guard_impact_body

.global hero_setter_hook
hero_setter_hook:
 /* Preserve the original high-bit early return exactly. */
 tbnz w1,#31,2f
#ifdef HERO_UNIFIED
 adrp x9,hero_settings_bits
 ldr w9,[x9,:lo12:hero_settings_bits]
 tbnz w9,#1,1f
#endif
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
#ifdef HERO_UNIFIED
 adrp x16,hero_settings_bits
 ldr w17,[x16,:lo12:hero_settings_bits]
 tbnz w17,#1,.Lguard_flags_native
#endif
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
#ifdef HERO_UNIFIED
 b .Lguard_flags_restore
.Lguard_flags_native:
#endif
 b .Lguard_flags_restore
.Lguard_flags_restore:
1:
 ldp x16,x17,[sp],#16
 orr w8,w8,w9
 b original_guard_flags_resume

.global hero_target_guard_update
hero_target_guard_update:
 stp x16,x17,[sp,#-16]!
#ifdef HERO_UNIFIED
 adrp x16,hero_settings_bits
 ldr w17,[x16,:lo12:hero_settings_bits]
 tbnz w17,#1,.Lguard_update_native
#endif
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
#ifdef HERO_UNIFIED
 b .Lguard_update_restore
.Lguard_update_native:
 orr w9,w9,#0x80000
#endif
 b .Lguard_update_restore
.Lguard_update_restore:
2:
 ldp x16,x17,[sp],#16
 b original_guard_update_resume

#ifdef HERO_UNIFIED
/* Patch 0x574e1c's native swap-option BEQ conditionally. With manual shield
   enabled it retains the published NOP behavior; when disabled it executes
   the original compare/branch semantics using the live w8/w9 values. */
.global hero_controller_toggle_gate
hero_controller_toggle_gate:
 str x16,[sp,#-16]!
 adrp x16,hero_settings_bits
 ldr w16,[x16,:lo12:hero_settings_bits]
 tbnz w16,#1,.Ltoggle_native
 ldr x16,[sp],#16
 b original_controller_toggle_resume
.Ltoggle_native:
 ldr x16,[sp],#16
 b.ne .Ltoggle_resume
 b original_controller_toggle_target
.Ltoggle_resume:
 b original_controller_toggle_resume

/* Patch 0x279d640's original prologue conditionally. The published manual
   behavior returns false; native mode runs the untouched function body. */
.global hero_controller_query_gate
hero_controller_query_gate:
 pacibsp
 adrp x9,hero_settings_bits
 ldr w9,[x9,:lo12:hero_settings_bits]
 tbnz w9,#1,.Lquery_native
 mov w0,wzr
 .inst 0xd65f0fff /* RETAB; keep assembly independent of -march pauth. */
.Lquery_native:
 b original_controller_query_body
#endif
