.text
.global hero_drop_lottery_entry
hero_drop_lottery_entry:
 stp x19,x30,[sp,#-32]!
 mov x19,x1
 bl hero_drop_lottery_original
 str x0,[sp,#16]
 mov x0,x19
 bl hero_filter_recovery_drops
 ldr x0,[sp,#16]
 ldp x19,x30,[sp],#32
 ret
hero_drop_lottery_original:
 pacibsp
 b native_drop_lottery_resume
