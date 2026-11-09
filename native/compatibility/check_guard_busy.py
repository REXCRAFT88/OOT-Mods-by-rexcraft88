"""Compile and execute each variant's AArch64 manual-shield busy predicate."""
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
BASE, BOOL_FN, INT_FN, STOP, INTERFACE, PLAYER, WHEEL_CACHE, CONTROL = 0x10000, 0x20000, 0x20010, 0x30000, 0x40000, 0x41000, 0x44000, 0x45000
ACTOR, TABLE, LIFTER = 0x46000, 0x47000, 0x48000
BUSY_FLAGS = [62, 86]

with tempfile.TemporaryDirectory(prefix='guard-busy-') as temp:
    temp = Path(temp)
    linker = temp / 'test.ld'
    linker.write_text(f'SECTIONS {{ . = {BASE:#x}; .text : {{ *(.text*) }} }}\nas_bool = {BOOL_FN:#x};\nas_int = {INT_FN:#x};\nwheel_cache = {WHEEL_CACHE:#x};\nhero_control_state = {CONTROL:#x};\n')
    for variant, source in SOURCES.items():
        obj, elf, binary = temp / f'{variant}.o', temp / f'{variant}.elf', temp / f'{variant}.bin'
        subprocess.run(['clang', *FLAGS, '-c', str(source), '-o', str(obj)], check=True)
        subprocess.run(['ld.lld.exe', '--gc-sections', '--undefined=hero_guard_should_apply', '--undefined=hero_player_carrying', '--undefined=hero_input_guard_active', '-T', str(linker), str(obj), '-o', str(elf)], check=True)
        subprocess.run(['llvm-objcopy.exe', '-O', 'binary', '--only-section=.text', str(elf), str(binary)], check=True)
        names = {int(line.split()[0], 16): line.split()[2] for line in subprocess.check_output(['llvm-nm.exe', str(elf)], text=True).splitlines() if len(line.split()) == 3}
        entry = next(address for address, name in names.items() if name == 'hero_guard_should_apply')
        carry_entry = next(address for address, name in names.items() if name == 'hero_player_carrying')
        input_entry = next(address for address, name in names.items() if name == 'hero_input_guard_active')
        u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        u.mem_map(BASE, 0x10000); u.mem_map(BOOL_FN, 0x1000)
        u.mem_map(INTERFACE, 0x4000); u.mem_map(STOP, 0x1000); u.mem_map(WHEEL_CACHE, 0x1000)
        u.mem_map(CONTROL, 0x1000); u.mem_map(ACTOR, 0x3000)
        u.mem_write(BASE, binary.read_bytes())
        bools, action_names, weapon = set(), [None, None], 1
        for addr, value in [(PLAYER+0x238, 0x42000), (PLAYER+0x310, 0x43000)]:
            u.mem_write(addr, bytes(8))

        def hook(uc, address, size, data):
            if address == BOOL_FN:
                uc.reg_write(UC_ARM64_REG_X0, int(uc.reg_read(UC_ARM64_REG_X1) in bools))
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            elif address == INT_FN:
                uc.reg_write(UC_ARM64_REG_X0, weapon)
                uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))

        u.hook_add(UC_HOOK_CODE, hook)

        def run(held=1, initialized=1, alive=1, combat=1, cap=100.0, stamina=50.0, interface=INTERFACE, ocarina_latch=0, carrying=0):
            u.mem_write(WHEEL_CACHE+120, int(ocarina_latch).to_bytes(4, 'little'))
            u.mem_write(CONTROL+5, bytes([carrying]))
            u.mem_write(PLAYER+0x238, bytes(8)); u.mem_write(PLAYER+0x310, bytes(8))
            for i, name in enumerate(action_names):
                if name:
                    address = 0x42000 if i == 0 else 0x43000
                    slot = PLAYER + 0x238 if i == 0 else PLAYER + 0x310
                    u.mem_write(slot, address.to_bytes(8, 'little'))
                    u.mem_write(address, name.encode() + b'\0')
            u.reg_write(UC_ARM64_REG_SP, STOP + 0x800)
            u.reg_write(UC_ARM64_REG_X0, interface)
            u.reg_write(UC_ARM64_REG_X1, PLAYER)
            for reg, value in [(UC_ARM64_REG_X2, held), (UC_ARM64_REG_X3, initialized),
                               (UC_ARM64_REG_X4, alive), (UC_ARM64_REG_X5, combat)]:
                u.reg_write(reg, value)
            u.reg_write(UC_ARM64_REG_S0, int.from_bytes(struct.pack('<f', cap), 'little'))
            u.reg_write(UC_ARM64_REG_S1, int.from_bytes(struct.pack('<f', stamina), 'little'))
            u.reg_write(UC_ARM64_REG_X30, STOP)
            u.emu_start(entry, STOP, count=1000)
            return u.reg_read(UC_ARM64_REG_X0)

        bools.clear(); weapon = 1
        assert run() == 1, (variant, 'ordinary guard, including target latch on')
        assert run(carrying=1) == 0, (variant, 'native lifter state blocks manual guard')
        assert run() == 1, (variant, 'manual guard resumes after carrying ends')
        bools.update([61, 90])
        assert run() == 1, (variant, 'default-true ocarina booleans do not cancel guard')
        bools.clear()
        bools.update([9,63])
        assert run() == 1, (variant, 'generic aiming and left-grab flags do not cancel guard')
        bools.clear()
        assert run(held=0) == 0, (variant, 'released guard')
        assert run(interface=0) == 0, (variant, 'null/stale interface')
        assert run(combat=0, stamina=0.0) == 1, (variant, 'outside combat')
        assert run(stamina=0.0) == 0, (variant, 'empty combat stamina')
        for index in BUSY_FLAGS:
            bools.clear(); bools.add(index)
            assert run() == 0, (variant, 'busy flag', index)
            bools.clear()
            assert run() == 1, (variant, 'held guard resumes when busy state exits', index)
        assert run(ocarina_latch=1) == 0, (variant, 'explicit active ocarina latch suppresses guard')
        assert run() == 1, (variant, 'guard resumes when explicit ocarina latch clears')
        for name, slot in [('HoldItemUpper', 0), ('LiftWait', 1), ('GrabMovableObj', 0),
                           ('BowChargeUpper', 1), ('BowShootUpper', 0),
                           ('BowReLoadUpper', 1), ('HookshotAimEd', 0),
                           ('BoomerangThrow', 1), ('AimHorseLowerB', 0)]:
            action_names[slot] = name
            assert run() == 0, (variant, 'busy AS request', name)
            action_names[slot] = None
            assert run() == 1, (variant, 'held guard resumes after AS request', name)
        bools.clear(); weapon = 2
        assert run() == 0, (variant, 'two-handed weapon')
        def carrying_state(state, has_table=True, has_lifter=True):
            u.mem_write(ACTOR+0x270, (TABLE if has_table else 0).to_bytes(8,'little'))
            u.mem_write(TABLE+0x2c8, (LIFTER if has_lifter else 0).to_bytes(8,'little'))
            u.mem_write(LIFTER+0x2b0, int(state).to_bytes(4,'little'))
            u.reg_write(UC_ARM64_REG_X0, ACTOR);u.reg_write(UC_ARM64_REG_X30,STOP)
            u.emu_start(carry_entry,STOP,count=200)
            return u.reg_read(UC_ARM64_REG_X0)
        for state in (3, 1, 2):
            assert carrying_state(state) == 1, (variant, 'setup, lift and carry states block guard', state)
        assert carrying_state(0) == 0, (variant, 'clear lifter state permits guard')
        assert carrying_state(3, has_lifter=False) == 0, (variant, 'missing lifter does not falsely block guard')
        for carried, expected in [(0, 1), (1, 0)]:
            u.mem_write(CONTROL+5, bytes([carried]))
            u.reg_write(UC_ARM64_REG_X0, 0x100);u.reg_write(UC_ARM64_REG_X30,STOP)
            u.emu_start(input_entry,STOP,count=100)
            assert u.reg_read(UC_ARM64_REG_X0) == expected, (variant, 'held L2 is removed while carrying', carried)
        print('PASS', variant, 'compiled guard policy, lifter states, and held-trigger suppression while carrying')
