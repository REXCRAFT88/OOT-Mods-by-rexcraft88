"""Build compatibility candidates from qualified release variants, preserving RomFS.

Run from the project workspace. Never writes to the source game or installed mods.
"""
from pathlib import Path
import sys, json, struct, subprocess, shutil, hashlib
sys.path[:0] = ['work/publish-oot-mods', 'outputs/OOT-Test-Kit']
import install
from nup_overlay import Nup

SRC = Path(__file__).resolve().parent
OUT = Path('work/compatibility-candidates')
OUT.mkdir(exist_ok=True)
n = Nup(json.load(open('outputs/OOT-Test-Kit/settings.json'))['source_nup'])
pkg = n.best_package()['index']
original = {name:n.read(pkg, 'exefs/'+name) for name in ['main','rtld','subsdk0','sdk']}
flags = ['--target=aarch64-none-elf','-Oz','-ffreestanding','-ffunction-sections','-fdata-sections','-fno-stack-protector','-fno-jump-tables','-Ioutputs/OOT-Test-Kit']
def run(*args): subprocess.run(list(map(str,args)),check=True)
def compile(src,dst): run('clang',*flags,'-c',src,'-o',dst)
def symbols(elf):
    return {v[2]:int(v[0],16) for l in subprocess.check_output(['llvm-nm',str(elf)],text=True).splitlines() if len(v:=l.split())==3}
