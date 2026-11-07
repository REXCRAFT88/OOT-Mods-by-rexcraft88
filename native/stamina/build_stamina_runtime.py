"""Build an isolated NSO candidate from the user's original NUP, preserving other segments."""
import sys,struct,hashlib,json,pathlib,zbic,subprocess
sys.path.insert(0,'outputs/OOT-Test-Kit');from nup_overlay import Nup
s=json.loads(pathlib.Path('outputs/OOT-Test-Kit/settings.json').read_text());n=Nup(s['source_nup']);pkg=n.best_package();original=n.read(pkg['index'],'exefs/main');b=bytearray(original);assert b[:4]==b'NSO0';assert b[64:84].hex().upper()=='E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348'
fileoff,memoff,size=struct.unpack_from('<III',b,0x10);compressed=struct.unpack_from('<I',b,0x60)[0];text=bytearray(zbic.decompress(bytes(b[fileoff:fileoff+compressed])));assert len(text)==size
symbols={parts[2]:int(parts[0],16) for line in subprocess.check_output(['llvm-nm','work/hero_stamina_runtime.elf'],text=True).splitlines() if len(parts:=line.split())==3};payload=pathlib.Path('work/hero_stamina_runtime.bin').read_bytes();cave=0x3c461d0;assert len(text)==cave;assert cave+len(payload)<=0x3c47000;text.extend(payload);changes=[]
def branch(at,to,link=False):
 delta=to-at;assert delta%4==0 and -(1<<27)<=delta<(1<<27);return struct.pack('<I',(0x94000000 if link else 0x14000000)|((delta>>2)&0x3ffffff))
def change(at,new,expected=None):
 old=bytes(text[at:at+len(new)])
 if expected is not None:assert old==expected,(hex(at),old.hex(),expected.hex())
 text[at:at+len(new)]=new;changes.append({'offset':hex(at),'before':old.hex(),'after':new.hex()})
change(0x2b30de0,branch(0x2b30de0,symbols['stamina_frame']),bytes.fromhex('7f2303d5'))
for name,at in json.loads(pathlib.Path('work/stamina-runtime-patches.json').read_text()).items():
 change(at,branch(at,symbols[name]),bytes.fromhex('7f2303d5'))
change(0xa3fb4c,branch(0xa3fb4c,symbols['attack_enter']),bytes.fromhex('a83a41f9'))
change(0x2de4340,branch(0x2de4340,symbols['tired_damage']),bytes.fromhex('08484439'))
for at,target,name in [(0x346966c,0x3c42800,'hid_full'),(0x34694f8,0x3c427f0,'hid_dual'),(0x3469524,0x3c42810,'hid_left'),(0x3469550,0x3c42820,'hid_right'),(0x3469698,0x3c42830,'hid_handheld')]:change(at,branch(at,symbols[name],True),branch(at,target,True))
change(0x33bdce0,branch(0x33bdce0,symbols['hero_mp_init']),bytes.fromhex('7f2303d5'))
# Preserve the original unmodified rodata/data files; append replacement text.
newpacked=bytes(text);struct.pack_into('<I',b,0xc,struct.unpack_from('<I',b,0xc)[0]&~1);b.extend(b'\0'*((-len(b))%0x100));newfile=len(b);b.extend(newpacked);struct.pack_into('<I',b,0x10,newfile);struct.pack_into('<I',b,0x18,len(text));struct.pack_into('<I',b,0x60,len(newpacked));b[0xa0:0xc0]=hashlib.sha256(text).digest()
data_mem,data_size=struct.unpack_from('<II',b,0x34);bss=struct.unpack_from('<I',b,0x3c)[0];assert data_mem+data_size+bss==0x4ea0000;struct.pack_into('<I',b,0x3c,bss+0x1000)
out=pathlib.Path('work/hero-stamina-trial/exefs/main');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b);pathlib.Path('work/hero-stamina-trial/changes.json').write_text(json.dumps({'status':'Native stamina action/frame/gate candidate; live qualification pending','source_build':b[64:84].hex(),'text_size':len(text),'cache_offset':'0x4ea0000','changes':changes},indent=2));print('Built native stamina candidate',len(b),'bytes; source unchanged')
