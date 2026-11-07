from pathlib import Path
import struct,sys,json,cityhash,zstandard as zs
sys.path.insert(0,'work');import oot_assets as a
a.init();root=Path('work/hero-stamina-trial/romfs');rel='UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.blarc.zs';source=Path('outputs/OOT-PS5-Buttons-v0.2/romfs')/rel;archive=a.decompress(source.read_bytes());members=a.sarc(archive)
def clone_hud(raw):
 old=bytearray(raw);pool=struct.unpack_from('<Q',old,0xe0)[0];poolsize=struct.unpack_from('<I',old,0xd8)[0];extra=bytearray()
 def alloc(data):
  extra.extend(b'\0'*((-len(extra))%8));p=pool+len(extra);extra.extend(data);return p
 def table(h,which):
  count=struct.unpack_from('<I',old,h+24)[0];p=struct.unpack_from('<Q',old,h+which*8)[0];return list(struct.unpack_from('<'+'Q'*count,old,p))
 descs=table(0x118,1);common=bytearray(old[descs[8]:descs[8]+68]);struct.pack_into('<I',common,40,0);struct.pack_into('<I',common,52,34);struct.pack_into('<I',common,64,0x7ffff)
 struct.pack_into('<ff',common,28,-1560,754) # stock world MP position with 80 local units of clearance
 struct.pack_into('<I',old,descs[0]+52,34)
 common[56]|=1 # new part starts visible; original magic part is controller-hidden
 pcommon=alloc(common)
 parts=table(0x1b8,1);part=bytearray(old[parts[1]:parts[1]+88]);struct.pack_into('<I',part,64,33);ppart=alloc(part)
 name='Pa_StaminaGauge_00';asset='PaStaminaGauge_00'
 nameoff=pool+0 # fixed after the final extra size is known
 arrays={}
 for h,count,newdesc in [(0x118,34,pcommon),(0x1b8,8,ppart)]:
  for j in range(3):
   vals=table(h,j);vals.append(newdesc if j==1 else cityhash.CityHash64(name) if j==2 else 0)
   arrays[h,j]=alloc(struct.pack('<'+'Q'*len(vals),*vals))
 extra.extend(b'\0'*((-len(extra))%8));delta=len(extra)
 # Relocate old StringPool pointers; keep all other existing offsets stable.
 for p in range(0xf8,pool-7,8):
  value=struct.unpack_from('<Q',old,p)[0]
  if pool<=value<pool+poolsize:struct.pack_into('<Q',old,p,value+delta)
 out=old[:pool]+extra+old[pool:]
 for h,count in [(0x118,34),(0x1b8,8)]:
  for i in range(count-1):
   p=arrays[h,0]+i*8;value=struct.unpack_from('<Q',out,p)[0]
   assert pool<=value<pool+poolsize
   struct.pack_into('<Q',out,p,value+delta)
 np=len(out);out.extend(name.encode()+b'\0');ap=len(out);out.extend(asset.encode()+b'\0')
 for h,count in [(0x118,34),(0x1b8,8)]:
  for j in range(3):struct.pack_into('<Q',out,h+j*8,arrays[h,j])
  struct.pack_into('<I',out,h+24,count);struct.pack_into('<Q',out,arrays[h,0]+(count-1)*8,np)
 struct.pack_into('<Q',out,ppart,ap)
 # The new part's empty override list remains in the original Default section.
 struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,0xb0,struct.unpack_from('<I',old,0xb0)[0]+delta)
 struct.pack_into('<I',out,0xd4,pool+delta);struct.pack_into('<Q',out,0xe0,pool+delta);struct.pack_into('<I',out,0xd8,len(out)-(pool+delta))
 return bytes(out)
