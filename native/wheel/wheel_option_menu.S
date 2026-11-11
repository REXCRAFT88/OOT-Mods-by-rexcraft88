.text
.global wheel_option_menu_entry
wheel_option_menu_entry:
    /* The native initializer keeps GameData and its option descriptor alive
       through this final row; preserve the original frame and continue the
       stock cleanup immediately after our append. */
    mov x0, x20
    add x1, sp, #0x70
    ldr x2, [sp, #0x80]
    str x30, [sp, #-16]!
    bl wheel_option_append
    ldr x30, [sp], #16
    ldr x8, [x21]
    b option_menu_resume
