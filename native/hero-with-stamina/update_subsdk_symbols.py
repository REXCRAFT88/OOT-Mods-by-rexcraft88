from pathlib import Path
import subprocess

root = Path('work/hero-mode-integrated-trial')
symbols = {}
for line in subprocess.check_output(['llvm-nm', str(root/'hero_controls_runtime.elf')], text=True).splitlines():
    parts = line.split()
    if len(parts) == 3:
        symbols[parts[2]] = int(parts[0], 16)

p = root/'src/wheel_probe.ld'
text = p.read_text()
for name in ('hero_all_input', 'hero_guard_frame'):
    rtld_relative = symbols[name] + 0x20000  # rtld is main - 0x20000 in qualified loader layout
    key = f'{name} = '
    lines = [line for line in text.splitlines() if not line.startswith(key)]
    lines.append(f'{name} = 0x{rtld_relative:x};')
    text = '\n'.join(lines) + '\n'
p.write_text(text)
