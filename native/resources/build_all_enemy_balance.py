from pathlib import Path
import sys,json,struct,math,copy,hashlib,shutil,zstandard as zs
sys.path.insert(0,'work');import oot_assets as a
from byml_inspect import parse
a.init();OUT=Path('outputs/OOT-Hero-Mode-AI-v0.4');BASE=Path('outputs/OOT-Hero-Mode-AI-v0.3/romfs');shutil.copytree(BASE,OUT/'romfs',dirs_exist_ok=True)
report={'damage_multiplier':2,'health_multiplier':1.5,'integer_health_rounding':'ceil; positive one-hit enemies become 2 HP','packs':[],'unchanged':[]};canonical={}
for entry in a.INDEX:
 path=entry['path'];name=Path(path).name
 if not path.startswith('package1/romfs/Pack/Actor/'):continue
 enemy=name.startswith('Enemy_');projectile=('Bullet' in name or name.startswith(('BeamosBeam','DungeonBossVolvagia_FireBreath'))) and not name.startswith(('Enemy_','Item_','Pouch_','Shop_','TBox_','Obj_','Weapon_','MirrorShield_')) and 'MirrorShieldReflect' not in name
 if name=='ScrubDeku_DekuNut.pack.zs':projectile=True
 if not enemy and not projectile:continue
 raw=a.read(path)
 if not raw:report['unchanged'].append({'pack':name,'reason':'empty package entry'});continue
 stock_archive=a.sarc(a.decompress(raw));rel=path.removeprefix('package1/romfs/');prior=BASE/rel;archive=bytearray(a.decompress(prior.read_bytes() if prior.exists() else raw));members=a.sarc(archive);replacements={};changes=[]
 for member,stock_bytes in stock_archive.items():
  if '/LifeParameters/' not in member and '/AttackParam/' not in member:continue
  stock,_,_=parse(stock_bytes);current,loc,e=parse(members[member]);patched=bytearray(members[member]);want=copy.deepcopy(current)
  fields=['MaxLife'] if '/LifeParameters/' in member and enemy else ['BaseAttackPower','BaseAttackPowerMeleeWeapon','BaseAttackPowerRangedWeapon'] if '/AttackParam/' in member else []
  for field in fields:
   old=stock.get(field)
   if not isinstance(old,(int,float)) or old<=0:continue
   typ,off=loc[(field,)];assert typ==0xd1,(member,field,typ)
   value=math.ceil(old*1.5) if field=='MaxLife' else old*2
   struct.pack_into(e+'i',patched,off,value);want[field]=value;changes.append({'member':member,'field':field,'stock':old,'new':value})
  if changes and patched!=members[member]:assert parse(patched)[0]==want;replacements[member]=bytes(patched)
  if member in replacements:
   digest=hashlib.sha256(replacements[member]).hexdigest()
   # Identical named resources must not receive inconsistent balance settings.
   if member in canonical:assert canonical[member]==digest,member
   canonical[member]=digest
 if not replacements:
  report['unchanged'].append({'pack':name,'reason':'no positive health/attack scalar (dictionary, helper, inherited or non-damaging actor)'});continue
 h=struct.unpack_from('<H',archive,4)[0];dataoff=struct.unpack_from('<I',archive,12)[0];nh,count=struct.unpack_from('<HH',archive,h+4);nodes=h+nh;names=nodes+16*count+8;found=set()
 for i in range(count):
  q=nodes+16*i;_,attr,st,en=struct.unpack_from('<IIII',archive,q);p=names+(attr&0xffffff)*4;n=bytes(archive[p:archive.index(0,p)]).decode()
  if n in replacements:assert en-st==len(replacements[n]);archive[dataoff+st:dataoff+en]=replacements[n];found.add(n)
 assert found==set(replacements)
 after=a.sarc(archive)
 for n,b in members.items():assert after[n]==replacements.get(n,b)
 packed=zs.ZstdCompressor(level=12,dict_data=a.DICT[4]).compress(archive);assert a.decompress(packed)==archive
 target=OUT/'romfs'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(packed)
 report['packs'].append({'pack':name,'type':'enemy' if enemy else 'enemy projectile','changes':changes})
report['unique_changed_resources']=len(canonical);report['changed_pack_count']=len(report['packs']);(OUT/'balance-report.json').write_text(json.dumps(report,indent=2));shutil.copytree(OUT/'romfs','outputs/OOT-Test-Kit/HeroModeAI/romfs',dirs_exist_ok=True)
print('Built',report['changed_pack_count'],'packs;',len(canonical),'unique stat resources;',len(report['unchanged']),'non-stat entries inventoried')
