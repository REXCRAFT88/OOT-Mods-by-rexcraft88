import sys,struct,pathlib,json,zlib
sys.path[:0]=['work','work/jungle'];import oot_assets as a
from byml_inspect import parse
from jungle.sead.sarc import SARCFile
from jungle.lms.common import MessageFile
a.init();changes={}
def arr(b,loc,ref,typ,values,endian):
 off=(len(b)+3)&~3;b.extend(b'\0'*(off-len(b)));b.extend(bytes([0xc0])+len(values).to_bytes(3,'little'if endian=='<'else'big'));b.extend(bytes([typ])*len(values));b.extend(b'\0'*((-len(b))%4));b.extend(struct.pack(endian+'I'*len(values),*values));struct.pack_into(endian+'I',b,loc[ref][1],off)
def raw(rel):return a.decompress(a.read('package1/romfs/'+rel))
def sarc_change(b,name,member):
 s=SARCFile();s.parse(b);s.files[name]=member;out=s.save();s2=SARCFile();s2.parse(out);assert s2.files[name]==member;return out
# Native choice enum's Normal/Pro tokens back the two swapped layouts.
rel='Pack/Bootup.Nin_Ounce_NVN2.pack.zs';original=raw(rel);m=a.sarc(original);name='UI/OptionSetTable/OptionSetTable.game__ui__OptionSetTable.bgyml';b=bytearray(m[name]);d,l,e=parse(b)
arr(b,l,('OptionSetArray',7,'ChoiceType'),0xd3,[1627154745,556646631,957022509,3568908360],e)
assert parse(b)[0]['OptionSetArray'][7]['ChoiceType']==[1627154745,556646631,957022509,3568908360]
changes[rel]=sarc_change(original,name,bytes(b))
rel='GameData/GameDataList.Product.110.byml.zs';b=bytearray(raw(rel));d,l,e=parse(b)
assert d['Data']['Enum'][53]['Hash']==0x4219063f and d['Data']['Enum'][52]['RawValues']==['Normal','Pro','ProMaster']
for field,typ in [('RawValues',0xa0),('Values',0xd5)]:
 vals=[struct.unpack_from(e+'I',b,l[('Data','Enum',i,field,j)][1])[0]for i,j in [(53,0),(53,1),(52,0),(52,1)]]
 arr(b,l,('Data','Enum',53,field),typ,vals,e)
assert parse(b)[0]['Data']['Enum'][53]['RawValues']==['Hold','Switch','Normal','Pro']
changes[rel]=bytes(b)
languages=[x['path'].removeprefix('package1/romfs/') for x in a.INDEX if x['path'].startswith('package1/romfs/Mals/') and x['path'].endswith('.sarc.zs')]
for rel in languages:
 # Keep existing message tags/other strings byte-for-byte.
 original=raw(rel);m=a.sarc(original);name='LayoutMsg/SystemOption_00.msbt';f=MessageFile();f.parse(m[name]);labels,buckets=f.parse_labels(f.blocks['LBL1']);t=f.blocks['TXT2'];e=f.endianness;n=struct.unpack_from(e+'I',t)[0];offsets=struct.unpack_from(e+'I'*n,t,4);messages=[t[o:offsets[i+1]if i+1<n else len(t)]for i,o in enumerate(offsets)]
 replacements={'LockOnType_Title':'Target / Shield Controls','LockOnType_Caption':'Choose Hold or Toggle targeting.\nBumper target: L/L1/LB targets, ZL/L2/LT shields.\nTrigger target: ZL/L2/LT targets, L/L1/LB shields.\nShield is held. R3 cancels targeting.','LockOnType_00':'Hold: bumper target','LockOnType_01':'Toggle: bumper target','LockOnType_02':'Hold: trigger target','LockOnType_03':'Toggle: trigger target'}
 for k,v in replacements.items():
  if k not in labels:labels[k]=len(messages);messages.append(b'')
  messages[labels[k]]=(v+'\0').encode('utf-8')
 header=bytearray(struct.pack(e+'I',len(messages)));off=4+len(messages)*4
 for b in messages:header.extend(struct.pack(e+'I',off));off+=len(b)
 f.blocks['TXT2']=bytes(header)+b''.join(messages);f.blocks['LBL1']=f.save_labels(labels,buckets);changes[rel]=sarc_change(original,name,f.save())
for key in ['hero-with-stamina','hero-without-stamina','manual-shield']:
 root=pathlib.Path('work/controller-options-candidates')/key
 rssrel='System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs';rp=root/'romfs'/rssrel;rss=bytearray(a.decompress(rp.read_bytes())if rp.exists()else raw(rssrel));count=struct.unpack_from('<I',rss,14)[0]
 for rel,b in changes.items():
  p=root/'romfs'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(a.zs.ZstdCompressor(level=12,dict_data=a.DICT[1]).compress(b));assert a.decompress(p.read_bytes())==b
  h=zlib.crc32(rel.removesuffix('.zs').encode());hits=[i for i in range(22,22+count*8,8)if struct.unpack_from('<I',rss,i)[0]==h];assert len(hits)==1,(rel,hits)
  at=hits[0]+4;prev=struct.unpack_from('<I',rss,at)[0];growth=max(0,len(b)-len(raw(rel)));struct.pack_into('<I',rss,at,(prev+growth+65535)&~65535)
 rp.parent.mkdir(parents=True,exist_ok=True);rp.write_bytes(a.zs.ZstdCompressor(level=12).compress(rss));print(key,'options resources written')

