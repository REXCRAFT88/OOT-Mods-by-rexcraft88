"""Execute the compiled AArch64 candidate at a relocated base, without the game."""
import sys,pathlib,struct,subprocess,json
sys.path.insert(0,'work/hero-review-deps')
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X30,UC_ARM64_REG_SP,UC_ARM64_REG_PC
root=pathlib.Path('work/hero-mode-integrated-trial')
symbols={p[2]:int(p[0],16) for l in subprocess.check_output(['llvm-nm',str(root/'hero_controls_runtime.elf')],text=True).splitlines() if len(p:=l.split())==3}
base=0x80000000;u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);mapped=set()
def maprange(addr,size):
 for p in range(addr&~4095,(addr+size+4095)&~4095,4096):
  if p not in mapped:u.mem_map(p,4096);mapped.add(p)
def write(p,b):maprange(p,len(b));u.mem_write(p,b)
def word(p,n):write(p,struct.pack('<I',n))
def quad(p,n):write(p,struct.pack('<Q',n))
def get(p):return struct.unpack('<I',u.mem_read(p,4))[0]
code=(root/'hero_controls_runtime.bin').read_bytes();placement=0x4ea5000+0x84770
assert symbols['hero_guard_impact']==placement, 'ELF code address differs from mapped NSO code'
write(base+placement,code)
main=(root/'exefs/main').read_bytes();textoff=struct.unpack_from('<I',main,16)[0]
for a,n in [(0x974eb0,24),(0x37ba100,0x3c)]:write(base+a,main[textoff+a:textoff+a+n])
stop=0x90000000;write(stop,b'\x1f\x20\x03\xd5');maprange(0x91000000,0x10000)
state=base+0x4ea3000;runtime=base+0x4ea0800;cache=base+0x4ea0000;maprange(cache,0x5000)
records=0x92000000;maprange(records,0x1000)
def run(name,*args):
 for r,v in zip([UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2],args):u.reg_write(r,v)
 u.reg_write(UC_ARM64_REG_SP,0x9100fff0);u.reg_write(UC_ARM64_REG_X30,stop)
 u.emu_start(base+symbols.get(name,0),stop,count=200000)
 assert u.reg_read(UC_ARM64_REG_PC)==stop,name
tick=0
def raw(bits,n=8,advance=True):
 global tick
 if advance:tick+=1;word(runtime+136,tick)
 for i in range(n):write(records+i*40,struct.pack('<5Q',tick,bits,0,0,0))
 run('hero_controls_raw',records,n)
 return struct.unpack('<Q',u.mem_read(records+8,8))[0]
assert raw(0x40|0x100|0x200|1)==0x100|0x200|1
assert u.mem_read(state+1,2)==b'\x01\x01'
assert raw(0x200)==0x300
assert raw(0x40|0x200)==0x200
assert u.mem_read(state+1,2)==b'\0\0'
raw(0);raw(0x40);assert raw(0x20|0x200)==0x220
assert u.mem_read(state+1,1)==b'\0'
for _ in range(10):v=raw(0x140|0x200,advance=False)
assert v==0x200 and u.mem_read(state+2,1)==b'\0'
raw(0x20)
assert raw(0x200|0x100|8,n=64)==0x308
player=0x93000000;actor=0x93003000;table=0x93006000;component=0x93009000;equipment=0x9300c000
animation=0x9300f000;vtable=0x93012000;values=0x93015000;dirty=0x93018000
maprange(player,0x1b000)
quad(cache,player);quad(player+0x18,actor);quad(actor+0x270,table);quad(table+0x188,component);quad(table+0x200,equipment)
quad(runtime+0x80,animation);quad(animation,vtable);quad(vtable+0x88,base+0x37ba100)
quad(animation+0x30,values);quad(animation+0x60,dirty);word(values,64);word(dirty,64)
write(runtime,struct.pack('<5f',100,100,100,0,1));word(runtime+20,1);word(runtime+32,1);word(runtime+36,1)
draw=[];drawaddr=base+0x6b6820;write(drawaddr,b'\xc0\x03\x5f\xd6')
def ondraw(uc,addr,size,data):
 draw.append((uc.reg_read(UC_ARM64_REG_X0),uc.reg_read(UC_ARM64_REG_X1),uc.reg_read(UC_ARM64_REG_X2)))
