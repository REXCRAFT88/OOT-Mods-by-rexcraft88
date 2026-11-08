from pathlib import Path
import sys,json,struct,subprocess
sys.path.insert(0,'work/publish-oot-mods');import install
root=Path('work/controller-options-native');root.mkdir(exist_ok=True)
asm='''.text
.global options_index
options_index:
 ldr w8,[sp,#16]
 mov w2,#0
 mov w9,#0xc0e7
 movk w9,#0x212d,lsl #16
 cmp w8,w9
 b.eq 1f
 mov w9,#0x692d
 movk w9,#0x390b,lsl #16
 cmp w8,w9
 b.eq 2f
 mov w9,#0x3848
 movk w9,#0xd4b9,lsl #16
 cmp w8,w9
 b.eq 3f
 b 4f
1: mov w2,#1
 b 4f
2: mov w2,#2
 b 4f
3: mov w2,#3
4: ldr w8,[x0,#80]
 ret
'''
# avoid hand-transcribing enum constants
normal=957022509;pro=3568908360
asm=asm.replace('0x692d',hex(normal&65535)).replace('0x390b',hex(normal>>16)).replace('0x3848',hex(pro&65535)).replace('0xd4b9',hex(pro>>16))
(root/'menu.S').write_text(asm)
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-fno-stack-protector','-fno-jump-tables']
for src,out in [(Path(__file__).resolve().parent/'controller_options.c',root/'options.o'),(root/'menu.S',root/'menu.o')]:subprocess.run(['clang',*flags,'-c',str(src),'-o',str(out)],check=True)
for key in ['hero-with-stamina','hero-without-stamina','manual-shield']:
 candidate=Path('work/compatibility-candidates')/key;dst=Path('work/controller-options-candidates')/key
 import shutil
 shutil.copytree(candidate,dst,dirs_exist_ok=True)
 control=0x4f29810 if key=='hero-with-stamina'else 0x4f29770
 begin=0x4f29c40
 (root/'options.ld').write_text(f'SECTIONS {{ . = {begin}; .text : {{ *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }} }}\nhero_control_state = 0x4ea3000; game_data_singleton = 0x4e842a8; read_enum = 0x17bf90; native_controls = {control+4};')
 subprocess.run(['ld.lld.exe','-T',str(root/'options.ld'),str(root/'options.o'),str(root/'menu.o'),'-o',str(root/'options.elf')],check=True)
 sy={v[2]:int(v[0],16)for l in subprocess.check_output(['llvm-nm',str(root/'options.elf')],text=True).splitlines()if len(v:=l.split())==3}
 subprocess.run(['llvm-objcopy','-O','binary','--only-section=.text',str(root/'options.elf'),str(root/'options.bin')],check=True)
 code=(root/'options.bin').read_bytes();print(key,len(code),hex(begin+len(code)))
 assert begin+len(code)<=0x4f2a000
 def branch(a,b,link=False):return struct.pack('<I',(0x94000000 if link else 0x14000000)|(((b-a)//4)&0x3ffffff))
 path=dst/'exefs/subsdk0';blob=path.read_bytes();text=bytearray(install.nso_text(blob));off=begin-0x4ea5000;text.extend(b'\0'*(off-len(text)));text.extend(code)
 # Existing input trampoline points into main's context guard; retarget its tail via IPS.
 d=json.load(open(candidate/'compatibility.json'));resume=d['symbols']['controls_context'];main=bytearray(install.nso_text((dst/'exefs/main').read_bytes()))
 # original compatibility stub ends with B controls_resume before RET
 ips=bytearray((dst/'exefs/E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348.ips').read_bytes());recordaddr,length=struct.unpack_from('>IH',ips,5)
 at=resume+48
 expected=branch(at,control+4)
 matches=[i for i in range(11,11+length-3,4) if ips[i:i+4]==expected]
 # locate branch by decoding rather than relying on stub size
 matches=[]
 for i in range(11,11+length-3,4):
  w=int.from_bytes(ips[i:i+4],'little');pc=recordaddr-0x100+(i-11);imm=w&0x3ffffff;imm-= (1<<26) if imm&(1<<25) else 0
  if w&0xfc000000==0x14000000 and pc+imm*4==control+4:matches.append((i,pc))
 assert len(matches)==1,matches
 i,pc=matches[0];ips[i:i+4]=branch(pc,sy['controller_options_raw']);(dst/'exefs/E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348.ips').write_bytes(ips)
 path.write_bytes(install.emit_nso(blob,text,struct.unpack_from('<I',blob,60)[0]))
 mp=dst/'exefs/main';blob=mp.read_bytes();text=bytearray(install.nso_text(blob));text[0x574e1c:0x574e20]=bytes.fromhex('1f2003d5');text[0x279d640:0x279d648]=bytes.fromhex('00008052c0035fd6')
 text[0x32df4e4:0x32df4e8]=branch(0x32df4e4,sy['options_index'],True);text[0x32df4e8:0x32df500]=bytes.fromhex('1f2003d5')*6
 mp.write_bytes(install.emit_nso(blob,text,struct.unpack_from('<I',blob,60)[0]));(dst/'controller-options.json').write_text(json.dumps({'symbols':sy,'code_bytes':len(code)},indent=2))



