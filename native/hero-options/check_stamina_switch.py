"""Run the real stamina bridge/core with synthetic native objects on AArch64."""
from pathlib import Path
import struct,subprocess,sys
sys.path.insert(0,'work/hero-review-deps')
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_PC,UC_ARM64_REG_SP,UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X30
project=Path(__file__).resolve().parents[2];root=Path('work/hero-stamina-switch-check');root.mkdir(exist_ok=True)
(root/'stub.c').write_text('''
typedef unsigned long long U; typedef unsigned W;
unsigned char hero_runtime[1024] __attribute__((aligned(16)));
unsigned char hero_user_options[128] __attribute__((aligned(16)));
unsigned char hero_control_state[256] __attribute__((aligned(16)));
U hero_cache[8],actor_manager_slot,battle_info_slot,battle_sound_slot;
W test_disabled,test_amount,test_guard;
void hero_settings_refresh(void){}
void hero_difficulty_tick(void){}
W hero_stamina_enabled(void){return !test_disabled;}
float hero_stamina_amount(void){return test_amount==1?.5f:test_amount==2?2:1;}
void copy_config(void*d,const void*s){for(W i=0;i<80;i++)((char*)d)[i]=((const char*)s)[i];}
void*resolve_player(void*p){return p;}
W as_bool(void*p,W n){return n==14?test_guard:0;}
W as_int(void*p,W n){return n==1?1:0;}
void*find_part(void*p,const char*n){return 0;}
void*find_anim(void*p,const char*n){return 0;}
void set_frame(void*p,float v){}
void actor_lock(void*p){} void actor_unlock(void*p){}
U hero_hud_pane(U p,const char*n){return 0;}
''')
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-fno-stack-protector','-fno-jump-tables','-DHERO_UNIFIED','-Ioutputs/OOT-Test-Kit','-I'+str(project/'native/hero-options')]
for src,name in [(project/'native/runtime-hud/stamina_bridge.c','bridge'),(Path('outputs/OOT-Test-Kit/hero_core.c'),'core'),(root/'stub.c','stub')]:
 subprocess.run(['clang',*flags,'-c',str(src),'-o',str(root/(name+'.o'))],check=True)
(root/'test.ld').write_text('SECTIONS { . = 0x1000; .text : { *(.text*) *(.rodata*) } . = 0x100000; .bss (NOLOAD) : { *(.bss*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\n')
subprocess.run(['ld.lld.exe','-T',str(root/'test.ld'),*[str(root/(n+'.o')) for n in ['bridge','core','stub']],'-o',str(root/'test.elf')],check=True)
subprocess.run(['llvm-objcopy','-O','binary','--only-section=.text',str(root/'test.elf'),str(root/'text.bin')],check=True)
sy={p[2]:int(p[0],16) for l in subprocess.check_output(['llvm-nm',str(root/'test.elf')],text=True).splitlines() if len(p:=l.split())==3}
for base in [0x80000000,0x90000000]:
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(base,0x600000);u.mem_write(base+0x1000,(root/'text.bin').read_bytes());stop=base+0x500000
 def put32(p,v):u.mem_write(p,struct.pack('<I',v))
 def put64(p,v):u.mem_write(p,struct.pack('<Q',v))
 def putf(p,v):u.mem_write(p,struct.pack('<f',v))
 def getf(p):return struct.unpack('<f',u.mem_read(p,4))[0]
 def call(name,a=0,b=0):
  u.reg_write(UC_ARM64_REG_SP,stop-0x100);u.reg_write(UC_ARM64_REG_X30,stop);u.reg_write(UC_ARM64_REG_X0,a);u.reg_write(UC_ARM64_REG_X1,b)
  u.emu_start(base+sy[name],stop,count=100000);assert u.reg_read(UC_ARM64_REG_PC)==stop;return u.reg_read(UC_ARM64_REG_X0)&0xffffffff
 player,actor,table,life,cur,maximum,anim,p1,p2,interface,update,balance=[base+x for x in [0x200000,0x210000,0x220000,0x230000,0x240000,0x241000,0x250000,0x251000,0x252000,0x260000,0x270000,0x280000]]
 for p,off,v in [(player,0x18,actor),(actor,0x270,table),(table,0x2b8,life),(life,0x1c10,cur),(life,0x1c18,maximum),(table,0x40,anim),(anim,0x18,p1),(p1,0x18,p2),(p2,0x40,interface)]:put64(p+off,v)
 put32(cur+8,12);put32(cur+12,0x31ab5580);put32(maximum+8,12);put32(maximum+12,0xfbe01da1)
 putf(update+8,1);putf(anim+0x98,1.25);put64(base+sy['battle_info_slot'],balance);u.mem_write(balance+0x3ce8,b'\1')
 call('hero_default_config',base+sy['hero_user_options']);runtime=base+sy['hero_runtime']
 for amount,want in [(0,100),(1,50),(2,200),(0,100)]:
  put32(base+sy['test_amount'],amount)
  for _ in range(20):call('hero_native_frame',player,update);assert abs(getf(runtime+4)-want)<.001
 # Empty stamina applies fatigue; disabling it restores the original rate.
 putf(runtime,0);call('hero_native_action',0,1);call('hero_native_frame',player,update)
 assert abs(getf(anim+0x98)-1.25*.75)<.001
 put32(base+sy['test_disabled'],1);call('hero_native_frame',player,update)
 assert abs(getf(anim+0x98)-1.25)<.001 and getf(runtime)==getf(runtime+4)
 assert call('hero_native_allow',1)==1
 before=getf(runtime);call('hero_native_action',5,1);call('hero_native_action',6,1);assert getf(runtime)==before
 # Re-enabling preserves the selected capacity and resumes accepted-action costs.
 put32(base+sy['test_disabled'],0);call('hero_native_frame',player,update)
 before=getf(runtime);call('hero_native_action',0,1);assert getf(runtime)<before
print('PASS: actual stamina bridge Half/Full/Double without compounding, disabled costs/restrictions, fatigue restoration, re-enable at two ASLR bases')
