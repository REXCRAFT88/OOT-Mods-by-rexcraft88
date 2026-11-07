"""Build a standalone wheel from the unmodified game modules."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,shutil,zbic
sys.path.insert(0,'outputs/OOT-Test-Kit')
from nup_overlay import Nup
settings=json.loads(Path('outputs/OOT-Test-Kit/settings.json').read_text())
source=Nup(settings['source_nup']);pkg=source.best_package()
root=Path('work/wheel-standalone-trial');root.mkdir(exist_ok=True)
rel='UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.blarc.zs'
p=root/'romfs'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read(pkg['index'],'romfs/'+rel))
symbols={p[2]:int(p[0],16) for line in subprocess.check_output(['llvm-nm','work/wheel_standalone.elf'],text=True).splitlines() if len(p:=line.split())==3}
payload=Path('work/wheel_standalone.bin').read_bytes()
def text_segment(b):
 off,_,size=struct.unpack_from('<III',b,0x10)
 compressed=struct.unpack_from('<I',b,0x60)[0]
 raw=bytes(b[off:off+compressed])
 if struct.unpack_from('<I',b,0xc)[0]&1:
  try:data=zbic.decompress(raw)
  except zbic.error:
   import lz4.block
   data=lz4.block.decompress(raw,uncompressed_size=size)
 else:data=raw
 assert len(data)==size
 return bytearray(data)
def branch(at,to):
 delta=to-at;assert delta%4==0 and -(1<<27)<=delta<(1<<27)
 return struct.pack('<I',0x14000000|((delta//4)&0x3ffffff))
def emit(b,text,path):
 b=bytearray(b);b.extend(b'\0'*((-len(b))%256));off=len(b);b.extend(text)
 struct.pack_into('<I',b,0xc,struct.unpack_from('<I',b,0xc)[0]&~1)
 struct.pack_into('<I',b,0x10,off);struct.pack_into('<I',b,0x18,len(text));struct.pack_into('<I',b,0x60,len(text))
 b[0xa0:0xc0]=hashlib.sha256(text).digest();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
rtld=source.read(pkg['index'],'exefs/rtld');text=text_segment(rtld)
assert len(text)==0x2740 and len(text)+len(payload)<=0x3000
emit(rtld,text+payload,root/'exefs/rtld')
main=bytearray(source.read(pkg['index'],'exefs/main'));text=text_segment(main);changes=[]
for at,label,expected in [(0x33ca1d0,'wheel_bind_item','e00315aa'),(0xe9ee30,'wheel_list_ctor','7f2303d5'),(0x3773874,'wheel_draw_entry','e923506d'),(0x33c9270,'wheel_update','7f2303d5'),(0x2b30de0,'wheel_tick_entry','7f2303d5'),(0x346966c,'wheel_hid_entry',struct.pack('<I',struct.unpack('<I',branch(0x346966c,0x3c42800))[0]|0x80000000).hex())]:
 assert text[at:at+4].hex()==expected
 replacement=branch(at,symbols[label]-0x20000)
 if label=='wheel_hid_entry':replacement=struct.pack('<I',struct.unpack('<I',replacement)[0]|0x80000000)
 text[at:at+4]=replacement
 changes.append({'offset':hex(at),'target_relative_main':hex(symbols[label]-0x20000),'original':expected,'replacement':replacement.hex()})
# Reserve wheel state in newly added BSS pages.
struct.pack_into('<I',main,0x3c,struct.unpack_from('<I',main,0x3c)[0]+0x5000)
emit(main,text,root/'exefs/main')
(root/'probe.json').write_text(json.dumps({'status':'Experimental native item wheel','rtld_payload_bytes':len(payload),'wheel_cache_relative_main':'0x4ea1000','changes':changes},indent=2))
print('Built native wheel:',len(payload),'bytes; standalone')
