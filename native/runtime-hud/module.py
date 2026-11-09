from pathlib import Path
import struct,hashlib,json
ROOT=Path(__file__).resolve().parent
START=0x4f85000;SIZE=0x80000

def module(text=b'\xc0\x03\x5f\xd6'):
 # Header-only private module; all imports in later helpers are linked PC-relative.
 raw=bytearray(0x1d000);raw[:4]=bytes.fromhex('c0035fd6');struct.pack_into('<I',raw,4,0x20)
 raw[0x20:0x24]=b'MOD0';struct.pack_into('<6I',raw,0x24,0x1e000-0x20,0x1f000-0x20,SIZE-0x20,0,0,0x1f000-0x20)
 raw[0x100:0x100+len(text)]=text
 ro=bytearray(64);struct.pack_into('<4I',ro,40,1,1,0,0) # one empty SysV hash bucket
 dynamic=b''.join(struct.pack('<QQ',tag,val) for tag,val in [(5,0x1d000),(10,1),(6,0x1d008),(11,24),(4,0x1d028),(0,0)])
 header=bytearray(0x100);header[:4]=b'NSO0';struct.pack_into('<I',header,12,0x38)
 for slot,fileoff,vm,data in [(0x10,0x100,0,raw),(0x20,0x100+len(raw),0x1d000,ro),(0x30,0x100+len(raw)+len(ro),0x1e000,dynamic)]:
  struct.pack_into('<III',header,slot,fileoff,vm,len(data));idx=(slot-0x10)//0x10;struct.pack_into('<I',header,0x60+4*idx,len(data));header[0xa0+32*idx:0xc0+32*idx]=hashlib.sha256(data).digest()
 struct.pack_into('<I',header,0x3c,SIZE-0x1e000-len(dynamic));header[0x40:0x60]=hashlib.sha256(raw).digest()
 struct.pack_into('<4I',header,0x88,0,1,8,24)
 return bytes(header+raw+ro+dynamic)
if __name__=='__main__':(ROOT/'subsdk1').write_bytes(module());print('Built private UI module, VM size',hex(SIZE))