# Rebuild SARC metadata while preserving every duplicate member and data offset relative to the data block.
h=struct.unpack_from('<H',archive,4)[0];dataoff=struct.unpack_from('<I',archive,12)[0];nh,n=struct.unpack_from('<HH',archive,h+4);nodes=h+nh;names=nodes+16*n+8;pool=bytearray(archive[names:dataoff]);data=bytearray(archive[dataoff:]);records=[];changed=0
for i in range(n):
 rec=list(struct.unpack_from('<IIII',archive,nodes+i*16));_,attr,st,en=rec;p=names+(attr&0xffffff)*4;name=archive[p:archive.index(0,p)].decode()
 if name=='PlayerStatus_00.buil':
  patched=clone_hud(archive[dataoff+st:dataoff+en]);data.extend(b'\0'*((-len(data))%16));rec[2]=len(data);data.extend(patched);rec[3]=len(data);changed+=1
 if name.endswith('.buil') and name!='PlayerStatus_00.buil':
  raw=archive[dataoff+st:dataoff+en]
  if b'ControllerGuide_Pro_04\0' in raw:
   replacement=raw.replace(b'ControllerGuide_Pro_04\0',b'ControllerGuide_Pro_03\0');data.extend(b'\0'*((-len(data))%16));rec[2]=len(data);data.extend(replacement);rec[3]=len(data)
 records.append(rec)
# Separate gauge asset: original magic meter remains untouched.
bar=bytearray(members['PaMpGauge_00.buil']);old=struct.unpack_from('<4f',bar,0x74e8);assert abs(old[1]-.5647)<.0001;struct.pack_into('<4f',bar,0x74e8,1,.85,.15,1)
# Reserve an unused transparent PS5 guide layer as a separate yellow texture view.
texture_name=len(bar);bar.extend(b'ControllerGuide_Pro_04\0');struct.pack_into('<Q',bar,0x35a0,texture_name)
internal=len(bar);bar.extend(b'PaStaminaGauge_00\0');struct.pack_into('<Q',bar,0x110,internal);struct.pack_into('<I',bar,8,len(bar));struct.pack_into('<I',bar,0xd8,len(bar)-struct.unpack_from('<Q',bar,0xe0)[0])
name='PaStaminaGauge_00.buil';newhash=0
for c in name.encode():newhash=(newhash*0x65+c)&0xffffffff
pool.extend(b'\0'*((-len(pool))%4));nameoff=len(pool)//4;pool.extend(name.encode()+b'\0');pool.extend(b'\0'*((-len(pool))%4));data.extend(b'\0'*((-len(data))%16));st=len(data);data.extend(bar);records.append([newhash,0x1000000|nameoff,st,len(data)]);records.sort(key=lambda x:x[0])
meta=bytearray(archive[:nodes]);struct.pack_into('<H',meta,h+6,len(records))
for rec in records:meta.extend(struct.pack('<IIII',*rec))
meta.extend(archive[names-8:names]);meta.extend(pool);meta.extend(b'\0'*((-len(meta))%4096));newdata=len(meta);meta.extend(data);struct.pack_into('<I',meta,12,newdata);struct.pack_into('<I',meta,8,len(meta));assert a.sarc(meta)[name]==bar;assert changed>0
out=root/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(zs.ZstdCompressor(level=12,dict_data=a.DICT[1]).compress(meta));assert a.decompress(out.read_bytes())==meta
Path('work/stamina-hud-layout.json').write_text(json.dumps({'status':'Unvalidated additive HUD layout trial','root_copies_patched':changed,'new_part':'Pa_StaminaGauge_00','new_asset':name,'bar_color_rgba':[1,.85,.15,1],'old_palette_rgba':old,'old_archive_size':len(archive),'new_archive_size':len(meta)},indent=2));print('Added independent stamina gauge part:',changed,'root variants; archive growth',len(meta)-len(archive))

# Expanded UI archives also require a matching resource allocation budget.
import zlib
rssrel='System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs';rss=bytearray(a.decompress(a.read('package1/romfs/'+rssrel)));count=struct.unpack_from('<I',rss,14)[0];wanted=zlib.crc32(rel.removesuffix('.zs').encode());hits=[]
for p in range(22,22+count*8,8):
 if struct.unpack_from('<I',rss,p)[0]==wanted:hits.append(p)
