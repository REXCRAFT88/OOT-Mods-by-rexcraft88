"""Execute compiled hero_guard_frame for ordinary, busy, resumed, and stale AS states."""
from pathlib import Path
import struct, subprocess, tempfile, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'hero-review-deps'))
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

SOURCES = {
    'hero-with-stamina': ROOT / 'native/hero-with-stamina/hero_controls_runtime.c',
    'hero-without-stamina': ROOT / 'native/hero-without-stamina/manual_controls.c',
    'manual-shield': ROOT / 'native/manual-shield/manual_controls.c',
}
FLAGS = ['--target=aarch64-none-elf', '-Oz', '-ffreestanding', '-ffunction-sections',
         '-fdata-sections', '-fno-stack-protector', '-fno-jump-tables']
BASE, STOP = 0x10000, 0x30000
IMPORTS = {'get_guard_component': 0x20000, 'as_bool': 0x20010,
           'as_int': 0x20020, 'set_bool': 0x20030, 'native_draw_equipment': 0x20040}
GLOBALS = {'hero_cache': 0x50000, 'hero_runtime': 0x51000, 'hero_control_state': 0x52000,
           'wheel_cache': 0x53000}
STATE, ACTOR, TABLE, ANIM, P1, P2, IFACE, VTABLE, COMP, EQUIP = [0x60000+i*0x1000 for i in range(10)]
LIFTER = 0x6a000

