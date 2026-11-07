from pathlib import Path
import re,subprocess,struct,json,sys,hashlib
sys.path.insert(0,'outputs/OOT-Test-Kit');from nup_overlay import Nup
r=Path('work/public-no-stamina-src');r.mkdir(exist_ok=True);src=Path('work/hero-mode-integrated-trial/src')
s=(src/'hero_controls_runtime.rejected-as-swap.c').read_text();a=s.index('/* Pointer-only StringRefs');b=s.index('void hero_controls_raw',a);s=s[:a]+s[b:];s=s.replace('if (targeting) {','if (targeting || held_guard) {');s=s.replace('    init_guard_names();\n','');a=s.index('    /* Use the previously visible');b=s.index('    hero_control_state[3]',a);s=s[:a]+s[b:];s=s.replace('    wheel_raw(records, count);\n','');s+='''
extern void *resolve_player(void *);
void manual_frame(void *ai) {
 u64 state=(u64)resolve_player(ai);if(!state)return;
 hero_cache[0]=state;u64 actor=*(u64 *)(state+0x18);if(!actor)return;
 u64 table=*(u64 *)(actor+0x270);if(!table)return;
 u64 anim=*(u64 *)(table+0x40);if(!anim)return;
 u64 p=*(u64 *)(anim+0x18);if(!p)return;
 p=*(u64 *)(p+0x18);if(!p)return;
 *(u64 *)(hero_runtime+0x80)=*(u64 *)(p+0x40);
 *(float *)hero_runtime=100;*(float *)(hero_runtime+4)=100;
 *(u32 *)(hero_runtime+20)=1;*(u32 *)(hero_runtime+32)=1;
 ++*(u32 *)(hero_runtime+136);hero_guard_frame();
}
''';s=s.replace('void hero_guard_frame(void) {','void hero_guard_frame(void) {');
wheel_symbols={v[2]:int(v[0],16) for l in subprocess.check_output(['llvm-nm','work/wheel_standalone.elf'],text=True).splitlines() if len(v:=l.split())==3}
s=s.replace('void hero_all_input(u64 *records, u32 count) {','void hero_all_input(u64 *records, u32 count) {\n    wheel_raw(records,count);')
s=s.replace('++*(u32 *)(hero_runtime+136);hero_guard_frame();','++*(u32 *)(hero_runtime+136);hero_guard_frame();\n ((void (*)(void))((u64)main_image-0x20000+WHEEL_TICK))();')
s='extern unsigned char main_image[];\n#define WHEEL_TICK '+str(wheel_symbols['wheel_tick'])+'\n'+s
s+='\nvoid wheel_raw(u64 *records,u32 count) { ((void (*)(u64 *,u32))((u64)main_image-0x20000+'+str(wheel_symbols['wheel_raw'])+'))(records,count); }\n'
(r/'manual_controls.c').write_text(s)

