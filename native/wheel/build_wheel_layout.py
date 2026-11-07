"""Patch real Layout2 descriptors, preserving duplicate SARC members and stamina."""
from pathlib import Path
import sys,struct,zstandard as zs,zlib
sys.path.insert(0,'work')
import oot_assets as a
a.init()
rel='UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.blarc.zs'
root=Path('work/wheel-standalone-trial/romfs' if '--standalone' in sys.argv else 'work/hero-wheel-trial/romfs')
archive=a.decompress((root/rel).read_bytes())
def patch(name,raw):
 b=bytearray(raw)
 names,descs,_,n,_=struct.unpack_from('<QQQII',b,0x118)
 panes={}
 for i in range(n):
  p=struct.unpack_from('<Q',b,names+8*i)[0]
  panes[b[p:b.index(0,p)].decode()]=struct.unpack_from('<Q',b,descs+8*i)[0]
 def field(p,k,v):struct.pack_into('<f',b,panes[p]+4*k,v)
 def hide(p):field(p,4,0);field(p,5,0)
 if name=='PaShortCutSlideList_00.buil':
  # Widen virtual layout coverage so the native engine creates all icon cards.
  field('N_SlideList_00',11,24000)
  field('N_SlideList_00',8,0)
  field('N_SlideList_00',12,2160)
  field('S_ScissorHT_00',8,0)
  field('S_ScissorHT_00',11,24000)
  field('S_ScissorHT_00',12,2160)
  field('T_Text_00',8,0)
  for p in ['N_Cursor_00','N_Arrow_00','N_Arrow_01','P_CursorSh_00','Pa_ShortCutScrollBar_00']:hide(p)
 elif name=='ShortCut_01.buil':
  for p in ['P_MaskR_00','P_MaskL_00','C_CaptureR_00','C_CaptureL_00','Pa_SortWindow_00','A_Guide_00','A_Guide_01']:hide(p)
 return b
h=struct.unpack_from('<H',archive,4)[0];dataoff=struct.unpack_from('<I',archive,12)[0]
nh,n=struct.unpack_from('<HH',archive,h+4);nodes=h+nh;names=nodes+16*n+8
out=bytearray(archive);changed=[]
for i in range(n):
 p=nodes+16*i;_,attr,st,en=struct.unpack_from('<4I',archive,p)
 np=names+(attr&0xffffff)*4;name=archive[np:archive.index(0,np)].decode()
 if name not in ['PaShortCutSlideList_00.buil','ShortCut_01.buil']:continue
 raw=patch(name,archive[dataoff+st:dataoff+en])
 assert len(raw)==en-st
 out[dataoff+st:dataoff+en]=raw;changed.append(name)
(root/rel).write_bytes(zs.ZstdCompressor(level=12,dict_data=a.DICT[1]).compress(out))
assert len(changed)>=2
print('Patched layout members:',changed)
