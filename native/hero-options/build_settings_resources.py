"""Add independent saved Hero settings to an already built unified candidate.

Run after the private builder restores its base resources. Native OptionType
extensions for these seven names must be installed alongside these resources.
"""
from pathlib import Path
import argparse,json,struct,sys,zlib,mmh3
sys.path[:0]=['work','work/jungle','outputs/OOT-Test-Kit']
import oot_assets as assets
from byml_inspect import parse
from jungle.lms.common import MessageFile
from resource_helpers import append_dict,append_array,append_value_string,sarc_change

p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args();root=Path(args.root)
assets.init();changes={}
def original(rel):return assets.decompress(assets.read('package1/romfs/'+rel))
def base(rel):
 path=root/'romfs'/rel
 return assets.decompress(path.read_bytes()) if path.exists() else original(rel)
def h(s):return mmh3.hash(s,signed=False)
def pointers(blob,loc,path,count,e):return [struct.unpack_from(e+'I',blob,loc[path+(i,)][1])[0] for i in range(count)]
def replace_array(blob,loc,path,values,types,e):
 at=append_array(blob,values,types,e);struct.pack_into(e+'I',blob,loc[path][1],at)
HOLD,SWITCH,NORMAL,PRO=0x60fc6939,0x212dc0e7,0x390b012d,0xd4b93848
settings=[
 ('HeroStamina','Stamina','Enable combat stamina and its gauge.',None,True),
 ('HeroStaminaAmount','Stamina Amount','Choose Half, Full or Double capacity.\nCosts and regeneration stay the same.',
  [('Hold','Half'),('Normal','Full'),('Switch','Double')],NORMAL),
 ('HeroManualShield','Manual Shield','Enable manual shield and target controls.',None,True),
 ('HeroItemWheel','Item Wheel','Use the wheel; tap to cycle item variants.',None,True),
 ('HeroWheelBumper','Wheel Bumper','Choose Left, Right or Both for the wheel.\nManual Shield On always uses Right.',
  [('Hold','Right'),('Switch','Left'),('Normal','Both')],HOLD),
 ('HeroDifficulty','Hero Difficulty','Damage / HP: Warrior 2x/1.5x; Hero 4x/2x\nLegend 8x/2x; Myth lethal/2x.',
  [('Hold','Warrior'),('Switch','Hero'),('Normal','Legend'),('Pro','Myth')],HOLD),
 ('HeroNoRecoveryDrops','Disable Heart / Magic Drops','Replace random recovery drops with rupees.\nHeart pieces and containers stay unchanged.',None,False),
]
aliases=[h(s[0]) for s in settings];fields=[h('RexHero.'+s[0]) for s in settings]

# Keep existing targeting/swap rows intact; use new native OptionType IDs.
rel='Pack/Bootup.Nin_Ounce_NVN2.pack.zs';source=base(rel);member='UI/OptionSetTable/OptionSetTable.game__ui__OptionSetTable.bgyml'
blob=bytearray(assets.sarc(source)[member]);data,loc,e=parse(blob);rows=data['OptionSetArray']
assert not any(row.get('OptionType') in aliases for row in rows),'Run the private builder before regenerating settings'
refs=pointers(blob,loc,('OptionSetArray',),len(rows),e)
for name,title,caption,choices,default in settings:
 row={'OptionType':(0xd3,h(name)),'ButtonType':(0xd3,0xd4c0f4d3 if choices else 0xbcbe684c)}
 if choices:
  row['ChoiceType']=(0xc0,append_array(blob,[h(c[0]) for c in choices],[0xd3]*len(choices),e))
 refs.append(append_dict(blob,row,e))
replace_array(blob,loc,('OptionSetArray',),refs,[0xc1]*len(refs),e)
parsed=parse(blob)[0]['OptionSetArray'];assert len(parsed)==len(rows)+7
assert [r['OptionType'] for r in parsed[-7:]]==aliases
changes[rel]=sarc_change(source,member,bytes(blob))

rel='GameData/GameDataList.Product.110.byml.zs';blob=bytearray(base(rel));data,loc,e=parse(blob)
added={'Bool':[],'Enum':[]};new_defaults=[]
for (name,title,caption,choices,default),alias,field in zip(settings,aliases,fields):
 typ='Enum' if choices else 'Bool';assert not any(r['Hash']==field for r in data['Data'][typ])
 row={'Hash':(0xd3,field),'ResetTypeValue':(0xd1,4),'SaveFileIndex':(0xd1,1)}
 if choices:
  tokens=[h(c[0]) for c in choices];assert default in tokens
  strings=[append_value_string(blob,c[0],e) for c in choices]
  row['RawValues']=(0xc0,append_array(blob,strings,[0xa0]*len(strings),e))
  payloads=[]
  for token in tokens:
   blob.extend(b'\0'*(-len(blob)%8));payloads.append(len(blob));blob.extend(struct.pack(e+'Q',token))
  row['Values']=(0xc0,append_array(blob,payloads,[0xd5]*len(payloads),e));row['DefaultValue']=(0xd3,default)
 else:row['DefaultValue']=(0xd0,int(default))
 added[typ].append(append_dict(blob,row,e))
 new_defaults.append(append_dict(blob,{'Hash':(0xd3,alias),'Value':(0xd3,field)},e))
