.text
.align 2
.global hero_menu_byml_option_type_reader
.type hero_menu_byml_option_type_reader, %function
/*
 * Native ABI at main+0x339ab40:
 *   x0 = wrapper, with output pointer at +8
 *   x1 = BYML value, type byte at +0xc and raw u32 hash at +8
 * For a custom D3 enum hash, write its new ID and report success. All other
 * hashes return through the original PACIBSP prologue at main+0x339ab44 with
 * x0/x1 restored, preserving the stock parser's behavior and ABI.
 */
hero_menu_byml_option_type_reader:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x0, x1, [sp, #16]
    ldrb w9, [x1, #0xc]
    cmp w9, #0xd3
    b.ne .Lstock_option_type
    ldr w0, [x1, #8]
    bl hero_menu_hash_to_enum_id
    cmp w0, #18
    b.lo .Lstock_option_type
    cmp w0, #24
    b.hi .Lstock_option_type
    mov w2, w0
    ldr x3, [sp, #16]
    ldr x3, [x3, #8]
    str w2, [x3]
    ldr x1, [sp, #24]
    ldp x29, x30, [sp], #32
    mov w0, #1
    ret
.Lstock_option_type:
    ldp x0, x1, [sp, #16]
    ldp x29, x30, [sp], #32
    pacibsp
    b hero_menu_stock_byml_resume
.size hero_menu_byml_option_type_reader, .-hero_menu_byml_option_type_reader
