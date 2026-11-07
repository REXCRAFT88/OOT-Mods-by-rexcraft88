from pathlib import Path
import json,struct,hashlib,shutil,subprocess,sys
import zbic
sys.path.insert(0,'outputs/OOT-Test-Kit'); from nup_overlay import Nup
root=Path('work/hero-mode-integrated-trial')
base=Path('work/hero-wheel-trial')
source=Nup(json.loads(Path('outputs/OOT-Test-Kit/settings.json').read_text())['source_nup']); pkg=source.best_package()

def text_segment(blob):
    b=bytearray(blob); off,_,size=struct.unpack_from('<III',b,0x10); clen=struct.unpack_from('<I',b,0x60)[0]; raw=bytes(b[off:off+clen])
    if struct.unpack_from('<I',b,0xc)[0]&1:
        try: data=zbic.decompress(raw)
        except zbic.error:
            import lz4.block; data=lz4.block.decompress(raw,uncompressed_size=size)
    else: data=raw
    assert len(data)==size
    return b,bytearray(data)

def emit_text(blob,text):
    b=bytearray(blob); b.extend(b'\0'*((-len(b))%0x100)); off=len(b); b.extend(text)
    struct.pack_into('<I',b,0xc,struct.unpack_from('<I',b,0xc)[0]&~1)
    struct.pack_into('<I',b,0x10,off); struct.pack_into('<I',b,0x18,len(text)); struct.pack_into('<I',b,0x60,len(text))
    b[0xa0:0xc0]=hashlib.sha256(text).digest()
    return b

def branch(at,to):
    d=to-at; assert d%4==0 and -(1<<27)<=d<(1<<27),(hex(at),hex(to),hex(d))
    return struct.pack('<I',0x14000000|((d>>2)&0x3ffffff))

# Build the main + rtld candidate from the latest combined stamina/wheel trial.
main_blob=(base/'exefs/main').read_bytes(); main,text=text_segment(main_blob)
assert main[64:84].hex().upper()=='E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348'
patch_at=0x37ba100; old=bytes(text[patch_at:patch_at+4]); assert old==bytes.fromhex('c101f837'), old.hex()
data_mem,data_size=struct.unpack_from('<II',main,0x34); bss=struct.unpack_from('<I',main,0x3c)[0]; assert data_mem+data_size+bss==0x4ea5000, hex(data_mem+data_size+bss)
symbols={parts[2]:int(parts[0],16) for line in subprocess.check_output(['llvm-nm','work/hero-mode-integrated-trial/hero_controls_runtime.elf'],text=True).splitlines() if len(parts:=line.split())==3}
text[patch_at:patch_at+4]=branch(patch_at,symbols['hero_setter_hook'])
for at,label,expected in [(0x27f7d00,'hero_guard_impact_entry','7f2303d5'),(0x933270,'hero_as_request_hook','7f2303d5'),(0x972e18,'hero_target_guard_flags','0801092a'),(0x97320c,'hero_target_guard_update','29010d32')]:
    assert text[at:at+4].hex()==expected,(hex(at),text[at:at+4].hex())
    text[at:at+4]=branch(at,symbols[label])
main_blob=emit_text(main,text); (root/'exefs/main').write_bytes(main_blob)

rtld_blob=source.read(pkg['index'],'exefs/rtld');rtld,rtld_text=text_segment(rtld_blob)
assert len(rtld_text)==0x2740 and len(rtld_text)+Path('work/hero-mode-integrated-trial/wheel_probe.bin').stat().st_size<=0x3000
rtld_text.extend(Path('work/hero-mode-integrated-trial/wheel_probe.bin').read_bytes())
(root/'exefs/rtld').write_bytes(emit_text(rtld,rtld_text))

# Append the control/guard bridge inside the original subsdk0 text alignment pad.
sub_blob=source.read(pkg['index'],'exefs/subsdk0'); sub,sub_text=text_segment(sub_blob)
assert sub[64:84].hex().upper()=='B0110087A7B339EF74588D3BD0B4DD5D5C7ABD0F'
assert len(sub_text)==0x84770
elf=Path('work/hero-mode-integrated-trial/hero_controls_runtime.elf').read_bytes()
shoff=struct.unpack_from('<Q',elf,0x28)[0];ents,num,strings=struct.unpack_from('<HHH',elf,0x3a)
string_header=shoff+strings*ents;sp,sz=struct.unpack_from('<QQ',elf,string_header+24);names=elf[sp:sp+sz]
text_addresses=[struct.unpack_from('<Q',elf,shoff+i*ents+16)[0] for i in range(num) if names[struct.unpack_from('<I',elf,shoff+i*ents)[0]:].split(b'\0')[0]==b'.text']
assert text_addresses==[0x4ea5000+len(sub_text)], 'Payload link address differs from actual module placement'
control=Path('work/hero-mode-integrated-trial/hero_controls_runtime.bin').read_bytes()
assert len(sub_text)+len(control)<=0x85000
sub_text.extend(control); (root/'exefs/subsdk0').write_bytes(emit_text(sub,sub_text))

# Keep wheel and stamina ROMFS; overlay the verified HeroModeAI v0.4 enemy resources.
shutil.copytree(base/'romfs',root/'romfs',dirs_exist_ok=True)
shutil.copytree(Path('outputs/OOT-Hero-Mode-AI-v0.4/romfs'),root/'romfs',dirs_exist_ok=True)
changes={'status':'Live integrated trial; moving guard, sheathed entry, collision and guard break remain under qualification','main_build_id':main[64:84].hex().upper(),'main_text_bytes':len(text),'subsdk0_build_id':sub[64:84].hex().upper(),'subsdk0_text_bytes':len(sub_text),'subsdk0_payload_offset':'0x84770','subsdk0_payload_bytes':len(control),'subsdk0_base_expected':'main + 0x4ea5000 (main image grew by 0x5000)','wheel_rtld_payload_bytes':len(rtld_text)-0x2740,'control_cache_main_offset':'0x4ea3000','input_masks':{'L2_ZL':'0x100','L1_L':'0x40','R3':'0x20','R1':'0x80'},'patched_setter':{'offset':'0x37ba100','original':old.hex(),'replacement':branch(patch_at,symbols['hero_setter_hook']).hex(),'target_main_relative':hex(symbols['hero_setter_hook']),'scope':'stored player AS pointer at NativeHero+0x80 (slot main+0x4ea0880), Bool14 only'},'guard_frame':'Held/alive/stamina policy; KeepMove component188+0x24 bit5; PlayerState E50 guard flags; scoped AS Bool14; native Square equipment-draw request 0xa43030(Actor,1,1) once on entry. Held-only slot0 Wait/Turn to LockOnWait, Move to LockOnMove. Slot1 and non-locomotion requests preserved. Directional movement still under live qualification.','pause_watchdog':'after >8 HID reads without player ticks, pass native buttons through and clear held guard; sync L1 edge state', 'changes_note':'L1 toggles native ZL targeting; physical ZL is consumed as manual guard. R3 clears target. No CrouchGuard or collision-bit override.'}
(root/'candidate.json').write_text(json.dumps(changes,indent=2))
print(json.dumps({k:changes[k] for k in ['main_text_bytes','subsdk0_text_bytes','subsdk0_payload_bytes','wheel_rtld_payload_bytes','patched_setter']},indent=2))
