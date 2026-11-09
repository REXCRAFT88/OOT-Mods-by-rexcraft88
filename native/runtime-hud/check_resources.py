from pathlib import Path
import struct,subprocess,sys
sys.path.insert(0,"work/hero-review-deps")
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_SP,UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X30
r=Path(sys.argv[1] if len(sys.argv)>1 else 'work/runtime-hud-lab').resolve()
sy={v[2]:int(v[0],16) for l in subprocess.check_output(['llvm-nm',str(r/'hud.elf')],text=True).splitlines() if len(v:=l.split())==3}
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x84f85000,0x80000);u.mem_write(0x84f85100,(r/'hud.bin').read_bytes());u.mem_map(0x100000,0x200000)
def put(p,v,fmt='Q'):u.mem_write(p,struct.pack('<'+fmt,v))
def q(p):return struct.unpack('<Q',u.mem_read(p,8))[0]
def call(name,x0,x1=0):
 u.reg_write(UC_ARM64_REG_SP,0x2f0000);u.reg_write(UC_ARM64_REG_X30,0x2ff000);u.reg_write(UC_ARM64_REG_X0,x0);u.reg_write(UC_ARM64_REG_X1,x1);u.emu_start(0x80000000+sy[name],0x2ff000,count=1000000);return u.reg_read(UC_ARM64_REG_X0)
def string(p,s):u.mem_write(p,s.encode()+b'\0');return p
root=0x110000;config=0x100000;handle=0x101000
put(root,0x004c4955,'I');put(root+0x18,string(0x120000,'PlayerStatus_00'));put(config,root);put(config+0x80,0x12345678)
# Extra HUD pane preceding magic exercises dynamic name resolution.
for off,names,descs in [(0x20,['RootPane','OtherHud','Pa_MpGauge_00'],[0x140000,0x140100,0x140200]),(0xc0,['Pa_MpGauge_00'],[0x141000])]:
 a=0x130000+off*0x20
 for j in range(3):put(root+off+j*8,a+j*0x100)
 put(root+off+24,len(names),'I');put(root+off+28,8,'I')
 for i,n in enumerate(names):put(a+i*8,string(0x150000+off*0x100+i*0x80,n));put(a+0x100+i*8,descs[i])
put(0x141000,string(0x180000,'PaMpGauge_00'))
original=bytes(u.mem_read(root,0x80000))
c=call('hud_prepare',handle,config);assert c!=config;newroot=q(c);assert q(config)==root;assert q(c+0x80)==0x12345678
assert struct.unpack('<I',u.mem_read(newroot+0x38,4))[0]==4
assert q(q(newroot+0x28)+8)==0x140100 # unrelated HUD descriptor untouched
assert bytes(u.mem_read(root,0x80000))==original
layout=0x190000;frame=0x191000;put(frame+0x80,layout);put(layout+0xf8,newroot);put(layout+0x100,0x192000)
assert call('hud_pane',frame,string(0x193000,'Pa_StaminaGauge_00'))==0x192000+3*0xb0
# Private gauge relocation and isolated color/texture replacement.
b=0x200000;g=b+0xf8;put(b,0x48464642,'I');put(b+8,0x7ad8,'I');put(g,0x004c4955,'I');put(g+0x18,string(b+0x7800,'PaMpGauge_00'));put(b+0x35a0,string(b+0x7840,'MpGaugeCenter_00'));u.mem_write(b+0x74e8,struct.pack('<4f',.051,.5647,.2902,1));put(handle+0x30,string(0x1a0000,'Pa_StaminaGauge_00'));put(config,g)
old=bytes(u.mem_read(b,0x7ad8));out=call('hud_prepare',handle,config);ng=q(out);assert ng!=g
assert bytes(u.mem_read(b,0x7ad8))==old
color=struct.unpack('<4f',u.mem_read(ng-0xf8+0x74e8,16));assert color[0]==1 and abs(color[1]-.85)<.0001
assert bytes(u.mem_read(q(ng-0xf8+0x35a0),14))==b'White8_00_BC4L'
assert bytes(u.mem_read(q(ng+0x18),17))==b'PaStaminaGauge_00'
print('PASS: compiled AArch64 private root append, added HUD pane preservation, dynamic pane lookup, relocation, independent yellow palette/texture, source resources unchanged.')

# Wheel edits preserve unrelated metadata and use each source skin's pane list.
r2=0x240000;put(r2,0x004c4955,'I');put(r2+0x18,string(0x241000,'PaShortCutSlideList_00'))
for j in range(3):put(r2+0x20+j*8,0x242000+j*0x100)
put(r2+0x38,3,'I')
for i,name in enumerate(['OtherHud','N_SlideList_00','N_Cursor_00']):
 put(0x242000+i*8,string(0x243000+i*0x80,name));put(0x242100+i*8,0x244000+i*0x80)
put(config,r2);put(handle+0x30,0);old=bytes(u.mem_read(r2,0x5000));wr=q(call('hud_prepare',handle,config));assert wr!=r2
assert q(q(wr+0x28))==0x244000
slide=q(q(wr+0x28)+8);cursor=q(q(wr+0x28)+16)
assert struct.unpack('<f',u.mem_read(slide+44,4))[0]==24000
assert struct.unpack('<f',u.mem_read(cursor+16,4))[0]==0
assert bytes(u.mem_read(r2,0x5000))==old
print('PASS: compiled wheel metadata edits, extra HUD pane preserved, original resource unmodified.')
