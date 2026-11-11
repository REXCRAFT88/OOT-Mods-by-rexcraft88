"""Exercise the compiled standalone wheel bumper routing on AArch64."""
from pathlib import Path
import struct
import subprocess
import sys

sys.path.insert(0, 'work/hero-review-deps')
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_SP, UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X30

project = Path(__file__).resolve().parents[2]
root = Path('work/wheel-options-check')
root.mkdir(parents=True, exist_ok=True)
stub = root / 'mode.c'
stub.write_text('unsigned mode_storage; unsigned wheel_bumper_mode(void){return mode_storage;}\n')
flags = ['--target=aarch64-none-elf', '-Oz', '-ffreestanding', '-fno-stack-protector', '-fno-jump-tables', '-DWHEEL_OPTIONS_ONLY']
subprocess.run(['clang', *flags, '-c', str(project / 'native/compatibility/wheel_context.c'), '-o', str(root / 'context.o')], check=True)
subprocess.run(['clang', *flags, '-c', str(stub), '-o', str(root / 'mode.o')], check=True)
(root / 'test.ld').write_text(
    'SECTIONS { . = 0x1000; .text : { *(.text*) *(.rodata*) } '
    '/DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\n'
    'wheel_cache = 0x100000; mode_storage = 0x200000;\n'
)
subprocess.run(['ld.lld.exe', '-T', str(root / 'test.ld'), str(root / 'context.o'), str(root / 'mode.o'), '-o', str(root / 'test.elf')], check=True)
subprocess.run(['llvm-objcopy', '-O', 'binary', '--only-section=.text', str(root / 'test.elf'), str(root / 'text.bin')], check=True)
symbols = {parts[2]: int(parts[0], 16) for line in subprocess.check_output(['llvm-nm', str(root / 'test.elf')], text=True).splitlines() if len(parts := line.split()) == 3}

base = 0x80000000
cache = base + 0x100000
state = base + 0x300000
stop = base + 0x400000
mode_addr = base + 0x200000
emu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
emu.mem_map(base, 0x500000)
emu.mem_write(base + 0x1000, (root / 'text.bin').read_bytes())

def put32(address, value):
    emu.mem_write(address, struct.pack('<I', value))

def call(mode, sample, buttons, bypass=0, heartbeat=None):
    put32(mode_addr, mode)
    put32(cache + 120, bypass)
    put32(cache + 124, sample + 10 if heartbeat is None else heartbeat)
    emu.mem_write(state, struct.pack('<5Q', sample, buttons, 0, 0, 0))
    emu.reg_write(UC_ARM64_REG_X0, state)
    emu.reg_write(UC_ARM64_REG_X1, 1)
    emu.reg_write(UC_ARM64_REG_X30, stop)
    emu.reg_write(UC_ARM64_REG_SP, stop - 0x100)
    emu.emu_start(base + symbols['wheel_context_raw'], stop, count=5000)
    assert emu.reg_read(UC_ARM64_REG_PC) == stop
    return struct.unpack('<Q', emu.mem_read(state + 8, 8))[0]

def event():
    return struct.unpack('<I', emu.mem_read(cache + 112, 4))[0]

# Right (default): taps are consumed; sustained R remains visible to stock.
put32(cache + 128, 0)
assert call(0, 100, 0x80) == 0
assert call(0, 110, 0) == 0 and event() == 1
assert call(0, 200, 0x80) == 0
assert call(0, 401, 0x80) == 0x80

# Left: a short L tap selects once, physical R is blocked, and a sustained L
# is converted to exactly one native R input after the tap window.
put32(cache + 68, 0); put32(cache + 112, 0); put32(cache + 128, 0)
assert call(1, 500, 0x40) == 0
assert call(1, 510, 0) == 0 and event() == 1
assert call(1, 520, 0x80) == 0
assert call(1, 600, 0x40) == 0
assert call(1, 801, 0x40) == 0x80

# Both: a simultaneous hold stays one logical hold and forwards only R.
put32(cache + 68, 0); put32(cache + 112, 0); put32(cache + 128, 0)
assert call(2, 900, 0xc0) == 0
assert call(2, 1101, 0xc0) == 0x80
assert call(2, 1110, 0) == 0 and event() == 2

# Explicit bypass leaves both bumpers untouched for native menu/ocarina input.
assert call(1, 1200, 0xc0, bypass=1) == 0xc0

# An open wheel pauses gameplay updates in some native paths. Repeated HID
# polls must not alternate mapped L with raw L when the heartbeat stops.
controller, screen, owner, item_list = [base + x for x in (0x220000, 0x230000, 0x240000, 0x250000)]
def put64(address, value):
    emu.mem_write(address, struct.pack('<Q', value))
put64(cache + 48, controller); put64(cache + 16, item_list)
put64(controller + 0x68, item_list); put64(controller + 0x18, screen); put64(controller + 0x20, owner)
put32(controller + 0x78, 10); put32(cache + 36, 10)
emu.mem_write(owner + 0x3a, b'\x02'); emu.mem_write(screen + 0x1a6, b'\x02')
for mode, physical in [(0, 0x80), (1, 0x40), (2, 0x40), (2, 0x80), (2, 0xc0)]:
    put32(cache + 68, 0); put32(cache + 132, 0)
    assert call(mode, 2000, physical, heartbeat=3000) == 0
    for sample in range(2200, 2230):
        assert call(mode, sample, physical, heartbeat=3000) == 0x80, (mode, sample)
    if mode == 1:
        assert call(mode, 2231, 0x80, heartbeat=3000) == 0 # unselected bumper stays blocked
    assert call(mode, 2240, 0, heartbeat=3000) == 0 and event() == 2
# Ocarina bypass always wins, including when a cached wheel looks visible.
assert call(1, 2300, 0x40, bypass=1, heartbeat=3000) == 0x40
# Incomplete binding must not masquerade as an active wheel.
put32(cache + 36, 9)
assert call(1, 2301, 0x40, heartbeat=3000) == 0x40
put32(cache + 36, 10)
# A regular menu still bypasses gameplay mapping when its scheduler is stale.
emu.mem_write(screen + 0x1a6, b'\x00')
assert call(1, 2310, 0x40, heartbeat=3000) == 0x40
print('PASS: compiled standalone bumper routing (Right, Left, Both, bypass)')
