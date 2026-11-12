"""Execute the compiled settings reader against a synthetic GameData descriptor."""
from pathlib import Path
import struct,subprocess,sys
sys.path.insert(0,'work/hero-review-deps')
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_PC,UC_ARM64_REG_SP,UC_ARM64_REG_X0,UC_ARM64_REG_X30,UC_ARM64_REG_S0
project=Path(__file__).resolve().parent;root=Path('work/hero-settings-check');root.mkdir(exist_ok=True)
(root/'stub.c').write_text('''
typedef unsigned U; extern U test_tokens[],fail_reads;
U settings_read_enum(void*g,U*out,void*d,U key){
 if(fail_reads)return 0;
 if(key==0x9ea340d8u)*out=test_tokens[1];
 else if(key==0x9fe1614bu)*out=test_tokens[4];
 else if(key==0x76269af3u)*out=test_tokens[5];else return 0;return 1;
}
U settings_read_bool(void*g,unsigned char*out,void*d,U key){
 if(fail_reads)return 0;
 if(key==0xe86f4645u)*out=test_tokens[0];
 else if(key==0xe21b9fedu)*out=test_tokens[2];
 else if(key==0x5af5d93au)*out=test_tokens[3];
 else if(key==0xf1c1f7eeu)*out=test_tokens[6];else return 0;return 1;
}
''')
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-fno-stack-protector','-fno-jump-tables']
for src,name in [(project/'settings.c','settings'),(root/'stub.c','stub')]:
 subprocess.run(['clang',*flags,'-c',str(src),'-o',str(root/(name+'.o'))],check=True)
(root/'test.ld').write_text('SECTIONS { . = 0x1000; .text : { *(.text*) *(.rodata*) } . = 0x110000; .bss (NOLOAD) : { *(.bss*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\ngame_data_singleton = 0x100000; test_tokens = 0x101000; fail_reads = 0x102000;\n')
subprocess.run(['ld.lld.exe','-T',str(root/'test.ld'),str(root/'settings.o'),str(root/'stub.o'),'-o',str(root/'test.elf')],check=True)
subprocess.run(['llvm-objcopy','-O','binary','--only-section=.text',str(root/'test.elf'),str(root/'text.bin')],check=True)
sy={p[2]:int(p[0],16) for line in subprocess.check_output(['llvm-nm',str(root/'test.elf')],text=True).splitlines() if len(p:=line.split())==3}
for base in [0x80000000,0x90000000]:
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(base,0x500000);u.mem_write(base+0x1000,(root/'text.bin').read_bytes());stop=base+0x400000
 def put32(p,v):u.mem_write(p,struct.pack('<I',v))
 def put64(p,v):u.mem_write(p,struct.pack('<Q',v))
 def call(name,floating=False):
  u.reg_write(UC_ARM64_REG_SP,stop-0x100);u.reg_write(UC_ARM64_REG_X30,stop)
  u.emu_start(base+sy[name],stop,count=10000);assert u.reg_read(UC_ARM64_REG_PC)==stop
  return struct.unpack('<f',struct.pack('<I',u.reg_read(UC_ARM64_REG_S0)))[0] if floating else u.reg_read(UC_ARM64_REG_X0)&0xffffffff
 def values():return [call(n) for n in ['hero_stamina_enabled','hero_manual_shield_enabled','hero_wheel_enabled','hero_wheel_bumper','hero_difficulty','hero_no_recovery_drops']]+[call('hero_stamina_amount',True)]
 assert values()==[1,1,1,0,0,0,1.0]
 call('hero_settings_refresh');assert values()==[1,1,1,0,0,0,1.0] # no GameData yet
 g=base+0x200000;mapping=base+0x210000;entry=base+0x220000
 put64(base+sy['game_data_singleton'],g);put64(g+0xc20,mapping);put32(g+0xc2c,1);put32(g+0xc10,1);put64(g+0xc18,entry)
 put32(mapping,0x834d9d9e);put32(mapping+4,0)
 def tokens(v):u.mem_write(base+sy['test_tokens'],struct.pack('<7I',*v));call('hero_settings_refresh')
 tokens([0,0x60fc6939,0,0,0x212dc0e7,0xd4b93848,1]);assert values()==[0,0,0,1,3,1,.5]
 tokens([1,0x212dc0e7,1,1,0x390b012d,0x390b012d,0]);assert values()==[1,1,1,2,2,0,2.0]
 tokens([1,0x390b012d,1,1,0x60fc6939,0x212dc0e7,0]);assert values()==[1,1,1,0,1,0,1.0]
 tokens([1,0xffffffff,1,1,0xffffffff,0xffffffff,0]);assert values()==[1,1,1,0,0,0,1.0]
 put32(base+sy['fail_reads'],1);tokens([0]*7);assert values()==[1,1,1,0,0,0,1.0]
print('PASS: unified Hero settings defaults, aliases, all tiers/capacities, invalid/missing values at two ASLR bases')
