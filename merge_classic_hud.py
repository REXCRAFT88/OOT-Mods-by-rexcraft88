"""Merge a user's Classic HUD texture archive into a Hero stamina addon."""
from pathlib import Path, PurePosixPath
import hashlib,json,struct,zipfile
from install import Source
from native.resources.stamina_texture import build_texture

TEXTURE='romfs/UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.bntx.zs'
BUDGET='romfs/System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs'

def entries(archive):
    infos=archive.infolist();names=[i.filename for i in infos]
    if len(names)!=len(set(names)) or len(names)>4096 or sum(i.file_size for i in infos)>2*1024**3:
        raise ValueError('Unsupported ZIP contents')
    if any(PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n or ':' in n for n in names):
        raise ValueError('Unsafe ZIP path')
    return names

def merge(source_path,hero_zip,hud_zip,output):
    import zstandard as zs,zlib
    output=Path(output).resolve()
    if output.exists() or output in [Path(hero_zip).resolve(),Path(hud_zip).resolve()]:raise ValueError('Choose a new output ZIP')
    source=Source(source_path)
    with zipfile.ZipFile(hero_zip) as hero,zipfile.ZipFile(hud_zip) as hud:
        hn,cn=entries(hero),entries(hud)
        def one(names,suffix):
            hits=[n for n in names if n.endswith('/'+suffix)]
            if len(hits)!=1:raise ValueError('Expected one '+suffix)
            return hits[0]
        texname=one(hn,TEXTURE);classicname=one(cn,TEXTURE);budgetname=one(hn,BUDGET);root=texname[:-len(TEXTURE)]
        info=json.loads(hero.read(root+'mod-info.json'))
        if 'stamina_settings' not in info:raise ValueError('Choose Hero Mode WITH Stamina')
        hero_texture=source.decompress(hero.read(texname))
        original=source.decompress(hud.read(classicname));metadata=json.loads((Path(__file__).parent/'native/resources/stamina_texture_metadata.json').read_text())
        view=next(t for t in metadata if t['name']=='ControllerGuide_Pro_04')
        if struct.unpack_from('<I',hero_texture,view['pos']+0x58)[0]!=0x05000303:raise ValueError('Unsupported stamina texture view')
        for t in metadata:
            p=struct.unpack_from('<Q',original,t['pos']+0x60)[0]
            if original[p+2:p+2+len(t['name'])].decode()!=t['name']:raise ValueError('Unsupported HUD texture layout')
        merged=build_texture(bytearray(original),metadata)
        data_start=struct.unpack_from('<Q',original,0x30)[0];reloc=struct.unpack_from('<I',original,0x18)[0]
        assert merged[data_start+16:reloc]==original[data_start+16:reloc] # existing hearts/pixels unchanged
        payload=zs.ZstdCompressor(level=12,dict_data=source.dictionaries[1]).compress(merged)
        assert source.decompress(payload)==merged
        budget=bytearray(source.decompress(hero.read(budgetname)));count=struct.unpack_from('<I',budget,14)[0];crc=zlib.crc32(TEXTURE.removeprefix('romfs/').removesuffix('.zs').encode())
        hits=[p for p in range(22,22+count*8,8) if struct.unpack_from('<I',budget,p)[0]==crc]
        if len(hits)!=1:raise ValueError('Missing HUD allocation budget')
        p=hits[0]+4;struct.pack_into('<I',budget,p,max(struct.unpack_from('<I',budget,p)[0],len(merged)+131072))
        replacements={texname:payload,budgetname:zs.ZstdCompressor(level=12).compress(budget)}
        for f in info['files']:
            if root+f['path'] in replacements:f['sha256']=hashlib.sha256(replacements[root+f['path']]).hexdigest()
        info['hud_compatibility']='Merged from user-provided Classic HUD archive; existing image payloads retained'
        replacements[root+'mod-info.json']=json.dumps(info,indent=2).encode()
        with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as result:
            for n in hn:
                if not n.endswith('/'):result.writestr(n,replacements.get(n,hero.read(n)))
            result.writestr(root+'HUD-MERGE.txt','Disable the original Hero addon and the separate Classic HUD addon. Import this combined ZIP and enable only it. Original game and input ZIPs are unchanged.\n')
    digest=hashlib.sha256(output.read_bytes()).hexdigest();output.with_name(output.stem+'-SHA256.txt').write_text(digest+'  '+output.name+'\n')
    return output

def gui():
    import tkinter as tk
    from tkinter import filedialog as f,messagebox as m
    root=tk.Tk();root.withdraw()
    try:
        source=f.askopenfilename(title='Select your matching original OOT NUP',filetypes=[('NUP game','*.nup')])
        if not source:return
        hero=f.askopenfilename(title='Select Hero Mode WITH Stamina Prepared Addon ZIP',filetypes=[('ZIP','*.zip')])
        if not hero:return
        hud=f.askopenfilename(title='Select your Classic HUD Hearts ZIP',filetypes=[('ZIP','*.zip')])
        if not hud:return
        output=f.asksaveasfilename(title='Save NEW combined addon',initialfile='OOT-Hero-Stamina-Classic-HUD.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip')])
        if not output:return
        merge(source,hero,hud,output);m.showinfo('Combined addon ready','Disable the separate Hero and Classic HUD addons. Import the NEW combined ZIP through Configure Game > Add-Ons > Import Mod from ZIP:\n'+output)
    except Exception as e:m.showerror('HUD merge failed',str(e))
    finally:root.destroy()

if __name__=='__main__':gui()
