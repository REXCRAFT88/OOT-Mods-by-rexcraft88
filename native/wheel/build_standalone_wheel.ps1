$ErrorActionPreference = 'Stop'
& clang --target=aarch64-none-elf -Oz -ffreestanding -ffunction-sections -fdata-sections -fno-stack-protector -c work/wheel_runtime.c -o work/wheel_runtime.o
if ($LASTEXITCODE) { throw 'Wheel compilation failed' }
& clang --target=aarch64-none-elf -c work/wheel_standalone.S -o work/wheel_standalone.o
if ($LASTEXITCODE) { throw 'Wheel assembly failed' }
& ld.lld --gc-sections --undefined=wheel_update --emit-relocs -e wheel_bind_item -T work/wheel_standalone.ld work/wheel_standalone.o work/wheel_runtime.o -o work/wheel_standalone.elf
if ($LASTEXITCODE) { throw 'Wheel linking failed' }
& llvm-objcopy -O binary --only-section=.text work/wheel_standalone.elf work/wheel_standalone.bin
if ($LASTEXITCODE) { throw 'Wheel extraction failed' }
& python work/build_wheel_standalone.py
if ($LASTEXITCODE) { throw 'Wheel executable patch failed' }
& python work/build_wheel_layout.py --standalone
if ($LASTEXITCODE) { throw 'Wheel layout patch failed' }
