.text
.global hud_entry
hud_entry:
 b hud_hook
.global hero_hud_pane
hero_hud_pane:
 b hud_pane
hud_hook:
 sub sp,sp,#0x100
 stp x0,x1,[sp]
 stp x2,x3,[sp,#16]
 stp x4,x5,[sp,#32]
 stp x6,x7,[sp,#48]
 str x30,[sp,#64]
 stp q0,q1,[sp,#80]
 stp q2,q3,[sp,#112]
 stp q4,q5,[sp,#144]
 stp q6,q7,[sp,#176]
 bl hud_prepare
 mov x16,x0
 ldp x0,x1,[sp]
 mov x1,x16
 ldp x2,x3,[sp,#16]
 ldp x4,x5,[sp,#32]
 ldp x6,x7,[sp,#48]
 ldr x30,[sp,#64]
 ldp q0,q1,[sp,#80]
 ldp q2,q3,[sp,#112]
 ldp q4,q5,[sp,#144]
 ldp q6,q7,[sp,#176]
 add sp,sp,#0x100
 pacibsp
 b layout_resume
