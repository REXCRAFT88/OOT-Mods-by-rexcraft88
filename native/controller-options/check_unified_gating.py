"""Offline AArch64 check for the unified Manual Shield input bypass."""
import pathlib
import struct
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / ".." / "hero-review-deps"))
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_PC, UC_ARM64_REG_SP, UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X30

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "work" / "unified-controller-options-check"
OUT.mkdir(parents=True, exist_ok=True)
BASE = 0x100000
RECORDS = 0x200000
STOP = 0x300000

stub = OUT / "stubs.c"
stub.write_text(r"""
typedef unsigned long long U64;
typedef unsigned U32;
unsigned char hero_control_state[256];
unsigned hero_settings_bits;
void *game_data_singleton;
unsigned native_call_count;
U32 hero_manual_shield_enabled(void) { return !(hero_settings_bits & 2); }
U32 read_enum(void *g, U32 *v, void *d, U32 k) { return 0; }
U32 read_bool(void *g, unsigned char *v, void *d, U32 k) { return 0; }
void native_controls(U64 *records, U32 count) { ++native_call_count; }
""")
flags = ["--target=aarch64-none-elf", "-DHERO_UNIFIED", "-I", str(ROOT / "native" / "hero-options"),
         "-Oz", "-ffreestanding", "-fno-stack-protector", "-fno-jump-tables"]
subprocess.run(["clang", *flags, "-c", str(ROOT / "native/controller-options/controller_options.c"), "-o", str(OUT / "options.o")], check=True)
subprocess.run(["clang", *flags, "-c", str(stub), "-o", str(OUT / "stubs.o")], check=True)
(OUT / "check.ld").write_text("SECTIONS { . = 0x100000; .text : { *(.text*) *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } }")
subprocess.run(["ld.lld.exe", "-T", str(OUT / "check.ld"), str(OUT / "options.o"), str(OUT / "stubs.o"), "-o", str(OUT / "check.elf")], check=True)
symbols = {p[2]: int(p[0], 16) for line in subprocess.check_output(["llvm-nm", str(OUT / "check.elf")], text=True).splitlines() if len(p := line.split()) == 3}
subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.text", str(OUT / "check.elf"), str(OUT / "check.bin")], check=True)
code = (OUT / "check.bin").read_bytes()

u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
u.mem_map(BASE, 0x10000)
u.mem_write(BASE, code)
u.mem_map(RECORDS, 0x1000)
u.mem_map(STOP, 0x1000)
u.mem_write(STOP, b"\x1f\x20\x03\xd5")
u.reg_write(UC_ARM64_REG_SP, BASE + 0x8000)

def put32(name, value):
    u.mem_write(symbols[name], struct.pack("<I", value))

def run(buttons):
    u.mem_write(RECORDS, struct.pack("<5Q", 1, buttons, 0, 0, 0))
    u.reg_write(UC_ARM64_REG_X0, RECORDS)
    u.reg_write(UC_ARM64_REG_X1, 1)
    u.reg_write(UC_ARM64_REG_X30, STOP)
    u.emu_start(symbols["controller_options_raw"], STOP, count=20000)
    assert u.reg_read(UC_ARM64_REG_PC) == STOP
    return struct.unpack("<Q", u.mem_read(RECORDS + 8, 8))[0]

# Off must reach native controls with physical L/ZL unchanged and reset custom
# target state, even if the custom controller layout had previously been used.
put32("hero_settings_bits", 2)
u.mem_write(symbols["hero_control_state"], b"\x01\x01" + b"\0" * 18)
assert run(0x140 | 0x200) == (0x140 | 0x200)
assert u.mem_read(symbols["hero_control_state"], 2) == b"\0\0"
assert struct.unpack("<I", u.mem_read(symbols["hero_control_state"] + 20, 4))[0] == 0xFFFFFFFF
assert struct.unpack("<I", u.mem_read(symbols["native_call_count"], 4))[0] == 1

# On retains the existing wrapper path and invokes native controls once.
put32("hero_settings_bits", 0)
u.mem_write(symbols["hero_control_state"] + 20, struct.pack("<I", 0x212DC0E7))
assert run(0x140 | 0x200) == (0x140 | 0x200)
assert struct.unpack("<I", u.mem_read(symbols["native_call_count"], 4))[0] == 2
print("PASS unified Manual Shield input Off passthrough and On wrapper routing")
