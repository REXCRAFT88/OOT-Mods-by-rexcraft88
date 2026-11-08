import sys,json,struct
sys.path[:0]=['work/hero-review-deps','work/publish-oot-mods'];import install
from unicorn import *
from unicorn.arm64_const import *
from pathlib import Path
base=0x80000000;candidate=Path('work/controller-options-candidates/manual-shield');sy=json.load(open(candidate/'controller-options.json'))['symbols'];code=install.nso_text((candidate/'exefs/subsdk0').read_bytes())
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(base+0x4ea5000,0x85000);u.mem_write(base+0x4ea5000,code);u.mem_map(base+0x4e84000,0x1000);u.mem_map(base+0x4ea0000,0x5000);u.mem_map(base+0x17b000,0x1000);u.mem_map(0x100000,0x10000);u.mem_map(0x200000,0x10000);u.mem_map(0x300000,0x1000)
u.mem_write(base+0x4e842a8,struct.pack('<Q',0x100000));u.mem_write(0x100c20,struct.pack('<Q',0x102000));u.mem_write(0x100c2c,struct.pack('<I',2));u.mem_write(0x102000,struct.pack('<IIII',0x834d9d9e,0,0x834d9d9e,0));u.mem_write(0x100c10,struct.pack('<I',1));u.mem_write(0x100c18,struct.pack('<Q',0x103000));u.mem_write(0x103018,struct.pack('<I',0));u.reg_write(UC_ARM64_REG_SP,0x208000)
mode=1627154745
calls=[]
def intercept(uc,addr,size,data):
 if addr==base+0x17bf90:
  calls.append(uc.reg_read(UC_ARM64_REG_X3));uc.mem_write(uc.reg_read(UC_ARM64_REG_X1),struct.pack('<I',mode));uc.reg_write(UC_ARM64_REG_X0,1);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
u.hook_add(UC_HOOK_CODE,intercept)
def run(bits):
 u.mem_write(0x200000,struct.pack('<QQQQQ',100,bits,0,0,0));u.mem_write(base+0x4ea0888,struct.pack('<I',1));u.reg_write(UC_ARM64_REG_X0,0x200000);u.reg_write(UC_ARM64_REG_X1,1);u.reg_write(UC_ARM64_REG_X30,0x300000);u.emu_start(base+sy['controller_options_raw'],0x300000,count=10000)
 return list(u.mem_read(base+0x4ea3000,3))
for mode,button,guard,toggle in [(1627154745,0x40,0x100,False),(556646631,0x40,0x100,True),(957022509,0x100,0x40,False),(3568908360,0x100,0x40,True)]:
 u.mem_write(base+0x4ea3000,b'\0'*32);assert run(button)[1]==1;assert run(0)[1]==int(toggle);assert run(button)[1]==int(not toggle);run(0);assert run(guard)[2]==1
print('PASS compiled controller wrapper: hold/toggle, both layouts, independent shield',len(calls),'reads')
