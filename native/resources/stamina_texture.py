"""Create the independent yellow stamina texture view from explicit metadata."""
import struct

def build_texture(tex, textures):
    src=next(t for t in textures if t['name']=='MpGaugeCenter_00');dst=next(t for t in textures if t['name']=='ControllerGuide_Pro_04')
    sp,dp=src['pos'],dst['pos'];nameptr=struct.unpack_from('<Q',tex,dp+0x60)[0];block=struct.unpack_from('<I',tex,dp+4)[0];assert block==struct.unpack_from('<I',tex,sp+4)[0]
    view=bytearray(tex[sp:sp+block])
    for off in range(0x60,len(view)-7,8):
     value=struct.unpack_from('<Q',view,off)[0]
     if sp<=value<sp+block:struct.pack_into('<Q',view,off,dp+value-sp)
    struct.pack_into('<Q',view,0x60,nameptr);struct.pack_into('<I',view,0x58,0x05000303)
    rlt=struct.unpack_from('<I',tex,0x18)[0];assert tex[rlt:rlt+4]==b'_RLT'
    pixels=rlt;extra=bytes(tex[src['data']:src['data']+src['size']]);tex[rlt:rlt]=extra
    new_rlt=rlt+len(extra);struct.pack_into('<I',tex,0x18,new_rlt);struct.pack_into('<I',tex,new_rlt+4,new_rlt)
    # Relocation section 1 owns encoded images and must include the appended copy.
    section1=new_rlt+16+24;assert struct.unpack_from('<I',tex,section1+8)[0]==struct.unpack_from('<Q',tex,0x30)[0]
    struct.pack_into('<I',tex,section1+12,struct.unpack_from('<I',tex,section1+12)[0]+len(extra))
    image_table=struct.unpack_from('<Q',view,0x70)[0]-dp;assert 0<=image_table<len(view)-7
    struct.pack_into('<Q',view,image_table,pixels);tex[dp:dp+block]=view
    struct.pack_into('<I',tex,0x1c,len(tex));data_block=struct.unpack_from('<Q',tex,0x30)[0];struct.pack_into('<Q',tex,data_block+8,new_rlt-data_block)
    assert tex[src['pos']+0x58:src['pos']+0x5c]==bytes.fromhex('02030405')
    return tex