for typ,extra in added.items():
 path=('Data',typ);refs=pointers(blob,loc,path,len(data['Data'][typ]),e)+extra
 replace_array(blob,loc,path,refs,[0xc1]*len(refs),e)
i=next(i for i,r in enumerate(data['Data']['Struct']) if r['Hash']==0x834d9d9e)
path=('Data','Struct',i,'DefaultValue');old=data['Data']['Struct'][i]['DefaultValue']
assert not any(r['Hash'] in aliases for r in old)
refs=pointers(blob,loc,path,len(old),e)+new_defaults;replace_array(blob,loc,path,refs,[0xc1]*len(refs),e)
for key,delta in [('AllDataSaveOffset',56),('AllDataSaveSize',448)]:
 struct.pack_into(e+'I',blob,loc[('MetaData',key)][1],data['MetaData'][key]+delta)
for key,delta in [('SaveDataOffsetPos',56),('SaveDataSize',448)]:
 struct.pack_into(e+'I',blob,loc[('MetaData',key,1)][1],data['MetaData'][key][1]+delta)
verified=parse(blob)[0]
for (name,title,caption,choices,default),alias,field in zip(settings,aliases,fields):
 row=next(r for r in verified['Data']['Enum' if choices else 'Bool'] if r['Hash']==field)
 assert row['DefaultValue']==default
 if choices:assert [struct.unpack_from(e+'Q',blob,v['raw'])[0] for v in row['Values']]==[h(c[0]) for c in choices]
 assert any(r['Hash']==alias and r['Value']==field for r in verified['Data']['Struct'][i]['DefaultValue'])
changes[rel]=bytes(blob)

labels={}
for name,title,caption,choices,default in settings:
 labels[name+'_Title']=title;labels[name+'_Caption']=caption
 if choices:labels.update({name+'_'+str(i).zfill(2):c[1] for i,c in enumerate(choices)})
for item in assets.INDEX:
 rel=item['path'].removeprefix('package1/romfs/')
 if not item['path'].startswith('package1/romfs/Mals/') or not rel.endswith('.sarc.zs'):continue
 source=base(rel);member='LayoutMsg/SystemOption_00.msbt';msg=MessageFile();msg.parse(assets.sarc(source)[member])
 table,buckets=msg.parse_labels(msg.blocks['LBL1']);text=msg.blocks['TXT2'];e=msg.endianness
 n=struct.unpack_from(e+'I',text)[0];offsets=struct.unpack_from(e+'I'*n,text,4)
 strings=[text[at:offsets[i+1] if i+1<n else len(text)] for i,at in enumerate(offsets)]
 for key,value in labels.items():
  if key not in table:table[key]=len(strings);strings.append(b'')
  strings[table[key]]=(value+'\0').encode('utf-8')
 header=bytearray(struct.pack(e+'I',len(strings)));at=4+len(strings)*4
 for value in strings:header.extend(struct.pack(e+'I',at));at+=len(value)
 msg.blocks['TXT2']=bytes(header)+b''.join(strings);msg.blocks['LBL1']=msg.save_labels(table,buckets)
 changes[rel]=sarc_change(source,member,msg.save())

rel='System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs';rss=bytearray(base(rel));n=struct.unpack_from('<I',rss,14)[0]
for path,content in changes.items():
 dest=root/'romfs'/path;dest.parent.mkdir(parents=True,exist_ok=True)
 packed=assets.zs.ZstdCompressor(level=12,dict_data=assets.DICT[1]).compress(content);dest.write_bytes(packed)
 assert assets.decompress(packed)==content
 crc=zlib.crc32(path.removesuffix('.zs').encode());at=next(i+4 for i in range(22,22+n*8,8) if struct.unpack_from('<I',rss,i)[0]==crc)
 required=len(content)+65536
 struct.pack_into('<I',rss,at,max(struct.unpack_from('<I',rss,at)[0],required))
for crc,minimum in [(zlib.crc32(b'UI/OptionSetTable/OptionSetTable.game__ui__OptionSetTable.bgyml'),65536),(0x8909365f,16384)]:
 at=next(i+4 for i in range(22,22+n*8,8) if struct.unpack_from('<I',rss,i)[0]==crc)
 struct.pack_into('<I',rss,at,max(struct.unpack_from('<I',rss,at)[0],minimum))
dest=root/'romfs'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(assets.zs.ZstdCompressor(level=12).compress(rss))
report={'settings':[{'name':s[0],'native_type':18+i,'alias':hex(aliases[i]),'field':hex(fields[i])} for i,s in enumerate(settings)],'changed_resources':len(changes)+1}
(root/'settings-resources.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
