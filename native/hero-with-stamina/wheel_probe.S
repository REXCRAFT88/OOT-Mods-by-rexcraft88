.text
.global wheel_bind_entry,wheel_bind_item,wheel_list_ctor
wheel_bind_entry:
 stp x16,x17,[sp,#-16]!
 adrp x16,wheel_cache
 add x16,x16,:lo12:wheel_cache
 str x0,[x16,#16] // Specific item binding owns the wheel-list cache.
 ldr w17,[x16,#32]
 add w17,w17,#1
 str w17,[x16,#32]
 ldp x16,x17,[sp],#16
 pacibsp
 b bind_entry_resume
wheel_bind_item:
 stp x16,x17,[sp,#-16]!
 ldr w17,[x20]
 cmp w17,#64
 b.hs 1f
 adrp x16,wheel_cache
 add x16,x16,:lo12:wheel_cache
 str w17,[x16,#36]
 add x16,x16,#256
 add x16,x16,x17,lsl #4
 stp x21,x19,[x16]
1:
 ldp x16,x17,[sp],#16
 mov x0,x21
 b bind_item_resume
wheel_list_ctor:
 // Generic UI lists must not overwrite the item wheel list.
 pacibsp
 b list_ctor_resume

.global wheel_draw_entry
wheel_draw_entry:
 stp x29,x30,[sp,#-16]!
 mov x0,x19
 bl wheel_draw
 ldp x29,x30,[sp],#16
 ldp d9,d8,[sp,#0x100]
 b draw_resume

.global wheel_tick_entry
wheel_tick_entry:
 stp x29,x30,[sp,#-16]!
 bl original_hero_frame
 bl wheel_tick
 ldp x29,x30,[sp],#16
 ret

.global wheel_hid_entry
wheel_hid_entry:
 cbz w0,1f
 ldr x16,[sp,#8]
 adrp x17,full_hid_return
 add x17,x17,:lo12:full_hid_return
 cmp x16,x17
 b.ne 1f
 ldr w16,[sp,#16]
 cbz w16,2f
 cmp w16,#32
 b.ne 1f
2:
 stp x0,x30,[sp,#-16]!
 mov w1,w0
 mov x0,x19
 bl hero_all_input
 ldp x0,x30,[sp],#16
1:
 ldp x19,x30,[sp],#32
 ret
