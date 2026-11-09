"""Execute the compiled wheel tap path and check that UI focus is updated."""
from pathlib import Path
import subprocess, tempfile, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'hero-review-deps'))
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

SOURCE = ROOT / 'native/wheel/wheel_runtime.c'
FLAGS = ['--target=aarch64-none-elf', '-Oz', '-ffreestanding', '-ffunction-sections',
         '-fdata-sections', '-fno-stack-protector', '-fno-jump-tables']
BASE, CACHE, LIST, CONTROLLER, STOP = 0x10000, 0x50000, 0x60000, 0x61000, 0x30000
API = {'set_index': 0x20000, 'change_focus': 0x20010,
       'equip_index': 0x20020, 'commit_item': 0x20030}

with tempfile.TemporaryDirectory(prefix='wheel-cycle-') as temp:
    temp = Path(temp)
    obj, elf, binary, linker = (temp / name for name in ['wheel.o', 'wheel.elf', 'wheel.bin', 'wheel.ld'])
    linker.write_text('SECTIONS { . = 0x10000; .text : { *(.text*) } }\n'
                      f'wheel_cache = {CACHE:#x};\n' + ''.join(f'{name} = {address:#x};\n' for name, address in API.items()))
    subprocess.run(['clang', *FLAGS, '-c', str(SOURCE), '-o', str(obj)], check=True)
    subprocess.run(['ld.lld.exe', '--gc-sections', '--undefined=wheel_tick', '-T', str(linker), str(obj), '-o', str(elf)], check=True)
    subprocess.run(['llvm-objcopy.exe', '-O', 'binary', '--only-section=.text', str(elf), str(binary)], check=True)
    syms = {line.split()[2]: int(line.split()[0], 16) for line in subprocess.check_output(['llvm-nm.exe', str(elf)], text=True).splitlines() if len(line.split()) == 3}

    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    for address, size in [(BASE, 0x10000), (CACHE, 0x1000), (LIST, 0x1000), (CONTROLLER, 0x1000), (0x20000, 0x1000), (STOP, 0x1000)]:
        u.mem_map(address, size)
    u.mem_write(BASE, binary.read_bytes())
    u.mem_write(CACHE + 16, LIST.to_bytes(8, 'little'))
    u.mem_write(CACHE + 48, CONTROLLER.to_bytes(8, 'little'))
    u.mem_write(CACHE + 36, (2).to_bytes(4, 'little'))
    u.mem_write(CONTROLLER + 0x78, (2).to_bytes(4, 'little'))
    u.mem_write(LIST + 0x4c, (0).to_bytes(4, 'little'))
    for i, address in enumerate([0x62000, 0x63000]):
        u.mem_map(address, 0x1000)
        u.mem_write(CACHE + 264 + i * 16, address.to_bytes(8, 'little'))
        u.mem_write(address + 0x94, b'Weapon_Bottle_' + (b'Red' if i == 0 else b'Blue') + b'\0')
    calls = []

    def hook(uc, address, size, data):
        for name, target in API.items():
            if address != target:
                continue
            x0, x1, x2 = (uc.reg_read(reg) for reg in [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2])
            calls.append((name, x0, x1, x2))
            if name == 'set_index':
                uc.mem_write(x0 + 0x4c, x1.to_bytes(4, 'little'))
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            break

    u.hook_add(UC_HOOK_CODE, hook)

    def tick():
        u.reg_write(UC_ARM64_REG_SP, STOP + 0x800)
        u.reg_write(UC_ARM64_REG_X30, STOP)
        try:
            u.emu_start(syms['wheel_tick'], STOP, count=1000)
        except Exception:
            print('wheel_tick exception at', hex(u.reg_read(UC_ARM64_REG_PC)), hex(syms['wheel_tick']))
            print(bytes(u.mem_read(u.reg_read(UC_ARM64_REG_PC)-16, 48)).hex())
            print('calls', calls, 'lr', hex(u.reg_read(UC_ARM64_REG_X30)), 'sp', hex(u.reg_read(UC_ARM64_REG_SP)))
            raise

    # Partial rebind must not inspect stale widget names or change selection.
    u.mem_write(CACHE + 36, (1).to_bytes(4, 'little'))
    u.mem_write(CACHE + 112, (1).to_bytes(4, 'little'))
    tick()
    assert not calls and int.from_bytes(u.mem_read(LIST + 0x4c, 4), 'little') == 0
    u.mem_write(CACHE + 36, (2).to_bytes(4, 'little'))
    for expected_from, expected_to in [(0, 1), (1, 0)]:
        u.mem_write(CACHE + 112, (1).to_bytes(4, 'little'))
        calls.clear(); tick()
        summary = [(name, x0, x1) if name != 'change_focus' else (name, x0, x1, x2)
                   for name, x0, x1, x2 in calls]
        assert summary == [('set_index', LIST, expected_to),
                           ('change_focus', CONTROLLER, expected_from, expected_to),
                           ('equip_index', CONTROLLER, expected_to),
                           ('commit_item', CONTROLLER, 0)], calls
        assert int.from_bytes(u.mem_read(LIST + 0x4c, 4), 'little') == expected_to
    print('PASS compiled variant cycle: both directions equip and update native focus/preview.')
