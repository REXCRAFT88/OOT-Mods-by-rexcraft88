"""Assemble the shipped item-binding hook and test same-address cache rebuilds."""
from pathlib import Path
import re, subprocess, tempfile, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'hero-review-deps'))
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import *

SOURCE = ROOT / 'native/hero-with-stamina/wheel_probe.S'
BASE, CACHE, RESUME, STOP = 0x10000, 0x50000, 0x20000, 0x30000

with tempfile.TemporaryDirectory(prefix='wheel-rebind-') as temp:
    temp = Path(temp)
    source = SOURCE.read_text()
    body = source.split('wheel_bind_item:\n', 1)[1].split('wheel_list_ctor:\n', 1)[0]
    asm = temp / 'wheel_bind_item.S'
    asm.write_text('.section .text.wheel_bind_item,"ax"\n.global wheel_bind_item\nwheel_bind_item:\n' + body)
    linker = temp / 'wheel.ld'
    linker.write_text(f'SECTIONS {{ . = {BASE:#x}; .text : {{ *(.text*) }} }}\n'
                      f'wheel_cache = {CACHE:#x};\nbind_item_resume = {RESUME:#x};\n')
    obj, elf, binary = temp / 'wheel.o', temp / 'wheel.elf', temp / 'wheel.bin'
    subprocess.run(['clang', '--target=aarch64-none-elf', '-c', str(asm), '-o', str(obj)], check=True)
    subprocess.run(['ld.lld.exe', '--gc-sections', '--undefined=wheel_bind_item', '-T', str(linker), str(obj), '-o', str(elf)], check=True)
    subprocess.run(['llvm-objcopy.exe', '-O', 'binary', '--only-section=.text', str(elf), str(binary)], check=True)
    symbols = {line.split()[2]: int(line.split()[0], 16) for line in subprocess.check_output(['llvm-nm.exe', str(elf)], text=True).splitlines() if len(line.split()) == 3}

    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    for address, size in [(BASE, 0x10000), (CACHE, 0x1000), (0x70000, 0x1000), (0x80000, 0x1000), (RESUME, 0x1000)]:
        u.mem_map(address, size)
    u.mem_write(BASE, binary.read_bytes())

    def bind(index, widget, other):
        u.mem_write(0x80000, index.to_bytes(4, 'little'))
        u.reg_write(UC_ARM64_REG_SP, 0x70ff0)
        u.reg_write(UC_ARM64_REG_X0, 0xaaaa)
        u.reg_write(UC_ARM64_REG_X19, other)
        u.reg_write(UC_ARM64_REG_X20, 0x80000)
        u.reg_write(UC_ARM64_REG_X21, widget)
        for reg, value in [(UC_ARM64_REG_X9, 0x909), (UC_ARM64_REG_X10, 0xa0a),
                           (UC_ARM64_REG_X11, 0xb0b), (UC_ARM64_REG_X16, 0x1616),
                           (UC_ARM64_REG_X17, 0x1717)]:
            u.reg_write(reg, value)
        u.reg_write(UC_ARM64_REG_X30, STOP)
        try:
            u.emu_start(symbols.get('wheel_bind_item', BASE), RESUME, count=300)
        except Exception:
            print('bind exception at', hex(u.reg_read(UC_ARM64_REG_PC)), bytes(u.mem_read(BASE, 128)).hex())
            raise
        assert u.reg_read(UC_ARM64_REG_SP) == 0x70ff0
        assert u.reg_read(UC_ARM64_REG_X0) == widget
        for reg, value in [(UC_ARM64_REG_X9, 0x909), (UC_ARM64_REG_X10, 0xa0a),
                           (UC_ARM64_REG_X11, 0xb0b), (UC_ARM64_REG_X16, 0x1616),
                           (UC_ARM64_REG_X17, 0x1717)]:
            assert u.reg_read(reg) == value, hex(reg)

    u.mem_write(CACHE + 48, (0x8888).to_bytes(8, 'little'))
    u.mem_write(CACHE + 36, (64).to_bytes(4, 'little'))
    for i in range(64):
        u.mem_write(CACHE + 256 + i * 16, (0x9000 + i * 16).to_bytes(8, 'little') + (0xaaaa).to_bytes(8, 'little'))
    bind(0, 0x1111, 0x2222)
    assert int.from_bytes(u.mem_read(CACHE + 48, 8), 'little') == 0
    assert int.from_bytes(u.mem_read(CACHE + 36, 4), 'little') == 1
    for i in range(1, 64):
        assert u.mem_read(CACHE + 256 + i * 16, 16) == b'\0' * 16, i
    assert u.mem_read(CACHE + 256, 16) == (0x1111).to_bytes(8, 'little') + (0x2222).to_bytes(8, 'little')
    bind(3, 0x3333, 0x4444)
    assert int.from_bytes(u.mem_read(CACHE + 36, 4), 'little') == 4
    assert u.mem_read(CACHE + 256 + 3 * 16, 16) == (0x3333).to_bytes(8, 'little') + (0x4444).to_bytes(8, 'little')
    print('PASS compiled item binding: same-pointer rebind clears stale widgets/controller, tracks completion, preserves registers and stack.')
