"""Execute the native AS-request observer and actual AArch64 cost routine."""
from pathlib import Path
import runpy
globals().update(runpy.run_path('work/publish-oot-mods/native/compatibility/check_combat_gate.py'))
def start(near=1,combat=1,age='Adult'):
 r=Runtime();r.state.initialized=1;r.state.alive=1;r.state.stamina=300;r.state.cap=300;r.state.drain=1;r.state.combat=combat;r.player=0x100000;r.interface=0x109000;r.near=near;r.config[11]=12
 r.config[12]=24;r.config[13]=24;r.config[14]=1
 u.mem_write(runtime,bytes(r));put(runtime+392,0,'I');u.mem_write(0x122000,('Player_'+age+'\0').encode());put(0x101020,0x122000)
def shot(lower,upper=''):
 u.mem_write(0x120000,lower.encode()+b'\0'*32);u.mem_write(0x121000,upper.encode()+b'\0'*32);put(0x100230,0x123000);put(0x100308,0x123000);put(0x100238,0x120000);put(0x100310,0x121000)
 u.reg_write(UC_ARM64_REG_SP,0x208000);u.reg_write(UC_ARM64_REG_X0,runtime);u.reg_write(UC_ARM64_REG_X30,0x300000);u.emu_start(base+sy['hero_item_tick'],0x300000,count=20000)
 return struct.unpack('<f',bytes(u.mem_read(runtime,4)))[0]
start();assert shot('BowCharge')==300;assert shot('BowShoot','BowShootUpper')==296;assert shot('BowShoot','BowShootUpper')==296;assert shot('BowReLoad')==296;assert shot('BowShootUpper')==292
start(age='Child');assert shot('BowShoot')==297
start();assert shot('BoomerangThrow','BoomerangThrowUpper')==297;assert shot('BoomerangThrow')==297;assert shot('BoomerangCatch')==297;assert shot('BoomerangThrowUpper')==294
start(near=0,combat=0);assert shot('BowShoot')==300
# Real native action profile chooses distinct sword / hammer costs.
intpage=(base+sy['as_int'])&~4095
try:u.mem_map(intpage,4096)
except UcError:pass
weapon=1;hammer=False
def weapon_reads(uc,addr,size,data):
 if addr==base+sy['as_int']:uc.reg_write(UC_ARM64_REG_X0,weapon if uc.reg_read(UC_ARM64_REG_X1)==1 else 0);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
 elif addr==base+sy['as_bool']:uc.reg_write(UC_ARM64_REG_X0,int(hammer and uc.reg_read(UC_ARM64_REG_X1)==86))
u.hook_add(UC_HOOK_CODE,weapon_reads)
for weapon,hammer,expected in [(1,False,288),(2,False,276),(1,True,276)]:
 start();u.reg_write(UC_ARM64_REG_SP,0x208000);u.reg_write(UC_ARM64_REG_X0,0);u.reg_write(UC_ARM64_REG_X1,1);u.reg_write(UC_ARM64_REG_X30,0x300000);u.emu_start(base+sy['hero_native_action'],0x300000,count=20000)
 actual=struct.unpack('<f',bytes(u.mem_read(runtime,4)))[0];assert actual==expected,(weapon,hammer,actual)
print('PASS compiled native item releases, aiming exclusion, body-slot deduplication, repeated shots, child slingshot, outside-combat exemption, Master/Biggoron/hammer profiles.')