u.hook_add(UC_HOOK_CODE,ondraw,begin=drawaddr,end=drawaddr)
write(state+2,b'\x01');word(component+0x24,0x400)
run('hero_guard_frame')
assert get(component+0x24)==0x420 and u.mem_read(values+18,1)==b'\x01'
assert len(draw)==1 and draw[0][:2]==(equipment,4)
run('hero_guard_frame');assert len(draw)==1
write(state+2,b'\0');run('hero_guard_frame');assert get(component+0x24)==0x400 and u.mem_read(values+18,1)==b'\0'
write(state+2,b'\x01');write(runtime,struct.pack('<f',0));run('hero_guard_frame');assert u.mem_read(values+18,1)==b'\0'
word(runtime+36,0);run('hero_guard_frame');assert u.mem_read(values+18,1)==b'\x01'
word(runtime+32,0);run('hero_guard_frame');assert u.mem_read(values+18,1)==b'\0'
# Exercise the real setter hook for another bool index and another AS object.
symbols['setter_test']=0x37ba100
run('setter_test',animation,15,1);assert u.mem_read(values+19,1)==b'\x01'
other=0x9301c000;maprange(other,4096);quad(other+0x30,values);quad(other+0x60,dirty)
run('setter_test',other,14,1);assert u.mem_read(values+18,1)==b'\x01'
# Actual request trampoline: preserve the native StringRef ABI and scope.
request_log=[]
body=base+0x933274;write(body,b'\xc0\x03\x5f\xd6')
def requested(uc,addr,size,data):
 ref=uc.reg_read(UC_ARM64_REG_X2);p=struct.unpack('<Q',uc.mem_read(ref,8))[0]
 request_log.append(bytes(uc.mem_read(p,20)).split(b'\0')[0].decode())
u.hook_add(UC_HOOK_CODE,requested,begin=body,end=body)
ref=0x9301d000;text=ref+256;quad(ref,text);write(text,b'CommonUpper\0'+b'\0'*20)
write(state+4,b'\x01');symbols['request_hook_test']=symbols['hero_as_request_hook']
run('request_hook_test',player,1,ref);assert request_log[-1]=='CommonUpper'
write(text,b'Wait\0'+b'\0'*20);run('request_hook_test',player,0,ref);assert request_log[-1]=='Wait'
write(text,b'Move\0'+b'\0'*20);run('request_hook_test',player,0,ref);assert request_log[-1]=='Move'
write(text,b'BowChargeUpper\0');run('request_hook_test',player,1,ref);assert request_log[-1]=='BowChargeUpper'
# Real compiled block-cost adapter: one event, scoped player, combat-only, no underflow.
write(base+0x973030,b'\xc0\x03\x5f\xd6')
write(state+4,b'\x01');word(runtime+20,1);word(runtime+32,1);word(runtime+36,1)
write(runtime,struct.pack('<f',100));write(runtime+16,struct.pack('<f',1.5));write(runtime+64,struct.pack('<f',8));write(runtime+12,struct.pack('<f',9))
run('hero_guard_impact',player);assert struct.unpack('<f',u.mem_read(runtime,4))[0]==88 and get(runtime+12)==0
before=bytes(u.mem_read(runtime,184));run('hero_guard_impact',other);assert bytes(u.mem_read(runtime,184))==before
word(runtime+36,0);run('hero_guard_impact',player);assert struct.unpack('<f',u.mem_read(runtime,4))[0]==88
word(runtime+36,1);write(state+4,b'\0');run('hero_guard_impact',player);assert struct.unpack('<f',u.mem_read(runtime,4))[0]==88
write(state+4,b'\1');write(runtime,struct.pack('<f',5));run('hero_guard_impact',player);assert get(runtime)==0 and struct.unpack('<f',u.mem_read(runtime+168,4))[0]==5
result={'confirmed_block_cost_scoped_combat_and_clamp':True,'relocated_base':hex(base),'input_toggle_and_R2_preservation':True,'64_state_input_batch':True,'pause_passthrough':True,'scoped_AS_setter':True,'guard_AS_request_and_StringRef_ABI':True,'guard_frame_request_bit':True,'one_draw_per_guard_entry':True,'combat_exhaustion_disallows_guard':True,'outside_combat_zero_stamina_allows_guard':True,'dead_player_disallows_guard':True,'native_collision_and_visible_pose':'Not established by emulation; require live qualification'}
pathlib.Path('work/hero-research/hero-controls-a64-review.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
