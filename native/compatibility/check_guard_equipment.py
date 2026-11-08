"""Check the compiled guard draw adapter in every guarded variant."""
from pathlib import Path
import sys,json,struct
sys.path.insert(0,'work/hero-review-deps')
from unicorn import *
from unicorn.arm64_const import *
base=0x80000000
for variant in ['hero-with-stamina','hero-without-stamina','manual-shield']:
 root=Path('work/compatibility-candidates')/variant;sy=json.loads((root/'compatibility.json').read_text())['symbols'];u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
 for p,size in [(base+0x5803000,0x2000),(base+0x4ea0000,0x5000),(base+0x37bb000,0x1000),(base+0x6b6000,0x1000),(0x100000,0x1000),(0x200000,0x10000),(0x300000,0x1000)]:u.mem_map(p,size)
 u.mem_write(base+0x5803850,(root/'sdk.bin').read_bytes());calls=[];weapon=0
 def hook(uc,at,size,data):
  if at==base+sy['as_int']:uc.reg_write(UC_ARM64_REG_X0,weapon);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
  elif at==base+sy['native_draw_equipment']:calls.append((uc.reg_read(UC_ARM64_REG_X0),uc.reg_read(UC_ARM64_REG_X1)));uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
 u.hook_add(UC_HOOK_CODE,hook)
 for interface,weapon,want in [(0x100000,0,4),(0x100000,1,4),(0x100000,2,None),(0x100000,3,4),(0x100000,4,4),(0,2,4)]:
  calls.clear();u.mem_write(base+sy['player_as_interface'],struct.pack('<Q',interface));u.reg_write(UC_ARM64_REG_SP,0x208000);u.reg_write(UC_ARM64_REG_X0,0x100123);u.reg_write(UC_ARM64_REG_X1,4);u.reg_write(UC_ARM64_REG_X30,0x300000);u.emu_start(base+sy['hero_guard_draw'],0x300000,count=1000);assert calls==([] if want is None else [(0x100123,want)]),(variant,weapon,calls)
 print('PASS',variant,'two-handed no forced draw (including hammer held); other weapons shield slot4; null-interface passthrough')
