"""Execute compiled AArch64 input helpers with synthetic controller records."""
from pathlib import Path
import sys,json,struct
sys.path.insert(0,'work/hero-review-deps')
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM
from unicorn.arm64_const import UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X30,UC_ARM64_REG_SP,UC_ARM64_REG_PC

results=[]
for variant in ['hero-with-stamina','hero-without-stamina','item-wheel','manual-shield']:
    root=Path('work/compatibility-candidates')/variant
    sy=json.loads((root/'compatibility.json').read_text())['symbols']
    base=0x80000000;u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
    u.mem_map(base+0x3c46000,0x1000)
    u.mem_write(base+0x3c46600,(root/'main.bin').read_bytes())
    u.mem_map(base+0x4ea0000,0x5000)
    u.mem_map(0x90000000,0x2000)
    stop=0x90000000;records=stop+0x100
    cache=base+0x4ea1000
    def word(p,v):u.mem_write(p,struct.pack('<I',v))
    def get(p):return int.from_bytes(u.mem_read(p,4),'little')
    def run(name,a=records,b=1):
        u.reg_write(UC_ARM64_REG_X0,a);u.reg_write(UC_ARM64_REG_X1,b)
        u.reg_write(UC_ARM64_REG_X30,stop);u.reg_write(UC_ARM64_REG_SP,stop+0x1ff0)
        u.emu_start(base+sy[name],stop,count=2000)
        assert u.reg_read(UC_ARM64_REG_PC)==stop
    def raw(sample,bits):
        u.mem_write(records,struct.pack('<5Q',sample,bits,0,0,0));run('wheel_context_raw')
        return int.from_bytes(u.mem_read(records+8,8),'little')
    heartbeat=cache+124 if variant=='item-wheel' else base+0x4ea0800+136
    word(heartbeat,1)
    assert raw(1,0x80)==0,variant
    assert raw(2,0)==0 and get(cache+112)==1,variant
    word(cache+120,1);word(cache+112,2)
    assert raw(3,0x3ff)==0x3ff and get(cache+112)==0,variant
    if variant!='item-wheel':run('controls_context') # must return with native input untouched
    word(cache+120,0)
    for _ in range(12):assert raw(4,0)==0
    assert raw(5,0x3ff)==0x3ff,variant # paused menu: both shoulder buttons pass
    if variant!='item-wheel':run('controls_context')
    word(heartbeat,2)
    assert raw(6,0x80)==0,variant # resume gameplay filtering
    results.append({'variant':variant,'tap':True,'ocarina_passthrough':True,'menu_passthrough':True,'resume':True})
Path('work/compatibility-candidates/context-check.json').write_text(json.dumps(results,indent=2))
print('PASS: compiled input checks for all four variants')
