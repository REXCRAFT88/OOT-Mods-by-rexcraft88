"""Finalize a relinked Hero stamina research candidate; never patches a game NUP."""
from pathlib import Path
import argparse,json,shutil,struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import install
import zstandard as zs

def finalize(base,output,module):
 base,output,module=map(lambda p:Path(p).resolve(),(base,output,module))
 if output==base or output.is_relative_to(base):raise ValueError('Output must be outside the input candidate')
 if output.exists() and any(output.iterdir()):raise ValueError('Choose a new empty output folder')
 symbols=json.loads((base/'compatibility.json').read_text())['symbols']
 if symbols.get('hero_hud_pane')!=0x4f85104 or symbols.get('hero_guard_draw',0)<0x5883850:
  raise ValueError('Input must first be relinked for the 0x80000 private-module SDK shift')
 output.mkdir(parents=True,exist_ok=True)
 for folder in ['exefs','romfs']:shutil.copytree(base/folder,output/folder,dirs_exist_ok=True)
 p=output/'exefs/main';blob=p.read_bytes();text=bytearray(install.nso_text(blob));at=0x43a6f8
 if text[at:at+4]!=bytes.fromhex('7f2303d5'):raise ValueError('Unexpected layout initializer')
 w=struct.unpack_from('<I',text,0x33ca110)[0];d=w&0x3ffffff;d-=1<<26 if d&(1<<25) else 0
 if w&0xfc000000!=0x14000000:raise ValueError('Expected existing item binding trampoline')
 bind=0x33ca110+d*4+0x20000
 text[at:at+4]=struct.pack('<I',0x14000000|(((0x4f85100-at)//4)&0x3ffffff));text[0xe9ee30:0xe9ee34]=bytes.fromhex('7f2303d5')
 p.write_bytes(install.emit_nso(blob,text,struct.unpack_from('<I',blob,60)[0]))
 p=output/'exefs/rtld';blob=p.read_bytes();text=bytearray(install.nso_text(blob))
 if text[bind+12:bind+16]!=bytes.fromhex('000600a9'):raise ValueError('Unexpected item binding probe')
 text[bind+12:bind+16]=bytes.fromhex('000a00f9');p.write_bytes(install.emit_nso(blob,text,struct.unpack_from('<I',blob,60)[0]))
 shutil.copyfile(module,output/'exefs/subsdk1')
 for suffix in ['blarc.zs','bntx.zs']:
  p=output/'romfs/UI/Layout2Archive'/('Common.Product.100.Nin_Ounce_NVN2.'+suffix)
  if p.exists():p.unlink()
 p=output/'romfs/System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs';raw=bytearray(zs.ZstdDecompressor().decompress(p.read_bytes()));count=struct.unpack_from('<I',raw,14)[0]
 pos=next(i for i in range(22,22+count*8,8)if struct.unpack_from('<I',raw,i)[0]==0x8909365f)
 struct.pack_into('<I',raw,pos+4,max(16384,struct.unpack_from('<I',raw,pos+4)[0]));p.write_bytes(zs.ZstdCompressor(level=12).compress(raw))
 print('Finalized private runtime HUD candidate:',output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True);p.add_argument('--output',required=True);p.add_argument('--module',required=True);a=p.parse_args();finalize(a.base,a.output,a.module)