with tempfile.TemporaryDirectory(prefix='guard-frame-') as temp:
    temp = Path(temp)
    script = temp / 'test.ld'
    script.write_text(f'SECTIONS {{ . = {BASE:#x}; .text : {{ *(.text*) }} }}\n' +
                      ''.join(f'{k} = {v:#x};\n' for k, v in {**IMPORTS, **GLOBALS}.items()))
    for variant, source in SOURCES.items():
        obj, elf, binary = temp / f'{variant}.o', temp / f'{variant}.elf', temp / f'{variant}.bin'
        subprocess.run(['clang', *FLAGS, '-c', str(source), '-o', str(obj)], check=True)
        subprocess.run(['ld.lld.exe', '--gc-sections', '--undefined=hero_guard_frame', '-T', str(script), str(obj), '-o', str(elf)], check=True)
        subprocess.run(['llvm-objcopy.exe', '-O', 'binary', '--only-section=.text', str(elf), str(binary)], check=True)
        symbols = {line.split()[2]: int(line.split()[0], 16) for line in subprocess.check_output(['llvm-nm.exe', str(elf)], text=True).splitlines() if len(line.split()) == 3}
        u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        u.mem_map(BASE, 0x10000); u.mem_map(0x20000, 0x1000); u.mem_map(0x50000, 0x4000)
        u.mem_map(0x60000, 0x10000); u.mem_map(STOP, 0x1000)
        u.mem_write(BASE, binary.read_bytes())
        def put(addr, value, fmt='Q'): u.mem_write(addr, struct.pack('<'+fmt, value))
        put(GLOBALS['hero_cache'], STATE)
        put(STATE+0x18, ACTOR)
        put(ACTOR+0x270, TABLE)
        put(TABLE+0x40, ANIM); put(TABLE+0x200, EQUIP)
        put(ANIM+0x18, P1); put(P1+0x18, P2); put(P2+0x40, IFACE)
        put(IFACE, VTABLE); put(VTABLE+0x88, IMPORTS['set_bool'])
        put(GLOBALS['hero_runtime'], 50.0, 'f'); put(GLOBALS['hero_runtime']+4, 100.0, 'f')
        put(GLOBALS['hero_runtime']+20, 1, 'I'); put(GLOBALS['hero_runtime']+32, 1, 'I')
        put(GLOBALS['hero_runtime']+36, 1, 'I'); put(GLOBALS['hero_runtime']+0x80, IFACE)
        put(GLOBALS['hero_control_state']+2, 1, 'B'); put(GLOBALS['hero_control_state']+1, 1, 'B')
        bools, weapon, draws, setters = set(), 1, [], []

        def hook(uc, address, size, data):
            if address == IMPORTS['get_guard_component']:
                uc.reg_write(UC_ARM64_REG_X0, COMP)
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            elif address == IMPORTS['as_bool']:
                uc.reg_write(UC_ARM64_REG_X0, int(uc.reg_read(UC_ARM64_REG_X1) in bools))
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            elif address == IMPORTS['as_int']:
                uc.reg_write(UC_ARM64_REG_X0, weapon)
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            elif address == IMPORTS['set_bool']:
                setters.append((uc.reg_read(UC_ARM64_REG_X1), uc.reg_read(UC_ARM64_REG_X2)))
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            elif address == IMPORTS['native_draw_equipment']:
                draws.append((uc.reg_read(UC_ARM64_REG_X0), uc.reg_read(UC_ARM64_REG_X1)))
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))

        u.hook_add(UC_HOOK_CODE, hook)

        def frame():
            u.reg_write(UC_ARM64_REG_SP, STOP+0x800); u.reg_write(UC_ARM64_REG_X30, STOP)
            u.emu_start(symbols['hero_guard_frame'], STOP, count=3000)

        frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\x01'
        assert int.from_bytes(u.mem_read(GLOBALS['hero_control_state']+0x70, 8), 'little') == ACTOR
        assert int.from_bytes(u.mem_read(GLOBALS['hero_control_state']+0x78, 8), 'little') == EQUIP
        assert int.from_bytes(u.mem_read(STATE+0xe50, 4), 'little') & 0x80000
        assert (EQUIP,4) in draws and setters[-1] == (14,1)
        # Native IsAiming / IsGrabLeft and default-true ocarina booleans must not cancel shield while the
        # target latch is on; the actual Bow/Hookshot AS requests are gated below.
        bools.update([9, 63, 61, 90]); draws.clear(); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\x01'
        assert setters[-1] == (14,1)
        bools.clear(); put(GLOBALS['wheel_cache']+120, 1, 'I'); draws.clear(); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\0'
        assert not draws and setters[-1] == (14,0)
        put(GLOBALS['wheel_cache']+120, 0, 'I'); draws.clear(); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\x01'
        assert draws == [(EQUIP,4)] and setters[-1] == (14,1)
        draws.clear(); setters.clear(); bools.clear(); bools.add(86); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\0'
        assert int.from_bytes(u.mem_read(COMP+0x24,4), 'little') & 0x20 == 0
        assert not draws and setters[-1] == (14,0)
        bools.clear(); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\x01'
        assert draws == [(EQUIP,4)] and setters[-1] == (14,1)
        put(TABLE+0x2c8, LIFTER); put(LIFTER+0x2b0, 3, 'I')
        draws.clear(); setters.clear(); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+5, 1) == b'\x01'
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\0'
        assert not draws and setters[-1] == (14,0)
        put(LIFTER+0x2b0, 0, 'I'); draws.clear(); frame()
        assert u.mem_read(GLOBALS['hero_control_state']+5, 1) == b'\0'
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\x01'
        assert draws == [(EQUIP,4)] and setters[-1] == (14,1)
        draws.clear(); setters.clear(); put(GLOBALS['hero_runtime']+0x80, VTABLE)
        frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\0'
        assert not draws and not setters
        assert int.from_bytes(u.mem_read(GLOBALS['hero_control_state']+0x70, 8), 'little') == 0
        assert int.from_bytes(u.mem_read(GLOBALS['hero_control_state']+0x78, 8), 'little') == 0
        draws.clear(); setters.clear(); put(GLOBALS['hero_runtime']+0x80, 0)
        frame()
        assert u.mem_read(GLOBALS['hero_control_state']+4, 1) == b'\0'
        assert not draws and not setters
        assert int.from_bytes(u.mem_read(GLOBALS['hero_control_state']+0x78, 8), 'little') == 0
        print('PASS', variant, 'compiled frame flags/draw, target+guard coexistence, busy suppression/resume, stale-interface stop')
