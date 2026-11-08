"""Build one checked mod from your own NUP or extracted exefs/romfs folder."""
import argparse, base64, hashlib, json, pathlib, struct, sys, zlib

ROOT = pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def sarc(b):
    h=struct.unpack_from('<H',b,4)[0]; nh,n=struct.unpack_from('<HH',b,h+4)
    nodes=h+nh; names=nodes+16*n+8; data=struct.unpack_from('<I',b,12)[0]; result={}
    for i in range(n):
        _,attr,s,e=struct.unpack_from('<4I',b,nodes+16*i); p=names+(attr&0xffffff)*4
        result[b[p:b.index(0,p)].decode()]=b[data+s:data+e]
    return result

def nso_text(b):
    off,_,size=struct.unpack_from('<III',b,16); stored=struct.unpack_from('<I',b,96)[0]
    data=b[off:off+stored]
    if struct.unpack_from('<I',b,12)[0]&1:
        import zbic, lz4.block
        try: data=zbic.decompress(data)
        except zbic.error: data=lz4.block.decompress(data,uncompressed_size=size)
    if len(data)!=size: raise ValueError('NSO text size mismatch')
    return data

def emit_nso(original,text,bss):
    b=bytearray(original); struct.pack_into('<I',b,60,bss)
    b.extend(b'\0'*((-len(b))%256)); off=len(b); b.extend(text)
    struct.pack_into('<I',b,12,struct.unpack_from('<I',b,12)[0]&~1)
    struct.pack_into('<I',b,16,off); struct.pack_into('<I',b,24,len(text))
    struct.pack_into('<I',b,96,len(text)); b[160:192]=hashlib.sha256(text).digest()
    return bytes(b)

class Source:
    def __init__(self,path):
        self.path=pathlib.Path(path).resolve(); self.nup=None
        if self.path.is_file():
            from nup_reader import Nup
            self.nup=Nup(self.path); self.pkg=self.nup.best_package()['index']
        self.dictionaries={}
    def read(self,path):
        if self.nup:return self.nup.read(self.pkg,path)
        return (self.path/path).read_bytes()
    def decompress(self,b):
        import zstandard as zs
        ident=zs.get_frame_parameters(b).dict_id
        if ident and not self.dictionaries:
            pack=zs.ZstdDecompressor().decompress(self.read('romfs/Pack/ZsDic.pack.zs'))
            for data in sarc(pack).values():
                d=zs.ZstdCompressionDict(data); self.dictionaries[d.dict_id()]=d
        return zs.ZstdDecompressor(dict_data=self.dictionaries.get(ident)).decompress(b)

def build(source,manifest_path,destination):
    import bsdiff4, zstandard as zs
    manifest_path=pathlib.Path(manifest_path); m=json.loads(manifest_path.read_text())
    destination=pathlib.Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Output folder must be empty; choose a new folder to avoid mixing mods')
    if source.path.is_dir() and (destination==source.path or destination.is_relative_to(source.path)):
        raise ValueError('Choose an output folder outside the source game folder')
    staged=[]
    for entry in m['files']:
        path=entry['path']
        patch=(manifest_path.parent/entry['patch']).read_bytes()
        if entry['kind']=='raw':
            if sha(patch)!=entry['target_sha256']:raise ValueError('Patch validation failed: '+path)
            staged.append((path,patch))
            continue
        original=source.read(path)
        if entry['kind']=='binary':
            if sha(original)!=entry['source_sha256']:raise ValueError('Wrong game/resource version: '+path)
            target=bsdiff4.patch(original,patch)
            if sha(target)!=entry['target_sha256']:raise ValueError('Output validation failed: '+path)
        elif entry['kind']=='nso':
            if sha(original)!=entry['source_sha256']:raise ValueError('Wrong game version: '+path)
            p=json.loads(zlib.decompress(patch)); old=nso_text(original)
            text=bytearray(old[:p['length']]);text.extend(b'\0'*(p['length']-len(text)))
            for off,data in p['blocks']:
                data=base64.b64decode(data);text[off:off+len(data)]=data
            target=emit_nso(original,text,p['bss'])
            if sha(target)!=entry['target_sha256']:raise ValueError('Output validation failed: '+path)
        else:
            raw=source.decompress(original)
            if sha(raw)!=entry['source_sha256']:raise ValueError('Wrong game/resource version: '+path)
            if entry['kind']=='zstd-blocks':
                ops=json.loads(zlib.decompress(patch));raw=b''.join(raw[off:off+n] if off is not None else base64.b64decode(n) for off,n in ops)
            else:raw=bsdiff4.patch(raw,patch)
            if sha(raw)!=entry['target_sha256']:raise ValueError('Output validation failed: '+path)
            ident=entry['dictionary'];target=zs.ZstdCompressor(level=12,dict_data=source.dictionaries.get(ident)).compress(raw)
        staged.append((path,target))
    for path,target in staged:
        p=destination/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(target)
    info={'name':m['name'],'version':m['version'],'title_id':m['title_id'],'build_id':m['build_id'],'files':[{'path':p,'sha256':sha(b)} for p,b in staged]}
    if 'stamina_settings' in m:
        info['stamina_settings']=m['stamina_settings']
        (destination/'stamina-settings.json').write_text(json.dumps(m['stamina_settings'],indent=2))
    (destination/'mod-info.json').write_text(json.dumps(info,indent=2))
    print('Built and verified',m['name'],'in',destination)
    return m

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,help='Your original NUP, or extracted game folder containing exefs/romfs')
    p.add_argument('--variant',choices=['hero-with-stamina','hero-without-stamina','manual-shield','item-wheel'],default=None)
    p.add_argument('--output',required=True,help='New empty mod folder; never your source game')
    p.add_argument('--patched-nup',help='Also build an independent playable NUP copy (needed for Lichii NUP loading)')
    a=p.parse_args(); variants=list((ROOT/'patches').glob('*/manifest.json'))
    if a.variant:manifest=ROOT/'patches'/a.variant/'manifest.json'
    elif len(variants)==1:manifest=variants[0]
    else:p.error('--variant is required when more than one patch is present')
    source=Source(a.source)
    if a.patched_nup:
        info=json.loads(manifest.read_text())
        if any(e['path'].endswith('.ips') for e in info['files']):
            p.error('This version uses Add-ons to preserve the built-in FPS fix. Build/import an Add-on ZIP instead of a patched NUP.')
        target=pathlib.Path(a.patched_nup).resolve()
        if not source.nup:p.error('--patched-nup requires a NUP source')
        if target==source.path or target.exists():p.error('--patched-nup must name a NEW file, never the source')
    manifest_info=build(source,manifest,a.output)
    if a.patched_nup:
        from nup_reader import apply_copy, set_display_title
        overrides={f.relative_to(a.output).as_posix():f.read_bytes() for f in pathlib.Path(a.output).rglob('*') if f.is_file() and f.relative_to(a.output).parts[0] in ('exefs','romfs')}
        apply_copy(source.path,target,overrides)
        title='The Legend of Zelda: Ocarina of Time ['+manifest_info['name']+']'
        set_display_title(target,title)
        print('Launch this NUP in Lichii:',target)
        print('Library display name:',title)
if __name__=='__main__':
    try:main()
    except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
