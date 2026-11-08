from pathlib import Path
import sys,json,zlib,base64,struct,hashlib,bsdiff4,zstandard as zs,importlib.util,shutil
repo=Path('work/publish-oot-mods');sys.path.insert(0,str(repo));import install
source=install.Source(json.load(open('outputs/OOT-Test-Kit/settings.json'))['source_nup']);cache={};source_cache={}
def original(path):
 if path not in source_cache:source_cache[path]=source.read(path)
 return source_cache[path]
variants=[('hero-with-stamina','Hero Mode with Stamina','work/public-variants/hero-with-stamina'),('hero-without-stamina','Hero Mode without Stamina','work/public-variants/hero-without-stamina'),('item-wheel','Item Wheel','work/wheel-standalone-trial')]
if '--manual' in sys.argv:variants=[('manual-shield','Manual Shield','work/public-variants/manual-shield')]
if '--compatibility' in sys.argv:
 variants=[(key,name,'work/compatibility-candidates/'+key) for key,name in [('hero-with-stamina','Hero Mode with Stamina'),('hero-without-stamina','Hero Mode without Stamina'),('manual-shield','Manual Shield'),('item-wheel','Item Wheel')]]
if '--wheel-only' in sys.argv:variants=[v for v in variants if v[0]=='item-wheel']
for key,name,folder in variants:
 root=Path(folder);out=repo/'patches'/key;out.mkdir(parents=True,exist_ok=True);files=[]
 for f in sorted(root.rglob('*')):
  if not f.is_file():continue
  path=f.relative_to(root).as_posix()
  if not path.startswith(('exefs/','romfs/')):continue
  target=f.read_bytes();number=len(files);patchname=f'{number:03d}.patch'
  kind='raw' if path.endswith('.ips') else 'nso' if path.startswith('exefs/') else 'binary' if path.endswith('.ainb') else 'zstd'
  if kind=='raw':
   patch=target;entry={'path':path,'kind':kind,'target_sha256':install.sha(target),'patch':patchname}
  elif kind=='binary':
   old=original(path);patch=bsdiff4.diff(old,target);assert bsdiff4.patch(old,patch)==target
   entry={'path':path,'kind':kind,'source_sha256':install.sha(old),'target_sha256':install.sha(target),'patch':patchname}
  elif kind=='nso':
   old=original(path)
   ot=install.nso_text(old);tt=install.nso_text(target);bss=struct.unpack_from('<I',target,60)[0];target=install.emit_nso(old,tt,bss)
   blocks=[]
   for off in range(0,len(tt),4096):
    block=tt[off:off+4096]
    if block!=ot[off:off+4096]:blocks.append([off,base64.b64encode(block).decode()])
   patch=zlib.compress(json.dumps({'length':len(tt),'bss':bss,'blocks':blocks},separators=(',',':')).encode(),9);entry={'path':path,'kind':kind,'source_sha256':install.sha(old),'target_sha256':install.sha(target),'patch':patchname};f.write_bytes(target)
  else:
   old=original(path)
   ident=zs.get_frame_parameters(target).dict_id;o=source.decompress(old);t=source.decompress(target);sh,th=install.sha(o),install.sha(t)
   if sh==th:continue
   pair=(sh,th)
   if pair not in cache:
    if len(t)>64*1024*1024:
     blocksize=4096;lookup={hashlib.sha256(o[i:i+blocksize]).digest():i for i in range(0,len(o),blocksize)};ops=[]
     for i in range(0,len(t),blocksize):
      block=t[i:i+blocksize];at=lookup.get(hashlib.sha256(block).digest())
      if at is not None:
       if ops and isinstance(ops[-1][0],int) and ops[-1][0]+ops[-1][1]==at:ops[-1][1]+=len(block)
       else:ops.append([at,len(block)])
      else:ops.append([None,base64.b64encode(block).decode()])
     cache[pair]=zlib.compress(json.dumps(ops,separators=(',',':')).encode(),9)
    else:cache[pair]=bsdiff4.diff(o,t)
   patch=cache[pair]
   if len(t)>64*1024*1024:kind='zstd-blocks'
   else:assert bsdiff4.patch(o,patch)==t
   entry={'path':path,'kind':kind,'source_sha256':sh,'target_sha256':th,'dictionary':ident,'patch':patchname}
  (out/patchname).write_bytes(patch);files.append(entry)
 m={'name':name,'version':{'hero-with-stamina':'0.1.0-beta.6','hero-without-stamina':'0.1.0-beta.4','item-wheel':'0.1.4','manual-shield':'0.1.2'}[key],'title_id':'0400486024DEC000','update_version':131072,'build_id':'E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348','files':files};
 if key=='hero-with-stamina':
  from stamina_settings import DEFAULTS
  m['stamina_settings']=DEFAULTS
 (out/'manifest.json').write_text(json.dumps(m,indent=2));print(key,len(files),'files',sum(p.stat().st_size for p in out.iterdir()),'patch bytes',flush=True)
