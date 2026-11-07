"""Model Lichii build95's actual built-in FPS eligibility checks, including text extent."""
import sys,json,struct,zipfile
from pathlib import Path
sys.path[:0]=['work/publish-oot-mods','outputs/OOT-Test-Kit']
import install
from nup_overlay import Nup
n=Nup(json.load(open('outputs/OOT-Test-Kit/settings.json'))['source_nup'])
original=n.read(n.best_package()['index'],'exefs/main')
stock=install.nso_text(original)
assert len(stock)==0x3c461d0
rows=[]
for key in ['hero-with-stamina','hero-without-stamina','manual-shield','item-wheel']:
    root=Path('work/compatibility-candidates')/key
    main=(root/'exefs/main').read_bytes();t=install.nso_text(main)
    assert len(t)==len(stock),key
    memory=bytearray(t+b'\0'*(0x4ea5000-len(t)))
    ips=(root/'exefs/E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348.ips').read_bytes()
    assert ips[:5]==b'IPS32' and ips[-4:]==b'EEOF'
    off=5;written=[]
    while ips[off:off+4]!=b'EEOF':
        address,size=struct.unpack_from('>IH',ips,off);off+=6;address-=0x100
        assert size>0 and ((address>=0x3c46600 and address+size<=0x3c47000) or
                          (key=='hero-with-stamina' and address==0x4ea4000 and size==96))
        memory[address:address+size]=ips[off:off+size];off+=size;written.append([hex(address),size])
    # Build95 requires executable padding OUTSIDE text, inside its aligned page,
    # original zero bytes, unchanged by user patches, and zero/unchanged BSS state.
    cave=0x3c46200;size=120
    assert cave>=len(t) and cave+size<=(len(t)+4095)&~4095
    assert cave+size<=struct.unpack_from('<I',main,0x24)[0]
    assert memory[cave:cave+size]==b'\0'*size
    assert t[0x6e6cc4:0x6e6cc8]==stock[0x6e6cc4:0x6e6cc8]==bytes.fromhex('2818201e')
    assert memory[0x4e9fe00:0x4e9fe10]==b'\0'*16
    data_at,data_size=struct.unpack_from('<II',main,0x34);bss=struct.unpack_from('<I',main,60)[0]
    assert data_at+data_size<=0x4e9fe00 and 0x4e9fe10<=data_at+data_size+bss
    assert memory[0x3c46400:0x3c465e4]==b'\0'*0x1e4
    rows.append({'variant':key,'original_text_extent':hex(len(t)),'built_in_fps_eligible':True,'fps_hook_unchanged':True,'fps_state_untouched':True,'ultrawide_cave_untouched':True,'sidecar_writes':written})
Path('work/compatibility-candidates/fps-loader-check.json').write_text(json.dumps(rows,indent=2))
print('PASS: all four variants satisfy built-in FPS padding, instruction and BSS checks')
