"""Execute the lottery filter and entry wrapper; verify exact reward scoping."""
from pathlib import Path
import struct,subprocess,sys,mmh3
sys.path.insert(0,'work/hero-review-deps')
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_PC,UC_ARM64_REG_SP,UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X19,UC_ARM64_REG_X30
src=Path(__file__).resolve().parent;root=Path('work/hero-drop-check');root.mkdir(exist_ok=True)
(root/'stub.c').write_text('extern unsigned test_flag; unsigned hero_no_recovery_drops(void){return test_flag;} unsigned native_name_hash(const char*s,unsigned seed){return 0;} unsigned long long fake_native(void*a,void*out,void*r){return 0x9876;}\n')
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-fno-stack-protector','-fno-jump-tables','-I'+str(src)]
objects=[]
for path,name in [(src/'recovery_drops.c','filter'),(src/'recovery_drops.S','entry'),(root/'stub.c','stub')]:
 obj=root/(name+'.o');subprocess.run(['clang',*flags,'-c',str(path),'-o',str(obj)],check=True);objects.append(str(obj))
(root/'test.ld').write_text('SECTIONS { . = 0x1000; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\ntest_flag = 0x100000; native_drop_lottery_resume = fake_native;\n')
subprocess.run(['ld.lld.exe','-T',str(root/'test.ld'),*objects,'-o',str(root/'test.elf')],check=True)
subprocess.run(['llvm-objcopy','-O','binary','--only-section=.text',str(root/'test.elf'),str(root/'text.bin')],check=True)
sy={p[2]:int(p[0],16) for l in subprocess.check_output(['llvm-nm',str(root/'test.elf')],text=True).splitlines() if len(p:=l.split())==3}
names=['Obj_Heart','Obj_MagicJar_Small','Obj_MagicJar_Large','Obj_Fairy','Obj_HeartContainer','Obj_HeartPiece','Obj_KeySmall','Obj_Rupee_Red','Obj_ArrowBundle_Small','Work/Actor/Obj_Heart.engine__actor__ActorParam.gyml','Quest_Reward','Animal_Insect']
for base in [0x80000000,0x90000000]:
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(base,0x500000);u.mem_write(base+0x1000,(root/'text.bin').read_bytes());stop=base+0x400000
 out,array,records,strings=[base+x for x in [0x200000,0x201000,0x202000,0x203000]]
 def put32(p,v):u.mem_write(p,struct.pack('<I',v))
 def put64(p,v):u.mem_write(p,struct.pack('<Q',v))
 def get64(p):return struct.unpack('<Q',u.mem_read(p,8))[0]
 def text(p):
  b=bytearray()
  for i in range(128):
   c=bytes(u.mem_read(p+i,1))
   if c==b'\0':return b.decode()
   b.extend(c)
  raise AssertionError('unterminated name')
 def hook(emu,pc,size,data):
  if pc==base+sy['native_name_hash']:
   value=mmh3.hash(text(emu.reg_read(UC_ARM64_REG_X0)),signed=False)
   emu.reg_write(UC_ARM64_REG_X0,value);emu.reg_write(UC_ARM64_REG_PC,emu.reg_read(UC_ARM64_REG_X30))
 u.hook_add(UC_HOOK_CODE,hook)
 def reset():
  put32(out,len(names));put32(out+4,16);put64(out+8,array)
  for i,name in enumerate(names):
   record=records+32*i;ptr=strings+128*i
   u.mem_write(ptr,name.encode()+b'\0');put64(array+8*i,record);put64(record,ptr);put32(record+8,mmh3.hash(name,signed=False));u.mem_write(record+12,b'\x5a'*20)
 def call(name):
  u.reg_write(UC_ARM64_REG_SP,stop-0x100);u.reg_write(UC_ARM64_REG_X30,stop);u.reg_write(UC_ARM64_REG_X0,out);u.reg_write(UC_ARM64_REG_X1,out);u.reg_write(UC_ARM64_REG_X19,0x123456)
  u.emu_start(base+sy[name],stop,count=100000);assert u.reg_read(UC_ARM64_REG_PC)==stop
 reset();put32(base+sy['test_flag'],0);before=bytes(u.mem_read(out,0x4000));call('hero_filter_recovery_drops');assert bytes(u.mem_read(out,0x4000))==before
 reset();put32(base+sy['test_flag'],1);call('hero_drop_lottery_entry');assert u.reg_read(UC_ARM64_REG_X0)==0x9876 and u.reg_read(UC_ARM64_REG_X19)==0x123456
 for i,name in enumerate(names):
  record=records+32*i;actual=text(get64(record));want='Obj_Rupee_Green' if i<4 else 'Work/Actor/Obj_Rupee_Green.engine__actor__ActorParam.gyml' if i==9 else name
  assert actual==want,(name,actual);assert get64(array+8*i)==record
  assert struct.unpack('<I',u.mem_read(record+8,4))[0]==mmh3.hash(want,signed=False)
  assert bytes(u.mem_read(record+12,20))==b'\x5a'*20
 reset();put32(out,17);before=bytes(u.mem_read(out,0x4000));call('hero_filter_recovery_drops');assert bytes(u.mem_read(out,0x4000))==before
print('PASS: recovery lottery scope, Off no-op, name/hash consistency, native record ownership, wrapper ABI and malformed bounds at two ASLR bases')