assert len(hits)==1;oldbudget=struct.unpack_from('<I',rss,hits[0]+4)[0];budget=(len(meta)+65536+4095)&~4095;struct.pack_into('<I',rss,hits[0]+4,budget)
p=root/rssrel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(zs.ZstdCompressor(level=12).compress(rss));assert a.decompress(p.read_bytes())==rss
print('UI resource budget',oldbudget,'->',budget)

# BNTX metadata-only texture view: original magic texture and encoded pixels remain unchanged.
texrel='UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.bntx.zs'
tex=bytearray(a.decompress((Path('outputs/OOT-PS5-Buttons-v0.2/romfs')/texrel).read_bytes()))
textures=json.loads(Path('work/oot-textures.json').read_text());src=next(t for t in textures if t['name']=='MpGaugeCenter_00');dst=next(t for t in textures if t['name']=='ControllerGuide_Pro_04')
sp,dp=src['pos'],dst['pos'];nameptr=struct.unpack_from('<Q',tex,dp+0x60)[0];block=struct.unpack_from('<I',tex,dp+4)[0];assert block==struct.unpack_from('<I',tex,sp+4)[0]
view=bytearray(tex[sp:sp+block])
for off in range(0x60,len(view)-7,8):
 value=struct.unpack_from('<Q',view,off)[0]
 if sp<=value<sp+block:struct.pack_into('<Q',view,off,dp+value-sp)
struct.pack_into('<Q',view,0x60,nameptr);struct.pack_into('<I',view,0x58,0x05000303)
rlt=struct.unpack_from('<I',tex,0x18)[0];assert tex[rlt:rlt+4]==b'_RLT'
pixels=rlt;extra=bytes(tex[src['data']:src['data']+src['size']]);tex[rlt:rlt]=extra
new_rlt=rlt+len(extra);struct.pack_into('<I',tex,0x18,new_rlt);struct.pack_into('<I',tex,new_rlt+4,new_rlt)
# Relocation section 1 owns encoded images and must include the appended copy.
section1=new_rlt+16+24;assert struct.unpack_from('<I',tex,section1+8)[0]==struct.unpack_from('<Q',tex,0x30)[0]
struct.pack_into('<I',tex,section1+12,struct.unpack_from('<I',tex,section1+12)[0]+len(extra))
image_table=struct.unpack_from('<Q',view,0x70)[0]-dp;assert 0<=image_table<len(view)-7
struct.pack_into('<Q',view,image_table,pixels);tex[dp:dp+block]=view
struct.pack_into('<I',tex,0x1c,len(tex));data_block=struct.unpack_from('<Q',tex,0x30)[0];struct.pack_into('<Q',tex,data_block+8,new_rlt-data_block)
assert tex[src['pos']+0x58:src['pos']+0x5c]==bytes.fromhex('02030405')
p=root/texrel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(zs.ZstdCompressor(level=12,dict_data=a.DICT[1]).compress(tex));assert a.decompress(p.read_bytes())==tex
print('Independent yellow texture view created; encoded texture bytes untouched')

# The texture archive also grows by one encoded image allocation.
wanted=zlib.crc32(texrel.removesuffix('.zs').encode());hits=[p for p in range(22,22+count*8,8) if struct.unpack_from('<I',rss,p)[0]==wanted];assert len(hits)==1
old_tex_budget=struct.unpack_from('<I',rss,hits[0]+4)[0];new_tex_budget=(len(tex)+65536+4095)&~4095;struct.pack_into('<I',rss,hits[0]+4,new_tex_budget)
(root/rssrel).write_bytes(zs.ZstdCompressor(level=12).compress(rss));print('Texture allocation budget',old_tex_budget,'->',new_tex_budget)
