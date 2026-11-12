"""Execute the combat bridge and full mid-function ABI wrapper on AArch64."""
from pathlib import Path
import struct,subprocess,sys,re
sys.path.insert(0,'work/hero-review-deps')
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
import unicorn.arm64_const as R
src=Path(__file__).resolve().parent;root=Path('work/hero-combat-check');root.mkdir(exist_ok=True)
(root/'stub.c').write_text('unsigned test_tier; unsigned long long actor_manager_slot; unsigned hero_difficulty(void){return test_tier;} void actor_lock(void*p){} void actor_unlock(void*p){}\n')
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-ffunction-sections','-fdata-sections','-fno-stack-protector','-fno-jump-tables','-I'+str(src)]
objs=[]
for path,name in [(src/'hero_options.c','policy'),(src/'combat_bridge.c','bridge'),(src/'combat_damage.S','entry'),(root/'stub.c','stub')]:
 obj=root/(name+'.o');subprocess.run(['clang',*flags,'-c',str(path),'-o',str(obj)],check=True);objs.append(str(obj))
(root/'test.ld').write_text('SECTIONS { . = 0x1000; .text : { *(.text*) *(.rodata*) } . = 0x100000; .bss (NOLOAD) : { *(.bss*) } /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\nnative_life_vtable = 0x110000; native_life_value_vtable = 0x111000; native_enemy_attack_resume = 0x400000; native_enemy_body_attack_resume = 0x400000;\n')
subprocess.run(['ld.lld.exe','-T',str(root/'test.ld'),*objs,'-o',str(root/'test.elf')],check=True)
subprocess.run(['llvm-objcopy','-O','binary','--only-section=.text',str(root/'test.elf'),str(root/'text.bin')],check=True)
sy={p[2]:int(p[0],16) for l in subprocess.check_output(['llvm-nm',str(root/'test.elf')],text=True).splitlines() if len(p:=l.split())==3}
for base in [0x80000000,0x90000000]:
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(base,0x600000);u.mem_write(base+0x1000,(root/'text.bin').read_bytes());stop=base+0x400000;stack=base+0x50ff00
 def put32(p,v):u.mem_write(p,struct.pack('<I',v))
 def put64(p,v):u.mem_write(p,struct.pack('<Q',v))
 def putf(p,v):u.mem_write(p,struct.pack('<f',v))
 def get32(p):return struct.unpack('<I',u.mem_read(p,4))[0]
 def call(name,a=0,b=0,c=0):
  u.reg_write(R.UC_ARM64_REG_SP,stack);u.reg_write(R.UC_ARM64_REG_X30,stop)
  for n,v in enumerate([a,b,c]):u.reg_write(getattr(R,'UC_ARM64_REG_X'+str(n)),v)
  u.emu_start(base+sy[name],stop,count=200000);assert u.reg_read(R.UC_ARM64_REG_PC)==stop
 actor,table,life,cur,maximum,name,ai,multiplier,holder,mgr,entry=[base+x for x in [0x200000,0x210000,0x220000,0x230000,0x231000,0x240000,0x250000,0x260000,0x270000,0x280000,0x290000]]
 def named(n):u.mem_write(name,n.encode()+b'\0');put64(actor+0x20,name)
 put64(ai+0x18,actor)
 put32(actor+0x2c,2)
 # Every live register except loaded S0 must survive the mid-function hook.
 for n in ['Enemy_Stalfos','BeamosBeam','Octorok_Bullet','Player','Obj_Fire','Enemy_Scrub_Business','Enemy_Skulltula_Gold']:
  named(n);hostile=n in ['Enemy_Stalfos','BeamosBeam','Octorok_Bullet']
  for tier in range(4):
   put32(base+sy['test_tier'],tier);putf(multiplier,.75)
   expected=[]
   for i in range(31):
    value=0x1100000000000000+i
    if i==0:value=multiplier
    if i==26:value=ai
    if i==30:value=stop
    expected.append(value);u.reg_write(getattr(R,'UC_ARM64_REG_X'+str(i)),value)
   vectors=[]
   for i in range(32):
    value=(0x123456789abcdef0+i)<<64 | (0xfedcba9876543210-i);vectors.append(value);u.reg_write(getattr(R,'UC_ARM64_REG_Q'+str(i)),value)
   u.reg_write(R.UC_ARM64_REG_SP,stack);u.reg_write(R.UC_ARM64_REG_NZCV,0xa0000000)
   put64(stack+0x78,ai)
   # Test the body entry with X26 deliberately NOT an actor/AI pointer.
   entry_name='hero_enemy_body_attack_entry' if tier&1 else 'hero_enemy_attack_entry'
   if tier&1:
    expected[26]=0x1234;u.reg_write(R.UC_ARM64_REG_X26,expected[26])
   u.emu_start(base+sy[entry_name],stop,count=100000)
   assert u.reg_read(R.UC_ARM64_REG_PC)==stop and u.reg_read(R.UC_ARM64_REG_SP)==stack
   assert [u.reg_read(getattr(R,'UC_ARM64_REG_X'+str(i))) for i in range(31)]==expected
   assert [u.reg_read(getattr(R,'UC_ARM64_REG_Q'+str(i))) for i in range(1,32)]==vectors[1:]
   want=.75*([1,2,4,1000000][tier] if hostile else 1)
   assert u.reg_read(R.UC_ARM64_REG_Q0)==struct.unpack('<I',struct.pack('<f',want))[0],(n,tier)
   assert u.reg_read(R.UC_ARM64_REG_NZCV)==0xa0000000
 # Synthetic native Life graph with the exact verified enemy value layout.
 named('Enemy_Stalfos');put32(actor+0x2c,2);put64(actor+0x270,table);put64(table+0x2b8,life)
 put64(life,base+sy['native_life_vtable']);put64(life+0x18,actor);put64(life+0x1c10,cur);put64(life+0x1c18,maximum)
 put64(cur,base+sy['native_life_value_vtable']);put64(maximum,base+sy['native_life_value_vtable']);put32(cur+12,0);put32(maximum+12,0)
 def health(c,m):put32(cur+8,c);put32(maximum+8,m)
 def apply(tier):call('hero_combat_apply_life',actor,tier,1);return get32(cur+8),get32(maximum+8)
 health(27,27);assert apply(0)==(27,27);assert apply(1)==(36,36)
 for _ in range(100):assert apply(1)==(36,36)
 health(18,36);assert apply(0)==(14,27) # preserve fraction, round living HP up
 health(0,27);assert apply(3)==(0,27) # never revive dead actors
 health(3,27);assert apply(1)==(4,36)
 named('Enemy_DungeonBoss_Gohma');health(32,32);assert apply(1)==(42,42);assert apply(0)==(32,32)
 named('Enemy_DungeonBoss_Ganon_SecondHalfBattle');health(27,27);assert apply(1)==(36,36);health(54,54);assert apply(1)==(72,72)
 for n in ['Player','Npc_Zelda','Enemy_Skulltula_Gold','Enemy_Scrub_Business']:
  named(n);health(27,27);assert apply(1)==(27,27)
 named('Enemy_Stalfos');health(19,12345);assert apply(1)==(19,12345)
 health(27,27);put32(cur+12,0x31ab5580);assert apply(1)==(27,27);put32(cur+12,0)
 # Full manager scan prunes despawned identities before reused storage.
 put64(base+sy['actor_manager_slot'],holder);put64(holder,mgr);put64(mgr+0x38,entry+8);put64(entry+0x28,actor)
 put32(base+sy['test_tier'],1);call('hero_difficulty_tick');assert get32(maximum+8)==36
 put64(mgr+0x38,0)
 for _ in range(16):call('hero_difficulty_tick')
 health(27,27);put64(mgr+0x38,entry+8)
 for _ in range(16):call('hero_difficulty_tick')
 assert get32(maximum+8)==36
 # Exercise every shipped Life rule, including variant/phase baselines.
 rules=re.findall(r'\{"([^"]+)",(\d+),(\d+)\}',(src/'combat_inventory.h').read_text())
 for n,stock,legacy in rules:
  stock,legacy=int(stock),int(legacy)
  # Retire the previous identity, as a different native component/spawn would.
  put64(mgr+0x38,0)
  for _ in range(16):call('hero_difficulty_tick')
  named(n);health(legacy,legacy)
  excluded=n.startswith(('Enemy_Scrub_Business','Enemy_Skulltula_Gold'))
  for tier in [0,1,2,3,0,3,1,0]:
   target=legacy if excluded or tier==0 else stock*2
   assert apply(tier)==(target,target),(n,stock,legacy,tier,apply(tier))
   assert apply(tier)==(target,target) # no repeated multiplication
print('PASS: all-register damage-hook ABI, hostile/projectile scoping, four factors, enemy/boss HP tiers, no stacking/revival, phase changes, despawn/reuse at two ASLR bases')
print('PASS:',len(rules),'Life baselines through all four tiers and repeated tier transitions at two ASLR bases')
