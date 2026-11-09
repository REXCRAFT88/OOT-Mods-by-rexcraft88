from pathlib import Path
import sys,subprocess,struct
sys.path[:0]=['work/hero-review-deps','work/publish-oot-mods'];import install
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
from unicorn.arm64_const import *
root=Path('work/runtime-hud-lab/candidate/exefs');sy={v[2]:int(v[0],16) for line in subprocess.check_output(['llvm-nm','work/hero-mode-integrated-trial/wheel_probe.elf'],text=True).splitlines() if len(v:=line.split())==3}
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);rtld=0x7ffe0000;cache=0x84ea1000;u.mem_map(rtld,0x10000);u.mem_map(cache,0x1000);u.mem_map(0x100000,0x10000);u.mem_write(rtld,install.nso_text((root/'rtld').read_bytes()))
u.mem_write(cache,struct.pack('<2Q',0x111,0x222))
for ptr in [0x2156780000,0x2167890000]:
 u.reg_write(UC_ARM64_REG_SP,0x108000);u.reg_write(UC_ARM64_REG_X0,ptr);u.reg_write(UC_ARM64_REG_X1,0x12345);u.reg_write(UC_ARM64_REG_X16,0x777);u.reg_write(UC_ARM64_REG_X17,0x888)
 u.emu_start(rtld+sy['wheel_bind_entry'],rtld+sy['wheel_bind_entry']+32,count=16)
 assert struct.unpack('<Q',u.mem_read(cache+16,8))[0]==ptr
 assert bytes(u.mem_read(cache,16))==struct.pack('<2Q',0x111,0x222)
 assert u.reg_read(UC_ARM64_REG_X0)==ptr and u.reg_read(UC_ARM64_REG_X16)==0x777 and u.reg_read(UC_ARM64_REG_X17)==0x888
 assert u.reg_read(UC_ARM64_REG_SP)==0x108000
assert install.nso_text((root/'main').read_bytes())[0xe9ee30:0xe9ee34]==bytes.fromhex('7f2303d5')
print('PASS AArch64 item binding refreshes only the wheel-list cache across replacement lists, preserves arguments/registers/stack; generic list capture removed.')