def branch(a,b,link=False):
    d=b-a
    assert d%4==0 and -(1<<27)<=d<(1<<27)
    return struct.pack('<I',(0x94000000 if link else 0x14000000)|((d//4)&0x3ffffff))
def emit(blob,text): return install.emit_nso(blob,text,struct.unpack_from('<I',blob,60)[0])

for variant in ['hero-with-stamina','hero-without-stamina','item-wheel','manual-shield']:
    baseline=Path('work/wheel-standalone-trial') if variant=='item-wheel' else Path('work/public-variants')/variant
    root=OUT/variant;root.mkdir(exist_ok=True)
    shutil.copytree(baseline/'romfs',root/'romfs',dirs_exist_ok=True) if (baseline/'romfs').exists() else None
    (root/'exefs').mkdir(exist_ok=True)
    blobs={p.name:p.read_bytes() for p in (baseline/'exefs').iterdir() if p.is_file()}
    texts={k:bytearray(install.nso_text(v)) for k,v in blobs.items()}
    stamina=variant=='hero-with-stamina'
    # Known FPS cave: 3c46200..278; ultrawide cave: 3c46400..5e4.
    # Preserve both by placing our code after 3c46600.
    ld='SECTIONS { . = 0x3c46600; .text : { context_s.o(.text*) context_c.o(.text*) context_c.o(.rodata*) '
    objects=[]
    context=(SRC/'ocarina_context.S').read_text()
    if stamina:
        context+='''
.global copy_config
copy_config:
 ldp q0,q1,[x1]
 stp q0,q1,[x0]
 ldp q0,q1,[x1,#32]
 stp q0,q1,[x0,#32]
 ldr q0,[x1,#64]
 str q0,[x0,#64]
 ret
'''
    if variant!='item-wheel':
        control=0x4f29810 if stamina else 0x4f29770
        context+='''
.global controls_context
controls_context:
 cbz x0,context_return
 sub sp,sp,#32
 stp x0,x1,[sp]
 str x30,[sp,#16]
 bl context_bypass
 mov w16,w0
 ldr x30,[sp,#16]
 ldp x0,x1,[sp]
 add sp,sp,#32
 cbnz w16,context_return
 b controls_resume
context_return:
 ret
'''
    else:
        context+='''
.global wheel_heartbeat
wheel_heartbeat:
 stp x16,x17,[sp,#-16]!
 adrp x16,wheel_cache
 add x16,x16,:lo12:wheel_cache
 ldr w17,[x16,#124]
 add w17,w17,#1
 str w17,[x16,#124]
 ldp x16,x17,[sp],#16
 stp x29,x30,[sp,#-0x60]!
 b wheel_tick_resume
'''
    (root/'context.S').write_text(context)
    (root/'context.c').write_text(('' if variant=='item-wheel' else '#define HERO_CONTEXT\n')+(SRC/'wheel_context.c').read_text())
    compile(root/'context.S',root/'context_s.o');compile(root/'context.c',root/'context_c.o')
    objects=[root/'context_s.o',root/'context_c.o']
    if stamina:
        asm=Path('work/hero_stamina_runtime.S').read_text()
        asm=asm.replace('exertion_filter:\n','''exertion_filter:
 adrp x16,wheel_cache
 add x16,x16,:lo12:wheel_cache
 ldr w16,[x16,#120]
 cbnz w16,hid_done
''')
        (root/'stamina.S').write_text(asm)
        compile(root/'stamina.S',root/'stamina_s.o')
        compile('outputs/OOT-Test-Kit/hero_core.c',root/'core.o')
        compile(SRC/'stamina_configurable.c',root/'native.o')
        objects += [root/'stamina_s.o',root/'core.o',root/'native.o']
        ld+='stamina_s.o(.text*) core.o(.text*) core.o(.rodata*) native.o(.text.near_enemy) '
    ld+='} '
    if stamina:
        # SDK text alignment pad is 1968 bytes. Module placement stays unchanged.
        ld+='. = 0x5803850; .sdktext : { native.o(.text*) native.o(.rodata*) } '
    ld+='/DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\n'
    defs=Path('work/hero_stamina_runtime.ld').read_text().split('\n',1)[1]
    ld+=defs+'\nwheel_cache = 0x4ea1000;\nocarina_enter_resume = 0x2894344;\nocarina_leave_resume = 0x28947f4;\n'
    ld+='hero_user_options = 0x4ea4000;\n'
    if variant!='item-wheel':ld+=f'controls_resume = {control+4};\n'
    else:ld+='wheel_tick_resume = 0x2ddc - 0x20000 + 4;\n'
    (root/'context.ld').write_text(ld)
    # lld input selectors use basenames, so execute from this build directory.
    args=[shutil.which('ld.lld.exe'),'--gc-sections','--undefined=ocarina_enter','--undefined=ocarina_leave','--undefined=wheel_context_raw']
    if variant!='item-wheel':args+=['--undefined=controls_context']
    else:args+=['--undefined=wheel_heartbeat']
    if stamina:
        args+=['--undefined='+s for s in ['stamina_frame','attack_enter','tired_damage','hero_mp_init','hid_full','hid_dual','hid_left','hid_right','hid_handheld',*json.load(open('work/stamina-runtime-patches.json')).keys()]]
    subprocess.run(args+['-T','context.ld',*[p.name for p in objects],'-o','context.elf'],cwd=root,check=True)
    sy=symbols(root/'context.elf')
    run('llvm-objcopy','-O','binary','--only-section=.text',root/'context.elf',root/'main.bin')
    code=(root/'main.bin').read_bytes();assert 0x3c46600+len(code)<=0x3c47000,len(code)
    t=texts['main']
    if stamina:
        # Remove the old stamina cave entirely, then retarget all original hooks.
        t=t[:0x3c461d0]
    t.extend(b'\0'*(0x3c46600-len(t)));t.extend(code)
    texts['main']=t
    for at,s in [(0x2894340,'ocarina_enter'),(0x28947f0,'ocarina_leave')]:
        assert t[at:at+4]==bytes.fromhex('7f2303d5');t[at:at+4]=branch(at,sy[s])
    raw=sy['wheel_context_raw']
    if stamina:
        old=symbols('work/hero_stamina_runtime.elf')
        # Wheel's frame call is a BL inside stamina_frame; redirect the relocated call.
        oldrt=symbols('work/hero-mode-integrated-trial/wheel_probe.elf')
        at=sy['stamina_frame']+0x20;t[at:at+4]=branch(at,oldrt['wheel_tick_entry']-0x20000,True)
        # Restore wheel tick trampoline's original_hero_frame call to the moved function.
        rt=texts['rtld'];a=oldrt['wheel_tick_entry']+4
        rt[a:a+4]=branch(a,sy['hero_native_frame']+0x20000,True)
        # The full-controller filter tail executes the combined input hook.
        at=sy['hid_done'];t[at:at+4]=branch(at,oldrt['wheel_hid_entry']-0x20000)
        changes=json.load(open('work/hero-stamina-trial/changes.json'))['changes']
        reverse={v:k for k,v in old.items()}
        for c in changes:
            at=int(c['offset'],16);w=int.from_bytes(bytes.fromhex(c['after']),'little')
            d=w&0x3ffffff;d=d-(1<<26) if d&(1<<25) else d
            target=at+d*4;name=reverse[target]
            t[at:at+4]=branch(at,sy[name],bool(w&0x80000000))
        # Hook above must use the wheel frame bridge, not replace it with stock BL.
        sdkbase=0x4f85000
        sdk=bytearray(install.nso_text(original['sdk']))
        assert sdkbase+len(sdk)==0x5803850
        run('llvm-objcopy','-O','binary','--only-section=.sdktext',root/'context.elf',root/'sdk.bin')
        sc=(root/'sdk.bin').read_bytes();assert len(sdk)+len(sc)<=0x87f000
        sdk.extend(sc);blobs['sdk']=original['sdk'];texts['sdk']=sdk
        off=0x4f29a88-0x4ea5000
        texts['subsdk0'][off:off+4]=branch(0x4f29a88,raw)
    elif variant!='manual-shield':
        rt=texts['rtld'];rt[0x2f18:0x2f1c]=branch(0x2f18,raw+0x20000)
        if variant=='item-wheel':rt[0x2ddc:0x2de0]=branch(0x2ddc,sy['wheel_heartbeat']+0x20000)
    if variant!='item-wheel':
        off=control-0x4ea5000
        assert int.from_bytes(texts['subsdk0'][off:off+4],'little')&0xff00001f==0xb4000000
        texts['subsdk0'][off:off+4]=branch(control,sy['controls_context'])
    # Keep main's ORIGINAL text extent. Lichii's built-in FPS routine checks
    # that its cave is outside that extent, not merely that the bytes are zero.
    # IPS32 fills our separate, already executable alignment padding after load.
    original_extent=len(install.nso_text(original['main']))
    cave=bytes(texts['main'][original_extent:])
    assert texts['main'][original_extent:0x3c46600]==b'\0'*(0x3c46600-original_extent)
    ips=b'IPS32'+struct.pack('>IH',0x3c46600+0x100,len(texts['main'])-0x3c46600)+bytes(texts['main'][0x3c46600:])+b'EEOF'
    if stamina:
        from stamina_settings import DEFAULTS,encode_settings
        options=encode_settings(DEFAULTS)
        ips=ips[:-4]+struct.pack('>IH',0x4ea4000+0x100,len(options))+options+b'EEOF'
        (root/'stamina-settings.json').write_text(json.dumps(DEFAULTS,indent=2))
    (root/'exefs/E0F3CCFAF50065AE4EA01EB5AEB13B1A45DA3348.ips').write_bytes(ips)
    texts['main']=texts['main'][:original_extent]
    for name,txt in texts.items():(root/'exefs'/name).write_bytes(emit(blobs[name],txt))
    (root/'compatibility.json').write_text(json.dumps({'variant':variant,'main_code_start':'0x3c46600','main_code_bytes':len(code),'sdk_code_bytes':len(sc) if stamina else 0,'symbols':sy},indent=2))
    print(variant,'built',len(code),'main bytes',len(sc) if stamina else 0,'SDK bytes',flush=True)