asm=(src/'hero_controls_runtime.S').read_text();a=asm.index('.global hero_as_request_hook');b=asm.index('hero_target_guard_flags:',a);asm=asm[:a]+'.global hero_target_guard_flags\n'+asm[b:];asm+='''
.global manual_frame_entry,manual_hid_entry
manual_frame_entry:
 ldr x16,[x0]
 adrp x17,main_scheduler_vtable
 add x17,x17,:lo12:main_scheduler_vtable
 cmp x16,x17
 b.ne 1f
 sub sp,sp,#32
 stp x0,x1,[sp]
 str x30,[sp,#16]
 bl manual_frame
 ldr x30,[sp,#16]
 ldp x0,x1,[sp]
 add sp,sp,#32
1:
 pacibsp
 b original_frame_body
manual_hid_entry:
 stp x19,x30,[sp,#-32]!
 mov x19,x0
 ldr w9,[x2]
 str w9,[sp,#16]
 bl sdk_full
 cbz w0,1f
 ldr w16,[sp,#16]
 cbz w16,2f
 cmp w16,#32
 b.ne 1f
2:
 stp x0,x30,[sp,#-16]!
 mov w1,w0
 mov x0,x19
 bl hero_controls_raw
 ldp x0,x30,[sp],#16
1:
 ldp x19,x30,[sp],#32
 ret
''';asm=asm.replace('bl hero_controls_raw','bl hero_all_input');(r/'manual_controls.S').write_text(asm)
ld=(src/'hero_controls.ld').read_text()+'''\nresolve_player = 0x973030;
main_scheduler_vtable = 0x4b05318;
original_frame_body = 0x2b30de4;
sdk_full = 0x3c42800;
''';ld+='\nmain_image = 0;\n';(r/'manual_controls.ld').write_text(ld)
def run(args):subprocess.run(args,check=True)
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-ffunction-sections','-fdata-sections','-fno-stack-protector']
run(['clang',*flags,'-c',str(r/'manual_controls.c'),'-o',str(r/'manual_c.o')]);run(['clang','--target=aarch64-none-elf','-c',str(r/'manual_controls.S'),'-o',str(r/'manual_s.o')]);run(['ld.lld.exe','--gc-sections','--undefined=manual_frame_entry','--undefined=manual_hid_entry','--undefined=hero_setter_hook','--undefined=hero_target_guard_flags','--undefined=hero_target_guard_update','-T',str(r/'manual_controls.ld'),str(r/'manual_c.o'),str(r/'manual_s.o'),'-o',str(r/'manual.elf')]);run(['llvm-objcopy','-O','binary','--only-section=.text',str(r/'manual.elf'),str(r/'manual.bin')])
n=Nup(json.load(open('outputs/OOT-Test-Kit/settings.json'))['source_nup']);p=n.best_package();root=Path('work/public-variants/hero-without-stamina');symbols={v[2]:int(v[0],16) for l in subprocess.check_output(['llvm-nm',str(r/'manual.elf')],text=True).splitlines() if len(v:=l.split())==3}
import zbic,lz4.block
def text(b):
 off,_,size=struct.unpack_from('<III',b,16);cs=struct.unpack_from('<I',b,96)[0];data=bytes(b[off:off+cs])
 if struct.unpack_from('<I',b,12)[0]&1:
  try:data=zbic.decompress(data)
  except zbic.error:data=lz4.block.decompress(data,uncompressed_size=size)
 return bytearray(data)
def emit(b,t):
 b=bytearray(b);b.extend(b'\0'*((-len(b))%256));off=len(b);b.extend(t);struct.pack_into('<I',b,12,struct.unpack_from('<I',b,12)[0]&~1);struct.pack_into('<I',b,16,off);struct.pack_into('<I',b,24,len(t));struct.pack_into('<I',b,96,len(t));b[160:192]=hashlib.sha256(t).digest();return b
def branch(a,d,link=False):return struct.pack('<I',(0x94000000 if link else 0x14000000)|(((d-a)//4)&0x3ffffff))
b=bytearray(Path('work/wheel-standalone-trial/exefs/main').read_bytes());t=text(b)
for at,name,expected,link in [(0x2b30de0,'manual_frame_entry','7f2303d5',False),(0x346966c,'manual_hid_entry',None,True),(0x37ba100,'hero_setter_hook','c101f837',False),(0x972e18,'hero_target_guard_flags','0801092a',False),(0x97320c,'hero_target_guard_update','29010d32',False)]:
 if expected and at!=0x2b30de0:assert t[at:at+4].hex()==expected
 t[at:at+4]=branch(at,symbols[name],link)
(root/'exefs').mkdir(parents=True,exist_ok=True);(root/'exefs/main').write_bytes(emit(b,t));b=n.read(p['index'],'exefs/subsdk0');t=text(b);assert len(t)==0x84770;payload=(r/'manual.bin').read_bytes();assert len(payload)<=0x890;t.extend(payload);(root/'exefs/subsdk0').write_bytes(emit(b,t));print('Built standalone experimental manual shield',len(payload),'bytes')
