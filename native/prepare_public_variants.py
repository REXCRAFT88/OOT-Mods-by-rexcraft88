from pathlib import Path
import sys,json,struct,zlib,shutil,zstandard as zs
sys.path[:0]=['work','outputs/OOT-Test-Kit'];from nup_overlay import Nup;import oot_assets as a
n=Nup(json.load(open('outputs/OOT-Test-Kit/settings.json'))['source_nup']);pkg=n.best_package();a.init();base=Path('work/public-variants');base.mkdir(exist_ok=True)
common='UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.blarc.zs';texrel=common.replace('blarc','bntx');rssrel='System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs'
def entries(raw):
 h=struct.unpack_from('<H',raw,4)[0];nh,count=struct.unpack_from('<HH',raw,h+4);nodes=h+nh;names=nodes+16*count+8;off=struct.unpack_from('<I',raw,12)[0];out=[]
 for i in range(count):
  hash,attr,s,e=struct.unpack_from('<4I',raw,nodes+i*16);p=names+(attr&0xffffff)*4;name=raw[p:raw.index(0,p)].decode();out.append((hash,name,raw[off+s:off+e]))
 return h,nodes,out
def clean_common(candidate,stamina):
 original=a.decompress(n.read(pkg['index'],'romfs/'+common));h,nodes,orig=entries(original);_,_,edited=entries(a.decompress(candidate.read_bytes()));allow={'ShortCut_01.buil','PaShortCutSlideList_00.buil'}
 if stamina:allow|={'PlayerStatus_00.buil','PaStaminaGauge_00.buil'}
 changed={};counts={}
 for _,name,b in edited:changed.setdefault(name,[]).append(b)
 result=[]
 for hash,name,b in orig:
  i=counts.get(name,0);counts[name]=i+1
  if name in allow:b=changed[name][min(i,len(changed[name])-1)]
  elif stamina and name.endswith('.buil'):b=b.replace(b'ControllerGuide_Pro_04\0',b'ControllerGuide_Pro_03\0')
  result.append((hash,name,b))
 if stamina:result.append(next(e for e in edited if e[1]=='PaStaminaGauge_00.buil'))
 result.sort(key=lambda x:x[0]);names=bytearray();records=[];data=bytearray()
 for hash,name,b in result:
  names.extend(b'\0'*((-len(names))%4));nameoff=len(names)//4;names.extend(name.encode()+b'\0');data.extend(b'\0'*((-len(data))%16));start=len(data);data.extend(b);records.append((hash,0x1000000|nameoff,start,len(data)))
 out=bytearray(original[:nodes]);struct.pack_into('<H',out,h+6,len(records))
 for r in records:out.extend(struct.pack('<4I',*r))
 out.extend(b'SFNT\x08\0\0\0');out.extend(names);out.extend(b'\0'*((-len(out))%4096));off=len(out);out.extend(data);struct.pack_into('<II',out,8,len(out),off);return out
for name,src,stamina in [('hero-with-stamina','work/hero-wheel-trial',True),('hero-without-stamina','work/wheel-standalone-trial',False)]:
 root=base/name;shutil.copytree(Path(src)/'exefs',root/'exefs',dirs_exist_ok=True);shutil.copytree('outputs/OOT-Hero-Mode-AI-v0.4/romfs',root/'romfs',dirs_exist_ok=True)
 b=clean_common(Path(src)/'romfs'/common,stamina);p=root/'romfs'/common;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(zs.ZstdCompressor(level=12,dict_data=a.DICT[1]).compress(b));budgets={common.removesuffix('.zs'):len(b)+131072}
 if stamina:
  tex=bytearray(a.decompress(n.read(pkg['index'],'romfs/'+texrel)))
  from resources.stamina_texture import build_texture
  tex=build_texture(tex,json.loads(Path('work/oot-textures.json').read_text()))
  target=root/texrel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(zs.ZstdCompressor(level=12,dict_data=a.DICT[1]).compress(tex))
  (root/'romfs'/texrel).write_bytes((root/texrel).read_bytes())
  (root/texrel).unlink()
  budgets[texrel.removesuffix('.zs')]=len(tex)+131072
 rss=bytearray(zs.ZstdDecompressor().decompress(n.read(pkg['index'],'romfs/'+rssrel)));count=struct.unpack_from('<I',rss,14)[0]
 for rel,budget in budgets.items():
  crc=zlib.crc32(rel.encode());hits=[i for i in range(22,22+count*8,8) if struct.unpack_from('<I',rss,i)[0]==crc];assert len(hits)==1;i=hits[0]+4;struct.pack_into('<I',rss,i,max(struct.unpack_from('<I',rss,i)[0],(budget+4095)&~4095))
 p=root/'romfs'/rssrel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(zs.ZstdCompressor(level=12).compress(rss));print('Prepared',name,'without PS5 artwork/profile',flush=True)
