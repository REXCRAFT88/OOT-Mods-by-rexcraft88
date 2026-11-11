"""Run the compiled native menu append callback and trampoline under Unicorn."""
from pathlib import Path
import struct
import subprocess
import sys

sys.path.insert(0, 'work/hero-review-deps')
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_SP, UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X20, UC_ARM64_REG_X21, UC_ARM64_REG_X30

project = Path(__file__).resolve().parents[2]
root = Path('work/wheel-options-menu-check')
root.mkdir(parents=True, exist_ok=True)
helper = root / 'helper.c'
helper.write_text('''
typedef unsigned u32;
extern volatile u32 enum_storage;
u32 read_enum(void *game_data, u32 *value, void *descriptor, u32 field) {
    if (field != 0x916ac217u) return 0;
    *value = enum_storage;
    return 1;
}
''')
flags = ['--target=aarch64-none-elf', '-Oz', '-ffreestanding', '-fno-stack-protector', '-fno-jump-tables']
for source, output in [
    (project / 'native/wheel/wheel_options.c', root / 'options.o'),
    (project / 'native/wheel/wheel_option_menu.S', root / 'menu.o'),
    (helper, root / 'helper.o'),
]:
    subprocess.run(['clang', *flags, '-c', str(source), '-o', str(output)], check=True)
(root / 'menu.ld').write_text(
    'SECTIONS { . = 0x1000; .text : { *(.text*) *(.rodata*) } '
    '/DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\n'
    'game_data_singleton = 0x201000; enum_storage = 0x200000; '
    'option_menu_resume = 0x4000; test_append = 0x500000;\n'
)
subprocess.run(['ld.lld.exe', '-T', str(root / 'menu.ld'), str(root / 'options.o'), str(root / 'menu.o'), str(root / 'helper.o'), '-o', str(root / 'menu.elf')], check=True)
subprocess.run(['llvm-objcopy', '-O', 'binary', '--only-section=.text', str(root / 'menu.elf'), str(root / 'text.bin')], check=True)
symbols = {parts[2]: int(parts[0], 16) for line in subprocess.check_output(['llvm-nm', str(root / 'menu.elf')], text=True).splitlines() if len(parts := line.split()) == 3}

base = 0x80000000
stop = base + 0x600000
sp = base + 0x300000
game = base + 0x201000
descriptor = base + 0x202000
list_obj = base + 0x203000
vtable = base + 0x204000
list_ptr = sp + 0x80
emu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
emu.mem_map(base, 0x700000)
emu.mem_write(base + 0x1000, (root / 'text.bin').read_bytes())
emu.mem_write(list_obj, struct.pack('<Q', vtable))
emu.mem_write(vtable + 0x58, struct.pack('<Q', base + symbols['test_append']))
emu.mem_write(sp + 0x70, struct.pack('<Q', descriptor))
emu.mem_write(sp + 0x80, struct.pack('<Q', list_obj))
emu.mem_write(base + symbols['option_menu_resume'], bytes.fromhex('c0035fd6'))

captured = []
def hook(uc, address, size, data):
    if address == base + symbols['test_append']:
        label = uc.reg_read(UC_ARM64_REG_X1)
        captured.append((uc.reg_read(UC_ARM64_REG_X0), label,
                         uc.reg_read(UC_ARM64_REG_X2), bytes(uc.mem_read(label + 12, 26))))
        uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
    elif address == stop:
        return

emu.hook_add(UC_HOOK_CODE, hook)
for choice, expected_index in [(1627154745, 0), (556646631, 1), (957022509, 2)]:
    emu.mem_write(base + 0x200000, struct.pack('<I', choice))
    emu.reg_write(UC_ARM64_REG_SP, sp)
    emu.reg_write(UC_ARM64_REG_X20, game)
    emu.reg_write(UC_ARM64_REG_X21, base + 0x205000)
    emu.reg_write(UC_ARM64_REG_X30, stop)
    emu.emu_start(base + symbols['wheel_option_menu_entry'], stop, count=10000)
    assert emu.reg_read(UC_ARM64_REG_PC) == stop
    _, label, index, title = captured[-1]
    assert index == expected_index
    assert title == b'MessageWindowTransparency\0'
    assert struct.unpack('<Q', emu.mem_read(label, 8))[0] == label + 12
print('PASS: compiled menu hook syncs Right/Left/Both via MessageWindowTransparency')
