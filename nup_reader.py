"""Apply existing-member overrides to a separate NUP copy (never the source)."""
import hashlib,pathlib,struct,shutil,os,json

class Nup:
    def __init__(self,path):
        self.path=pathlib.Path(path)
        with self.path.open('rb') as f:
            self.header=bytearray(f.read(128))
            if self.header[:4]!=b'NUP\x01':raise ValueError('Not a NUP v1 file')
            self.toc_offset,self.toc_size=struct.unpack_from('<QQ',self.header,8)
            if self.toc_size>256*1024*1024:raise ValueError('TOC exceeds supported size')
            f.seek(self.toc_offset);self.toc=bytearray(f.read(self.toc_size))
        if hashlib.sha256(self.toc).digest()!=self.header[24:56]:raise ValueError('TOC hash mismatch')
        magic,np,nd,nf,po,ps,_=struct.unpack_from('<IIQQQQQ',self.toc)
        if magic!=0x01434f54:raise ValueError('Invalid table magic')
        self.packages=[];self.files={};pos=48
        for i in range(np):
            tid,root,ex,rom,version=struct.unpack_from('<QIIII',self.toc,pos)
            self.packages.append(dict(title_id=tid,root=root,exefs=ex,romfs=rom,version=version,kind=self.toc[pos+24],index=i));pos+=64
        def name(o,n):return self.toc[po+o:po+o+n].decode('utf-8')
        dirs=[]
        for i in range(nd):
            o,n,c,k=struct.unpack_from('<IIII',self.toc,pos);dirs.append((name(o,n),c,k));pos+=24
        files=[]
        for i in range(nf):
            o,n,size,offset,stored=struct.unpack_from('<IIQQQ',self.toc,pos)
            files.append(dict(name=name(o,n),size=size,offset=offset,stored=stored,codec=self.toc[pos+64],record=pos));pos+=80
        children=struct.unpack_from('<'+'I'*((po-pos)//4),self.toc,pos)
        def walk(i,path,package,depth=0):
            if depth>128:raise ValueError('Directory depth exceeded')
            _,c,k=dirs[i]
            for ch in children[c:c+k]:
                if ch<nd:walk(ch,path+'/'+dirs[ch][0],package,depth+1)
                else:
                    a=files[ch-nd];self.files[(package,path+'/'+a['name'])]=a
        for p in self.packages:walk(p['root'],'',p['index'])
    def read(self,package,path):
        a=self.files[(package,'/'+path.lstrip('/'))]
        with self.path.open('rb') as f:f.seek(a['offset']);b=f.read(a['stored'])
        if a['codec']:
            import zstandard
            b=zstandard.ZstdDecompressor().decompress(b,max_output_size=a['size'])
        if len(b)!=a['size']:raise ValueError('Short or malformed member')
        return b
    def best_package(self):
        updates=[p for p in self.packages if p['kind']==1]
        return max(updates or [p for p in self.packages if p['kind']==0],key=lambda p:p['version'])

def apply_copy(source,destination,overrides):
    source=pathlib.Path(source).resolve();destination=pathlib.Path(destination).resolve()
    if source==destination:raise ValueError('Refusing to modify the source NUP')
    source_stat=source.stat()
    destination.parent.mkdir(parents=True,exist_ok=True)
    receipt=destination.with_suffix('.source.json')
    identity={'path':str(source),'size':source_stat.st_size,'mtime_ns':source_stat.st_mtime_ns}
    if not destination.exists():
        if shutil.disk_usage(destination.parent).free<source_stat.st_size+1024**3:raise ValueError('Insufficient space for an independent NUP copy')
        print('Creating independent test NUP copy; this needs about 26 GB once.',flush=True)
        shutil.copyfile(source,destination);receipt.write_text(json.dumps(identity,indent=2))
    elif not receipt.exists() or json.loads(receipt.read_text())!=identity:
        raise ValueError('Existing destination is not a recognized test copy of this source')
    n=Nup(destination);p=n.best_package();patches=[]
    # Validate every requested path before changing the copy.
    for path,data in overrides.items():
        key=(p['index'],'/'+path.lstrip('/'))
        if key not in n.files:raise ValueError('No member to override: '+path)
        if not isinstance(data,bytes):raise TypeError('Override must be bytes')
        patches.append((path,n.files[key],data))
    with destination.open('r+b') as f:
        f.seek(0,2)
        for path,a,data in patches:
            pad=(-f.tell())%16;f.write(b'\0'*pad);offset=f.tell();f.write(data)
            rec=a['record'];struct.pack_into('<QQQ',n.toc,rec+8,len(data),offset,len(data))
            n.toc[rec+32:rec+64]=hashlib.sha256(data).digest();n.toc[rec+64]=0;n.toc[rec+65]=0
        struct.pack_into('<Q',n.header,64,f.tell());n.header[24:56]=hashlib.sha256(n.toc).digest()
        f.seek(n.toc_offset);f.write(n.toc);f.seek(0);f.write(n.header);f.flush();os.fsync(f.fileno())
    checked=Nup(destination)
    for path,_,data in patches:
        if checked.read(p['index'],path)!=data:raise ValueError('Read-back mismatch: '+path)
    if source.stat().st_mtime_ns!=source_stat.st_mtime_ns or source.stat().st_size!=source_stat.st_size:raise ValueError('Source changed during test-copy build')
    print('Verified',len(patches),'resource overrides in',destination,flush=True)
    return destination
