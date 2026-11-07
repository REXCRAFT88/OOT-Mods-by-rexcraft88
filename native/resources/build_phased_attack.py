import sys,json,struct,copy,pathlib,uuid
import ainb,ainb.utils;ainb.utils.ParseWarning=lambda *args: None
sys.path.insert(0,'work');import oot_assets as a
a.init();rel='Pack/AI.Global.Product.111.pack.zs';bundle=bytearray(a.decompress(a.read('package1/romfs/'+rel)));member='AI/Wolfos.action.BasicAttack.module.ainb';original=a.sarc(bundle)[member];d=ainb.AINB.from_binary(original).as_dict();templates=json.load(open('work/as-timing-templates.json'))
def node(i):return next(n for n in d['Nodes'] if n['Node Index']==i)
def replace(i,t):
 n=copy.deepcopy(t);n['Node Index']=i;n['GUID']=node(i)['GUID'];d['Nodes'][next(k for k,n in enumerate(d['Nodes']) if n['Node Index']==i)]=n;return n
def default(p,value):
 p['Default Value']=value;p['Node Index']=-1;p['Output Index']=0;p['Flags']=['Uses Default'];p.pop('Blackboard Index',None);p.pop('Expression Index',None)
def prop(n,name,value):
 for rows in n['Properties'].values():
  for p in rows:
   if p['Name']==name:p['Default Value']=value;return
 raise KeyError(name)
# Finish directly after the attack, bypassing the recovery/exposure group.
node(17)['Plugs']['Child'][1]['Node Index']=37
# Slip event must not forcibly rotate toward FlipPos during the second slash.
next(p for p in node(2)['Plugs']['Child'] if p['Name']=='True')['Node Index']=39
# Latch acceleration after the first strike begins; keep subsequent slash windups fast.
d['Blackboard']['Bool'].append({'Blackboard Index':3,'Name':'HeroFastPhase','Notes':'Long initial telegraph, then fast combo','Inherit Mode':'DontInherit','Default Value':False})
prop(node(21),'BlackboardKey','HeroFastPhase');prop(node(22),'BlackboardKey','HeroFastPhase')
prop(node(13),'PlayRate',1.0)
frame=replace(16,templates['QueryASGetCurrentFrame']['node']);frame['Queries']=[];frame['Plugs']={}
compare=node(70);compare['Queries']=[16];compare['Plugs']={}
default(compare['Parameters']['Inputs']['Float'][0],38.0)
p=compare['Parameters']['Inputs']['Float'][1];default(p,0.0);p.update({'Node Index':16,'Output Index':0,'Flags':[]})
selector=replace(20,node(24));selector['Queries']=[70]
p=selector['Parameters']['Inputs']['Bool'][0];default(p,False);p.update({'Node Index':70,'Output Index':0,'Flags':[]})
selector['Plugs']={'Child':[{'Node Index':21,'Name':'True'},{'Node Index':43,'Name':'False'}]}
node(1)['Plugs']['Child'].append({'Node Index':20,'Name':''})
rate=replace(76,node(58));rate['Queries']=[];rate['Plugs']={}
p=rate['Parameters']['Inputs']['Bool'][0];default(p,False);p.update({'Blackboard Index':3,'Flags':[]})
for p in rate['Parameters']['Inputs']['Float']:default(p,2.0 if p['Name']=='A' else 1.0)
# Its previous dummy action use now shares the existing dummy node48.
next(p for p in node(77)['Plugs']['Child'] if p['Name']=='False')['Node Index']=48
play=replace(0,templates['ExecuteASPlayByPlug']['node']);play['Queries']=[76];play['Plugs']={}
for p in play['Parameters']['Inputs']['String']:
 default(p,'NoWeaponAttack' if p['Name']=='ASCommand' else '')
for p in play['Parameters']['Inputs']['Float']:
 default(p,1.0 if p['Name']=='PlayRate' else 0.0)
 if p['Name']=='PlayRate':p.update({'Node Index':76,'Output Index':0,'Flags':[]})
for p in play['Parameters']['Inputs']['Bool']:
 default(p,p['Name'] in ['BusyUntilFinished','IsIgnoreSameCommand','RestorePlayRateOnLeave'])
obj=ainb.AINB.from_dict(d)
if obj.blackboard is None:obj.blackboard=ainb.Blackboard()
patched=obj.to_binary();assert ainb.AINB.from_binary(patched).as_dict()==d
# Append only this SARC member; preserve every other member and its offsets.
e='<';h=struct.unpack_from('<H',bundle,4)[0];dataoff=struct.unpack_from('<I',bundle,12)[0];nh,n=struct.unpack_from('<HH',bundle,h+4);nodes=h+nh;names=nodes+16*n+8
record=None
for i in range(n):
 q=nodes+i*16;_,attr,st,en=struct.unpack_from('<IIII',bundle,q);p=names+(attr&0xffffff)*4;name=bytes(bundle[p:bundle.index(0,p)]).decode()
 if name==member:record=q
assert record is not None
bundle.extend(b'\0'*((-len(bundle))%16));st=len(bundle)-dataoff;bundle.extend(patched);struct.pack_into('<II',bundle,record+8,st,len(bundle)-dataoff);struct.pack_into('<I',bundle,8,len(bundle));assert a.sarc(bundle)[member]==patched
import zstandard as zs
out=pathlib.Path('work/hero-phased-trial/romfs')/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(zs.ZstdCompressor(level=12,dict_data=a.DICT[4]).compress(bundle));assert a.decompress(out.read_bytes())==bundle
pathlib.Path('work/hero-phased-attack.json').write_text(json.dumps(d,indent=2));print('Built phase candidate; original member',len(original),'patched',len(patched),'initial rate1, latch at frame38, then rate2; slip rotation branch disabled')
