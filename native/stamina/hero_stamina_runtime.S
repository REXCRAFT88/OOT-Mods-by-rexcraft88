.text
.macro SAVE
 sub sp,sp,#32
 stp x0,x1,[sp]
 str x30,[sp,#16]
.endm
.macro RESTORE
 ldr x30,[sp,#16]
 ldp x0,x1,[sp]
 add sp,sp,#32
.endm
.global stamina_frame
stamina_frame:
 ldr x16,[x0]
 adrp x17,main_scheduler_vtable
 add x17,x17,:lo12:main_scheduler_vtable
 cmp x16,x17
 b.ne frame_original
 SAVE
 bl hero_native_frame
 RESTORE
frame_original:
 pacibsp
 b frame_resume
.macro ACTION name,kind,entering,resume
.global \name
\name:
 stp x30,x16,[sp,#-16]!
 mov w16,#\kind
 mov w17,#\entering
 bl action_common
 ldp x30,x16,[sp],#16
 pacibsp
 b \resume
.endm
action_common:
 SAVE
 mov w0,w16
 mov w1,w17
 bl hero_native_action
 RESTORE
 ret
.global attack_enter
attack_enter:
 SAVE
 mov w0,#0
 mov w1,#1
 bl hero_native_action
 RESTORE
 ldr x8,[x21,#0x270]
 b attack_enter_resume
ACTION attack_leave,0,0,attack_leave_resume
ACTION roll_enter,1,1,roll_enter_resume
ACTION roll_leave,1,0,roll_leave_resume
ACTION back_enter,2,1,back_enter_resume
ACTION back_leave,2,0,back_leave_resume
ACTION side_enter,3,1,side_enter_resume
ACTION side_leave,3,0,side_leave_resume
ACTION jump_enter,4,1,jump_enter_resume
ACTION jump_leave,4,0,jump_leave_resume
ACTION spin_enter,5,1,spin_enter_resume
ACTION spin_leave,5,0,spin_leave_resume
ACTION jumpattack_enter,6,1,jumpattack_enter_resume
ACTION jumpattack_leave,6,0,jumpattack_leave_resume
.global hero_mp_init
hero_mp_init:
 stp x16,x17,[sp,#-16]!
 adrp x16,hero_cache
 str x0,[x16,#8]
 ldp x16,x17,[sp],#16
 pacibsp
 b mp_init_resume

/* Filter only exertion buttons; movement, targeting, items and attacks stay intact. */
.macro HID name,target
.global \name
\name:
 stp x19,x30,[sp,#-32]!
 mov x19,x0
 ldr w9,[x2]
 str w9,[sp,#16]
 bl \target
 b exertion_filter
.endm
HID hid_full,sdk_full
HID hid_dual,sdk_dual
HID hid_left,sdk_left
HID hid_right,sdk_right
HID hid_handheld,sdk_handheld
exertion_filter:
 cbz w0,hid_done
 ldr w10,[sp,#16]
 cbz w10,2f
 cmp w10,#32
 b.ne hid_done
2:
 adrp x9,hero_runtime
 add x9,x9,:lo12:hero_runtime
 ldr w10,[x9,#36]
 cbz w10,hid_done
 /* Bypass paused/menu input after eight HID reads without a player update. */
 ldr w10,[x9,#136]
 adrp x11,hero_cache
 ldr w12,[x11,#32]
 cmp w10,w12
 b.ne 3f
 ldr w12,[x11,#36]
 add w12,w12,#1
 str w12,[x11,#36]
 cmp w12,#8
 b.hi hid_done
 b 4f
3:
 str w10,[x11,#32]
 str wzr,[x11,#36]
4:
 ldr s0,[x9]
 ldr s1,[x9,#52]
 ldr s2,[x9,#16]
 fmul s1,s1,s2
 fcmp s0,s1
 b.ge hid_done
 mov w12,w0
 mov x13,x19
 mov x11,#5
1:
 ldr x10,[x13,#8]
 bic x10,x10,x11
 str x10,[x13,#8]
 add x13,x13,#40
 subs w12,w12,#1
 b.ne 1b
hid_done:
 ldp x19,x30,[sp],#32
 ret

.global tired_damage
tired_damage:
 adrp x9,hero_runtime
 add x9,x9,:lo12:hero_runtime
 ldr w10,[x9,#36]
 cbz w10,damage_original
 ldr w10,[x9,#144]
 mov w11,#0x61
 tst w10,w11
 b.eq damage_original
 /* Qualify the runtime attacker too, including actors sharing player resources. */
 adrp x10,damage_call_return
 add x10,x10,:lo12:damage_call_return
 cmp x30,x10
 b.ne damage_original
 ldr x10,[x9,#120]
 ldr x10,[x10,#0x18]
 ldr x11,[x26,#0x18]
 cmp x10,x11
 b.ne damage_original
 ldrb w10,[x0,#0x112]
 tbz w10,#0,damage_original
 ldr s0,[x9,#172]
 fmov s1,#1.0
 fcmp s0,s1
 b.ge damage_original
 ldr s1,[x0,#0xec]
 fmul s0,s0,s1
 ubfx x10,x0,#3,#5
 add x10,x9,x10,lsl #2
 str s0,[x10,#264]
 add x0,x10,#264
 ret
damage_original:
 ldrb w8,[x0,#0x112]
 b damage_resume
