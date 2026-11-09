"""Verify attack entry performs a fresh nearby-enemy check in each stamina bridge."""
from pathlib import Path
import struct, subprocess, tempfile, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'hero-review-deps'))
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *

SOURCES = {
    'runtime-hud': ROOT / 'native/runtime-hud/stamina_bridge.c',
    'compatibility': ROOT / 'native/compatibility/stamina_configurable.c',
}
FLAGS = ['--target=aarch64-none-elf', '-Oz', '-ffreestanding', '-ffunction-sections',
         '-fdata-sections', '-fno-stack-protector', '-fno-jump-tables', '-I'+str(ROOT/'native/stamina')]
BASE, STOP, RUNTIME, MANAGER_SLOT = 0x10000, 0x30000, 0x50000, 0x52000
LOCK, UNLOCK, AS_INT, AS_BOOL, BEGIN = 0x20000, 0x20010, 0x20020, 0x20030, 0x20040
PLAYER_STATE, PLAYER_ACTOR, NODE, ENEMY, NAME = 0x60000, 0x61000, 0x62000, 0x63000, 0x64000

with tempfile.TemporaryDirectory(prefix='attack-combat-') as temp:
    temp=Path(temp)
    linker=temp/'test.ld'
    linker.write_text(f'SECTIONS {{ . = {BASE:#x}; .text : {{ *(.text*) }} }}\n'
        f'hero_runtime = {RUNTIME:#x}; actor_manager_slot = {MANAGER_SLOT:#x}; battle_info_slot = 0x52008; battle_sound_slot = 0x52010;\n'
        f'actor_lock = {LOCK:#x}; actor_unlock = {UNLOCK:#x}; as_int = {AS_INT:#x};\n'
        f'as_bool = {AS_BOOL:#x}; hero_begin_action = {BEGIN:#x};\n')
    for label,source in SOURCES.items():
        obj,elf,binary=[temp/f'{label}.{ext}' for ext in ('o','elf','bin')]
        subprocess.run(['clang',*FLAGS,'-c',str(source),'-o',str(obj)],check=True)
        subprocess.run(['ld.lld.exe','--gc-sections','--undefined=hero_native_action','-T',str(linker),str(obj),'-o',str(elf)],check=True)
        subprocess.run(['llvm-objcopy.exe','-O','binary','--only-section=.text',str(elf),str(binary)],check=True)
        syms={line.split()[2]:int(line.split()[0],16) for line in subprocess.check_output(['llvm-nm.exe',str(elf)],text=True).splitlines() if len(line.split())==3}
        u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
        u.mem_map(BASE,0x10000);u.mem_map(0x20000,0x1000);u.mem_map(RUNTIME,0x3000);u.mem_map(0x53000,0x2000)
        u.mem_map(PLAYER_STATE,0x1000);u.mem_map(PLAYER_ACTOR,0x1000);u.mem_map(NODE,0x1000)
        u.mem_map(ENEMY,0x1000);u.mem_map(NAME,0x1000);u.mem_map(STOP,0x1000)
        u.mem_write(BASE,binary.read_bytes())
        def put(addr,value,fmt='Q'):u.mem_write(addr,struct.pack('<'+fmt,value))
        def setup(enemy_name=None,distance=0):
            u.mem_write(RUNTIME,b'\0'*0x3000);u.mem_write(MANAGER_SLOT,struct.pack('<Q',0x53000))
            u.mem_write(0x53000,struct.pack('<Q',0x54000));u.mem_write(0x54000+0x38,struct.pack('<Q',NODE))
            put(NODE,0);put(NODE+8,0);put(NODE-8+0x28,ENEMY);put(NODE-8+0x38,0)
            put(ENEMY+0x2c,2,'I');put(ENEMY+0x20,NAME)
            u.mem_write(NAME,(enemy_name or 'Npc_Test').encode()+b'\0')
            put(PLAYER_STATE+0x18,PLAYER_ACTOR)
            put(ENEMY+0x31c,float(distance),'f');put(ENEMY+0x320,0.0,'f');put(ENEMY+0x324,0.0,'f')
            put(PLAYER_ACTOR+0x31c,0.0,'f');put(PLAYER_ACTOR+0x320,0.0,'f');put(PLAYER_ACTOR+0x324,0.0,'f')
            put(RUNTIME+20,1,'I');put(RUNTIME+120,PLAYER_STATE)
            put(RUNTIME+128,0x65000)
        calls=[]
        def hook(uc,address,size,data):
            if address==LOCK or address==UNLOCK:
                calls.append('lock' if address==LOCK else 'unlock');uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
            elif address==AS_INT:
                uc.reg_write(UC_ARM64_REG_X0,1);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
            elif address==AS_BOOL:
                uc.reg_write(UC_ARM64_REG_X0,0);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
            elif address==BEGIN:
                calls.append(('begin_combat',int.from_bytes(bytes(uc.mem_read(RUNTIME+36,4)),'little')))
                result=uc.reg_read(UC_ARM64_REG_X8);uc.mem_write(result,b'\0'*24)
                uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_X30))
        u.hook_add(UC_HOOK_CODE,hook)
        def action(kind=0):
            u.reg_write(UC_ARM64_REG_SP,STOP+0x800);u.reg_write(UC_ARM64_REG_X0,kind);u.reg_write(UC_ARM64_REG_X1,1);u.reg_write(UC_ARM64_REG_X30,STOP)
            try:u.emu_start(syms['hero_native_action'],STOP,count=6000)
            except Exception:
                print(label,'action failed at',hex(u.reg_read(UC_ARM64_REG_PC)),'calls',calls)
                raise
        setup('Enemy_Dekubaba');action(0)
        assert ('begin_combat',1) in calls and calls[:2]==['lock','unlock'],(label,calls)
        calls.clear();setup('Enemy_Dekubaba',10.58);action(0)
        assert ('begin_combat',1) in calls,(label,'restored combat radius',calls)
        calls.clear();setup('Enemy_Dekubaba',20);action(0)
        assert ('begin_combat',0) in calls,(label,'out of range',calls)
        calls.clear();setup('Npc_Test');action(0)
        assert ('begin_combat',0) in calls,(label,'non-enemy',calls)
        for name,distance in [('Enemy_Dekubaba',12.1),('Enemy_Dekubaba_DekuStickDrop',1),('Enemy_Skulltula_Gold',1)]:
            calls.clear();setup(name,distance);put(RUNTIME+36,1,'I');put(RUNTIME+156,1,'I');action(0)
            assert ('begin_combat',0) in calls,(label,'false combat/stale cache',name,calls)
        calls.clear();setup('Enemy_Dekubaba');action(1)
        assert 'lock' not in calls and 'unlock' not in calls,(label,'nonattack scanned',calls)
        print('PASS',label,'attack-entry proximity sample catches brief Deku Baba attack; no false combat out of range/nonenemy')
