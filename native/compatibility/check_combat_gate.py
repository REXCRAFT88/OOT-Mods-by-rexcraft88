"""Exercise the compiled AArch64 stamina frame with synthetic native records."""
import sys,json,struct,ctypes as C
from pathlib import Path
sys.path[:0]=['work/hero-review-deps','work/publish-oot-mods']
import install
from unicorn import *
from unicorn.arm64_const import *
sy=json.loads(Path('work/compatibility-candidates/hero-with-stamina/compatibility.json').read_text())['symbols'];base=0x80000000
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
for at,size in [(base+0x3c46000,0x1000),(base+0x5803000,0x2000),(base+0x4ea0000,0x5000),(base+0x4e37000,0x1000),(base+0x4dd3000,0x1000),(0x100000,0x30000),(0x200000,0x10000),(0x300000,0x1000)]:u.mem_map(at,size)
u.mem_write(base+0x3c46600,Path('work/compatibility-candidates/hero-with-stamina/main.bin').read_bytes());u.mem_write(base+0x5803850,Path('work/compatibility-candidates/hero-with-stamina/sdk.bin').read_bytes())
# Imported native calls outside our compiled image.
imports=['resolve_player','as_bool','hero_tick']
for name in imports:
 at=(base+sy[name])&~4095
 try:u.mem_map(at,4096)
 except UcError:pass

def put(p,v,fmt='Q'):u.mem_write(p,struct.pack('<'+fmt,v))
for p,v in [(0x100018,0x101000),(0x101270,0x102000),(0x1022b8,0x103000),(0x103000+0x1c10,0x104000),(0x103000+0x1c18,0x105000),(0x102040,0x106000),(0x106018,0x107000),(0x107018,0x108000),(0x108040,0x109000)]:put(p,v)
put(0x10400c,0x31ab5580,'I');put(0x10500c,0xfbe01da1,'I');put(0x105008,48,'I');put(0x110008,1.,'f')
# Runtime offsets mirror NativeHero ABI; asserts include known published offsets.
class State(C.Structure):_fields_=[('stamina',C.c_float),('cap',C.c_float),('full',C.c_float),('idle',C.c_float),('drain',C.c_float),('initialized',C.c_uint),('lasttoken',C.c_uint),('lastimpact',C.c_uint),('alive',C.c_uint),('combat',C.c_uint)]
class Runtime(C.Structure):_fields_=[('state',State),('config',C.c_float*20),('player',C.c_uint64),('interface',C.c_uint64),('ticks',C.c_uint),('token',C.c_uint),('mask',C.c_uint),('kind',C.c_uint),('weapon',C.c_uint),('near',C.c_uint),('previous_hp',C.c_uint),('delta',C.c_float),('spent',C.c_float),('damage',C.c_float),('speed',C.c_float),('override',C.c_uint),('bar',C.c_uint64),('ratio',C.c_uint64),('trace',C.c_uint64),('maximum',C.c_uint64),('color',C.c_uint64),('owner',C.c_uint64),('laststamina',C.c_float),('lastcapacity',C.c_float),('grace',C.c_float),('savedrate',C.c_float),('fatigue',C.c_uint)]
assert Runtime.ticks.offset==136
runtime=base+sy['hero_runtime'];guard=False;seen=[]
def hook(uc,addr,size,data):
 name=next((n for n in imports if addr==base+sy[n]),None)
 if not name:return
 if name=='resolve_player':uc.reg_write(UC_ARM64_REG_X0,0x100000)
 elif name=='as_bool':uc.reg_write(UC_ARM64_REG_X0,int(guard))
 else:
  p=uc.reg_read(UC_ARM64_REG_X2);seen.append(struct.unpack('<I',bytes(uc.mem_read(p+24,4)))[0])
 uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
u.hook_add(UC_HOOK_CODE,hook)
rows=[]
for label,near,attack,target,held,previous,hp,grace,expected in [
 ('quiet near enemy',1,0,0,0,48,48,0,0),('attack near enemy',1,1,0,0,48,48,0,1),('guard near enemy',1,0,0,1,48,48,0,1),('target near enemy',1,0,1,0,48,48,0,1),('damage near enemy',1,0,0,0,48,44,0,1),('attack outside combat',0,1,0,0,48,48,0,0),('target outside combat',0,0,1,0,48,48,0,0),('near grace active',1,0,0,0,48,48,1,1),('near grace expired',1,0,0,0,48,48,.001,0),('enemy gone',0,0,0,0,48,48,3,0)]:
 r=Runtime();r.state.initialized=1;r.player=0x100000;r.ticks=1;r.near=near;r.mask=attack;r.previous_hp=previous;r.grace=grace;r.speed=1
 u.mem_write(runtime,bytes(r));put(0x104008,hp,'I');u.mem_write(base+0x4ea3000,bytes([0,target,held]));guard=bool(held)
 u.reg_write(UC_ARM64_REG_SP,0x208000);u.reg_write(UC_ARM64_REG_X0,0);u.reg_write(UC_ARM64_REG_X1,0x110000);u.reg_write(UC_ARM64_REG_X30,0x300000)
 u.emu_start(base+sy['hero_native_frame'],0x300000,count=20000)
 assert seen[-1]==expected,(label,seen[-1],expected);rows.append({'case':label,'combat':seen[-1]})
Path('work/compatibility-candidates/combat-gate-check.json').write_text(json.dumps(rows,indent=2));print('PASS compiled native frame combat gate:',len(rows),'cases')
