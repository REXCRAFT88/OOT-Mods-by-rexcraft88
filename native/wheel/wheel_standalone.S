.text
.global wheel_bind_item,wheel_list_ctor
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
 ldr x16,[x0]
 adrp x17,main_scheduler_vtable
 add x17,x17,:lo12:main_scheduler_vtable
 cmp x16,x17
 b.ne 1f
 sub sp,sp,#32
 stp x0,x1,[sp]
 str x30,[sp,#16]
 bl wheel_tick
 ldr x30,[sp,#16]
 ldp x0,x1,[sp]
 add sp,sp,#32
1:
 pacibsp
 b frame_resume
.global wheel_hid_entry
wheel_hid_entry:
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
 bl wheel_raw
 ldp x0,x30,[sp],#16
1:
 ldp x19,x30,[sp],#32
 ret
