.text
.global ocarina_enter,ocarina_leave
ocarina_enter:
 stp x16,x17,[sp,#-16]!
 adrp x16,wheel_cache
 add x16,x16,:lo12:wheel_cache
 mov w17,#1
 str w17,[x16,#120]
 str wzr,[x16,#68]
 str wzr,[x16,#112]
 ldp x16,x17,[sp],#16
 pacibsp
 b ocarina_enter_resume
ocarina_leave:
 stp x16,x17,[sp,#-16]!
 adrp x16,wheel_cache
 add x16,x16,:lo12:wheel_cache
 str wzr,[x16,#120]
 str wzr,[x16,#68]
 str wzr,[x16,#112]
 ldp x16,x17,[sp],#16
 pacibsp
 b ocarina_leave_resume
