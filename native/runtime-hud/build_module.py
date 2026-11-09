from pathlib import Path
import subprocess,cityhash,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent));from module import module
SRC=Path(__file__).resolve().parent
r=Path(sys.argv[1] if len(sys.argv)>1 else 'work/runtime-hud-lab').resolve();r.mkdir(parents=True,exist_ok=True)
flags=['--target=aarch64-none-elf','-Oz','-ffreestanding','-fno-stack-protector','-fno-jump-tables','-mbranch-protection=none']
for src in ['hud.c','hud.S']:subprocess.run(['clang',*flags,'-DSTAMINA_HASH='+str(cityhash.CityHash64('Pa_StaminaGauge_00'))+'ull','-c',str(SRC/src),'-o',str(r/(src+'.o'))],check=True)
(r/'hud.ld').write_text('SECTIONS { . = 0x4f85100; .text : { *(.text) *(.text*) *(.rodata*) } . = 0x4fa5000; .telemetry (NOLOAD) : { *(.telemetry) } .bss (NOLOAD) : { *(.bss*) *(COMMON) } ASSERT(. <= 0x5005000, "private UI BSS exceeds module") /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) } }\nlayout_resume = 0x43a6fc;')
subprocess.run(['ld.lld.exe','-T',str(r/'hud.ld'),str(r/'hud.S.o'),str(r/'hud.c.o'),'-o',str(r/'hud.elf')],check=True)
subprocess.run(['llvm-objcopy','-O','binary','--only-section=.text',str(r/'hud.elf'),str(r/'hud.bin')],check=True)
code=(r/'hud.bin').read_bytes();assert len(code)<0x1cf00
(r/'subsdk1').write_bytes(module(code))
print('Private runtime UI module:',len(code),'code bytes')
print(subprocess.check_output(['llvm-nm','-n',str(r/'hud.elf')],text=True))
